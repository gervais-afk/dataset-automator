#!/usr/bin/env python3
"""
entity_resolver.py — SOVEREIGN.BI Enterprise Context & Action Layer

Module de Réconciliation d'Entités (Entity Resolution / Deduplication).

Fonctionnement :
  1. Parsing  : Lit un fichier CSV/JSON d'entités brutes (depuis ERP, CRM, Excel...).
  2. Normalisation : Nettoyage des noms (casse, accents, ponctuation).
  3. Fuzzy Matching : Compare chaque entité brute aux entités Neo4j existantes
                      via rapidfuzz (ratio de similarité configurable, défaut: 85%).
  4. Attribution MID : Attribue un MID stable UUID4 aux nouvelles entités.
                       Réutilise le MID existant pour les entités résolues.
  5. Upsert Neo4j  : MERGE sur le MID, enrichit la liste `aliases` sans écraser.

Usage CLI :
  python entity_resolver.py --input sample_erp_entities.csv [--dry-run] [--threshold 85]
  python entity_resolver.py --input data.json [--verbose]

Usage Python (import) :
  from entity_resolver import EntityResolver
  resolver = EntityResolver()
  result = resolver.resolve_and_upsert(entities_list)
"""

import os
import sys
import json
import uuid
import csv
import argparse
import unicodedata
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field, asdict

# ── Gestion optionnelle de rapidfuzz ─────────────────────────────────────────
try:
    from rapidfuzz import fuzz, process as rfuzz_process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    print("⚠️  rapidfuzz non installé. Fallback sur SequenceMatcher (moins précis).")
    print("   → Installez-le : pip install rapidfuzz")
    from difflib import SequenceMatcher

# ── Gestion Neo4j ─────────────────────────────────────────────────────────────
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  neo4j driver non disponible. Mode --dry-run uniquement.")

# ─── Configuration ────────────────────────────────────────────────────────────

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://127.0.0.1:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

DEFAULT_SIMILARITY_THRESHOLD = 85  # Score minimum pour considérer deux entités comme identiques (0–100)


# ─── Structures de données ───────────────────────────────────────────────────

@dataclass
class RawEntity:
    """Entité brute provenant d'une source externe (ERP, CRM, CSV...)."""
    name: str
    entity_type: str                    # Ex: "Supplier", "GIC", "Product"
    source: str                         # Nom de la source (ex: "ERP_SAP", "CRM_Salesforce")
    aliases: list[str] = field(default_factory=list)
    properties: dict   = field(default_factory=dict)  # Attributs métier additionnels


@dataclass
class ResolutionResult:
    """Résultat de la résolution pour une entité brute."""
    raw_name: str
    status: str                    # "MATCHED", "NEW", "AMBIGUOUS"
    resolved_mid: Optional[str]    # MID attribué ou trouvé
    resolved_name: Optional[str]   # Nom canonique dans le graphe
    similarity_score: float        # Score de similarité (0–100)
    matched_alias: Optional[str]   # L'alias qui a été matché (si applicable)
    is_new: bool                   # True si c'est une nouvelle entité
    aliases_added: list[str]       # Nouveaux aliases injectés dans le graphe


# ─── Classe principale ────────────────────────────────────────────────────────

