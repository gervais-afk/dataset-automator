import os
import glob
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class LocalRAGPipeline:
    def __init__(self, kb_dir: str = None):
        if kb_dir:
            self.kb_dir = kb_dir
        else:
            # Chemin par défaut depuis py-executors/src vers dataset_automator/knowledge_base
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.kb_dir = os.path.join(base_dir, "knowledge_base")
            
        self.documents = []
        self.metadata = []
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if not os.path.exists(self.kb_dir):
            print(f"⚠️ Dossier knowledge_base introuvable à : {self.kb_dir}")
            return

        # Recherche récursive des fichiers markdown
        search_pattern = os.path.join(self.kb_dir, "**", "*.md")
        files = glob.glob(search_pattern, recursive=True)
        
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.documents.append(content)
                    self.metadata.append({
                        "file_name": os.path.basename(file_path),
                        "path": file_path
                    })
            except Exception as e:
                print(f"Erreur lors de la lecture de {file_path}: {e}")

        if self.documents:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

    def query(self, user_query: str, top_k: int = 3) -> str:
        """Recherche les documents les plus pertinents pour la requête."""
        if not self.documents or self.tfidf_matrix is None:
            return "Erreur : La base de connaissances est vide ou n'a pas pu être chargée."

        # Vectoriser la requête
        query_vec = self.vectorizer.transform([user_query])
        
        # Calculer la similarité cosinus
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Récupérer les top_k indices
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.05: # Seuil de pertinence minimum
                doc_name = self.metadata[idx]["file_name"]
                content = self.documents[idx]
                # Extraire un extrait (les 1000 premiers caractères)
                snippet = content[:1000] + ("..." if len(content) > 1000 else "")
                results.append(f"--- Document pertinent trouvé : {doc_name} ---\n{snippet}\n")
        
        if not results:
            return "Aucune information pertinente trouvée dans la base de connaissances pour cette requête."
            
        return "\n\n".join(results)

# Instance globale (Singleton) pour une utilisation facile dans les outils
_rag_instance = None

def get_rag_pipeline():
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = LocalRAGPipeline()
    return _rag_instance

def query_knowledge_base(query_text: str) -> str:
    """Fonction utilitaire pour interroger la base de connaissances."""
    rag = get_rag_pipeline()
    return rag.query(query_text)

if __name__ == "__main__":
    # Test basique
    print("Test du RAG Local...")
    result = query_knowledge_base("Comment faire du stacking ou du pseudo-labeling ?")
    print(result)
