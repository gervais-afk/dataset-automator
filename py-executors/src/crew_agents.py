import os
import json
import pandas as pd
from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI
from crewai.tools import tool

# 1. Configuration du LLM Local (LM Studio)
# Assurez-vous que LM Studio est lancé sur le port 1234
os.environ["OPENAI_API_KEY"] = "lm-studio"
local_llm = ChatOpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
    model="google/gemma-4-12b",
    temperature=0.1
)

# 2. Création des Outils Déterministes (Option B)
@tool("Nettoyeur de Colonne")
def clean_column_tool(file_path: str, column_name: str, action: str) -> str:
    """
    Outil sécurisé pour nettoyer une colonne. 
    Les actions supportées sont : 'drop', 'impute_mean', 'impute_median'.
    """
    try:
        df = pd.read_csv(file_path)
        if column_name not in df.columns:
            return f"Erreur: Colonne {column_name} introuvable."
            
        if action == "drop":
            df = df.drop(columns=[column_name])
        elif action == "impute_mean":
            df[column_name] = df[column_name].fillna(df[column_name].mean())
        elif action == "impute_median":
            df[column_name] = df[column_name].fillna(df[column_name].median())
        else:
            return f"Action {action} non supportée."
            
        df.to_csv(file_path, index=False)
        return f"Succès : L'action {action} a été appliquée sur {column_name}."
    except Exception as e:
        return f"Erreur lors du nettoyage : {str(e)}"

# 2.5 Outil RAG Base de Connaissances
from rag_pipeline import query_knowledge_base

@tool("Recherche Expertise MLOps")
def rag_knowledge_tool(query: str) -> str:
    """
    Outil permettant de consulter la base de connaissances du projet. 
    Utilise-le pour lire les procédures expertes (Stacking, Pseudo-labeling, MLOps, etc.).
    """
    return query_knowledge_base(query)

# 3. Définition des Agents
data_engineer = Agent(
    role='Data Engineer Spécialiste de la Fiabilité',
    goal="""Exécuter aveuglément et précisément la stratégie JSON fournie 
    sans jamais inventer d'étapes supplémentaires. Tu dois logger chaque action.""",
    backstory="""Tu es un robot exécutant très strict. Tu reçois un JSON contenant un tableau 'steps'. 
    Pour CHAQUE objet dans 'steps', tu DOIS appeler l'outil 'Nettoyeur de Colonne'. 
    Si une colonne n'existe pas, tu l'ignores et tu passes à la suite, sans paniquer.""",
    verbose=True,
    allow_delegation=False,
    llm=local_llm,
    tools=[clean_column_tool]
)

data_scientist = Agent(
    role='Machine Learning Architect & Reviewer',
    goal="""Valider le travail de l'Engineer et dicter le prochain modèle à entraîner.
    Tu dois utiliser l'outil 'Recherche Expertise MLOps' pour justifier ta recommandation.""",
    backstory="""Tu es un Critique (QA) et un Architecte ML. Ton rôle est double :
    1. Vérifier que l'Engineer a bien traité les données.
    2. Utiliser la Base de Connaissances (RAG) pour chercher 'Quel modèle utiliser pour ce dataset ?'.
    Tu DOIS impérativement formater ta réponse finale en JSON.""",
    verbose=True,
    allow_delegation=False,
    llm=local_llm,
    tools=[rag_knowledge_tool]
)

# 4. Définition des Tâches
def create_cleaning_task(file_path: str, strategy: str) -> Task:
    return Task(
        description=f"""
        Voici la stratégie stricte au format JSON à appliquer sur {file_path} :
        {strategy}
        
        Parcours le tableau 'steps'. Pour chaque élément, appelle 'Nettoyeur de Colonne'.
        Si une erreur survient (ex: colonne introuvable), note-la dans ton rapport mais continue.
        """,
        expected_output="Un rapport d'exécution détaillant les succès et les échecs de chaque étape.",
        agent=data_engineer
    )

def create_validation_task(file_path: str) -> Task:
    return Task(
        description=f"""
        Le Data Engineer a terminé sur le fichier {file_path}.
        Fais une requête à la base de connaissances (outil RAG) pour trouver le meilleur modèle pour la suite.
        Tu dois répondre STRICTEMENT avec un objet JSON ayant la structure suivante:
        {{
            "narrative_summary": "Résumé de tes trouvailles et de la qualité",
            "quality_score": 90,
            "next_recommended_model": "RandomForest / XGBoost / K-Means..."
        }}
        """,
        expected_output="Un JSON valide contenant narrative_summary, quality_score, et next_recommended_model.",
        agent=data_scientist
    )

# 5. Fonction Principale pour Orchestrer le Crew
def run_dataset_crew(file_path: str, strategy_json: str):
    # Créer une copie de travail pour le Crew
    work_file = file_path.replace('.csv', '_crew_working.csv')
    pd.read_csv(file_path).to_csv(work_file, index=False)
    
    task1 = create_cleaning_task(work_file, strategy_json)
    task2 = create_validation_task(work_file)
    
    crew = Crew(
        agents=[data_engineer, data_scientist],
        tasks=[task1, task2],
        process=Process.sequential,
        verbose=True
    )
    
    # Lancement de l'équipe
    result = crew.kickoff()
    return str(result), work_file