class EntityResolver:
    """
    Résout les entités brutes vers des entités canoniques dans le graphe Neo4j.
    Attribue des MIDs stables et enrichit les aliases sans écraser les données existantes.
    """

    def __init__(self, threshold: int = DEFAULT_SIMILARITY_THRESHOLD, verbose: bool = False):
        self.threshold = threshold
        self.verbose   = verbose
        self._graph_entities: list[dict] = []  # Cache des entités Neo4j

    # ── Normalisation ─────────────────────────────────────────────────────────

    @staticmethod
    def normalize(text: str) -> str:
        """Normalise un nom d'entité : minuscule, sans accents, sans ponctuation."""
        # Supprimer les accents (NFD decomposition)
        nfkd = unicodedata.normalize('NFD', text)
        no_accent = ''.join(c for c in nfkd if unicodedata.category(c) != 'Mn')
        # Minuscule
        lower = no_accent.lower()
        # Supprimer la ponctuation et les caractères spéciaux (garder les espaces et tirets)
        cleaned = re.sub(r"[^\w\s\-]", "", lower)
        # Réduire les espaces multiples
        return re.sub(r"\s+", " ", cleaned).strip()

    # ── Chargement des entités depuis Neo4j ───────────────────────────────────

    def load_graph_entities(self, driver) -> list[dict]:
        """Charge toutes les entités :Entity depuis Neo4j (avec leurs aliases)."""
        with driver.session() as session:
            result = session.run(
                "MATCH (e:Entity) RETURN e.mid AS mid, e.name AS name, e.type AS type, "
                "coalesce(e.aliases, []) AS aliases"
            )
            entities = []
            for record in result:
                name    = record["name"] or ""
                aliases = record["aliases"] or []
                entities.append({
                    "mid":     record["mid"],
                    "name":    name,
                    "type":    record["type"],
                    "aliases": aliases,
                    # Précalculer tous les noms normalisés pour la comparaison
                    "all_names_normalized": [
                        self.normalize(n) for n in [name] + aliases if n
                    ],
                })
            self._graph_entities = entities
            if self.verbose:
                print(f"  [Neo4j] {len(entities)} entités chargées depuis le graphe")
            return entities

    # ── Calcul de similarité ──────────────────────────────────────────────────

    def _similarity(self, a: str, b: str) -> float:
        """Calcule le score de similarité entre deux chaînes normalisées (0–100)."""
        if RAPIDFUZZ_AVAILABLE:
            # Utilise le score token_sort_ratio (résistant aux permutations de mots)
            return fuzz.token_sort_ratio(a, b)
        else:
            # Fallback difflib
            return SequenceMatcher(None, a, b).ratio() * 100

    def _best_match(self, normalized_query: str, entity: dict) -> tuple[float, Optional[str]]:
        """
        Retourne le meilleur score de similarité entre la query et toutes les variantes
        (nom + aliases) d'une entité. Retourne (score, nom_matché).
        """
        best_score = 0.0
        best_name  = None
        for candidate_norm in entity["all_names_normalized"]:
            score = self._similarity(normalized_query, candidate_norm)
            if score > best_score:
                best_score = score
                best_name  = candidate_norm
        return best_score, best_name

    # ── Résolution d'une entité ───────────────────────────────────────────────

    def resolve_entity(self, raw: RawEntity) -> ResolutionResult:
        """
        Résout une entité brute contre le graphe en mémoire.
        Retourne le MID existant si match, ou génère un nouveau MID.
        """
        normalized_query = self.normalize(raw.name)

        best_score      = 0.0
        best_entity     = None
        best_alias      = None

        for entity in self._graph_entities:
            score, matched_alias = self._best_match(normalized_query, entity)
            if score > best_score:
                best_score  = score
                best_entity = entity
                best_alias  = matched_alias

        # ── Décision de résolution ────────────────────────────────────────
        if best_score >= self.threshold and best_entity:
            # MATCH — entité existante trouvée
            # Déterminer le nouvel alias à ajouter si le nom brut n'est pas déjà connu
            new_aliases = []
            if raw.name not in best_entity["aliases"] and raw.name != best_entity["name"]:
                new_aliases.append(raw.name)
            for alias in raw.aliases:
                if alias not in best_entity["aliases"] and alias != best_entity["name"]:
                    new_aliases.append(alias)

            if self.verbose:
                print(f"    MATCH  [{best_score:.1f}%] '{raw.name}' → '{best_entity['name']}' (MID: {best_entity['mid']})")

            return ResolutionResult(
                raw_name         = raw.name,
                status           = "MATCHED",
                resolved_mid     = best_entity["mid"],
                resolved_name    = best_entity["name"],
                similarity_score = best_score,
                matched_alias    = best_alias,
                is_new           = False,
                aliases_added    = new_aliases,
            )

        elif 60 <= best_score < self.threshold and best_entity:
            # AMBIGUOUS — score trop faible pour matcher automatiquement, trop élevé pour ignorer
            if self.verbose:
                print(f"    AMBIG  [{best_score:.1f}%] '{raw.name}' ≈ '{best_entity['name']}' (sous le seuil {self.threshold}%) → Nouvelle entité")
            # On crée quand même une nouvelle entité mais on le signale
            new_mid = self._generate_mid(raw.entity_type)
            return ResolutionResult(
                raw_name         = raw.name,
                status           = "AMBIGUOUS",
                resolved_mid     = new_mid,
                resolved_name    = raw.name,
                similarity_score = best_score,
                matched_alias    = None,
                is_new           = True,
                aliases_added    = raw.aliases,
            )

        else:
            # NEW — aucun match suffisant → nouvelle entité
            new_mid = self._generate_mid(raw.entity_type)
            if self.verbose:
                print(f"    NEW    [score max: {best_score:.1f}%] '{raw.name}' → MID généré: {new_mid}")
            return ResolutionResult(
                raw_name         = raw.name,
                status           = "NEW",
                resolved_mid     = new_mid,
                resolved_name    = raw.name,
                similarity_score = best_score,
                matched_alias    = None,
                is_new           = True,
                aliases_added    = raw.aliases,
            )

    # ── Génération de MID stable ─────────────────────────────────────────────

    @staticmethod
    def _generate_mid(entity_type: str) -> str:
        """Génère un Machine ID stable basé sur le type et un UUID4."""
        prefix = entity_type.upper()[:8].replace(" ", "_")
        short_id = str(uuid.uuid4()).split("-")[0].upper()
        return f"{prefix}-{short_id}"

    # ── Upsert dans Neo4j ─────────────────────────────────────────────────────

    def upsert_to_neo4j(self, driver, result: ResolutionResult, raw: RawEntity):
        """
        Persiste le résultat de résolution dans Neo4j :
        - Si NEW : crée le nœud :Entity avec le MID
        - Si MATCHED : enrichit les aliases de l'entité existante
        """
        with driver.session() as session:
            if result.is_new:
                # Créer un nouveau nœud :Entity
                session.run(
                    """
                    MERGE (e:Entity { mid: $mid })
                    ON CREATE SET
                      e.name    = $name,
                      e.type    = $type,
                      e.aliases = $aliases,
                      e.source  = $source,
                      e.createdAt = datetime()
                    ON MATCH SET
                      e.aliases = [x IN (e.aliases + $aliases) WHERE x IS NOT NULL | x],
                      e.updatedAt = datetime()
                    """,
                    {
                        "mid":     result.resolved_mid,
                        "name":    result.resolved_name,
                        "type":    raw.entity_type,
                        "aliases": list(set(raw.aliases)),
                        "source":  raw.source,
                    },
                )
            else:
                # Enrichir les aliases de l'entité existante (sans écraser)
                if result.aliases_added:
                    session.run(
                        """
                        MATCH (e:Entity { mid: $mid })
                        SET e.aliases = [x IN (coalesce(e.aliases, []) + $new_aliases)
                                         WHERE x IS NOT NULL | x],
                            e.updatedAt = datetime()
                        """,
                        {
                            "mid":         result.resolved_mid,
                            "new_aliases": result.aliases_added,
                        },
                    )

    # ── Pipeline principal ────────────────────────────────────────────────────

    def resolve_and_upsert(
        self,
        entities: list[RawEntity],
        dry_run: bool = False,
        driver=None,
    ) -> list[ResolutionResult]:
        """
        Pipeline complet : résout toutes les entités et upsert dans Neo4j.

        Args:
            entities : Liste d'entités brutes à réconcilier
            dry_run  : Si True, n'écrit pas dans Neo4j (simulation seulement)
            driver   : Driver Neo4j (si None et pas dry_run, crée une connexion)

        Returns:
            Liste des ResolutionResult pour chaque entité
        """
        if not dry_run and NEO4J_AVAILABLE:
            if driver is None:
                driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            self.load_graph_entities(driver)
        else:
            print("  [Mode dry-run] Aucune écriture en Neo4j.")
            self._graph_entities = []

        results = []
        matched = new_count = ambiguous = 0

        for raw in entities:
            res = self.resolve_entity(raw)
            results.append(res)

            if res.status == "MATCHED":
                matched += 1
            elif res.status == "NEW":
                new_count += 1
            else:
                ambiguous += 1

            if not dry_run and driver:
                self.upsert_to_neo4j(driver, res, raw)

        print(f"\n  📊 Résumé résolution :")
        print(f"     ✅  Matchés  : {matched}")
        print(f"     🆕  Nouveaux : {new_count}")
        print(f"     ⚠️  Ambigus  : {ambiguous}")
        print(f"     📦  Total    : {len(results)}")

        return results


# ─── Parsing CSV / JSON ──────────────────────────────────────────────────────

def load_entities_from_csv(filepath: str) -> list[RawEntity]:
    """Charge des entités depuis un fichier CSV."""
    entities = []
    with open(filepath, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            aliases_raw = row.get("aliases", "")
            aliases     = [a.strip() for a in aliases_raw.split("|") if a.strip()] if aliases_raw else []
            entities.append(RawEntity(
                name        = row.get("name", "").strip(),
                entity_type = row.get("type", "Entity").strip(),
                source      = row.get("source", "CSV").strip(),
                aliases     = aliases,
                properties  = {k: v for k, v in row.items()
                               if k not in ("name", "type", "source", "aliases") and v},
            ))
    return entities


def load_entities_from_json(filepath: str) -> list[RawEntity]:
    """Charge des entités depuis un fichier JSON."""
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    entities = []
    for item in data:
        entities.append(RawEntity(
            name        = item.get("name", "").strip(),
            entity_type = item.get("type", "Entity").strip(),
            source      = item.get("source", "JSON").strip(),
            aliases     = item.get("aliases", []),
            properties  = item.get("properties", {}),
        ))
    return entities


# ─── Point d'entrée CLI ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SOVEREIGN.BI Entity Resolver — Réconciliation d'entités vers Neo4j",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--input",     required=True, help="Fichier CSV ou JSON d'entités brutes")
    parser.add_argument("--threshold", type=int, default=DEFAULT_SIMILARITY_THRESHOLD,
                        help=f"Seuil de similarité fuzzy (défaut: {DEFAULT_SIMILARITY_THRESHOLD})")
    parser.add_argument("--dry-run",   action="store_true", help="Simulation sans écriture en Neo4j")
    parser.add_argument("--verbose",   action="store_true", help="Affichage détaillé")
    parser.add_argument("--output",    help="Fichier de sortie JSON pour les résultats")
    args = parser.parse_args()

    print('\n╔══════════════════════════════════════════════════════════════╗')
    print('║       SOVEREIGN.BI — Entity Resolver (Réconciliation)        ║')
    print('╚══════════════════════════════════════════════════════════════╝\n')

    # Chargement des entités
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌  Fichier introuvable : {args.input}")
        sys.exit(1)

    print(f"📂 Chargement depuis : {args.input}")
    if input_path.suffix.lower() == ".csv":
        entities = load_entities_from_csv(str(input_path))
    elif input_path.suffix.lower() == ".json":
        entities = load_entities_from_json(str(input_path))
    else:
        print("❌  Format non supporté. Utilisez .csv ou .json")
        sys.exit(1)

    print(f"  → {len(entities)} entités brutes chargées\n")

    # Résolution
    resolver = EntityResolver(threshold=args.threshold, verbose=args.verbose)
    results  = resolver.resolve_and_upsert(
        entities,
        dry_run = args.dry_run or not NEO4J_AVAILABLE,
    )

    # Rapport détaillé
    print("\n📋 Détail des résolutions :")
    for res in results:
        icon = {"MATCHED": "✅", "NEW": "🆕", "AMBIGUOUS": "⚠️"}.get(res.status, "❓")
        print(f"  {icon}  [{res.status:9s}] {res.raw_name!r:40s} → MID: {res.resolved_mid} (score: {res.similarity_score:.1f}%)")
        if res.aliases_added:
            print(f"         + aliases ajoutés: {res.aliases_added}")

    # Export JSON optionnel
    if args.output:
        output_data = [asdict(r) for r in results]
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Résultats exportés vers : {args.output}")

    mode = "dry-run" if args.dry_run else "appliqué en Neo4j"
    print(f"\n✅  Réconciliation terminée ({mode})\n")


if __name__ == "__main__":
    main()
