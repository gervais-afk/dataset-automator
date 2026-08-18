import os
import sys
import time
import json
import requests
import mlflow

# Configuration de MLflow
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../workspace/mlflow_eval.db")).replace("\\", "/")
mlflow.set_tracking_uri(f"sqlite:///{db_path}")
mlflow.set_experiment("Agent_Local_Evaluation")

# Jeu de données de test de référence (Golden Dataset)
GOLDEN_DATASET = [
    # 1. Téléphones Camerounais (Standardisation attendue à 9 chiffres commençant par 6, 2 ou 3)
    {
        "type": "phone",
        "input": "+237 6 77 88 99 00",
        "expected": "677889900",
        "desc": "Téléphone avec code pays et espaces"
    },
    {
        "type": "phone",
        "input": "699-88-77-66",
        "expected": "699887766",
        "desc": "Téléphone avec tirets"
    },
    {
        "type": "phone",
        "input": "99887766",
        "expected": "699887766",
        "desc": "Téléphone historique à 8 chiffres commençant par 9 (ajout du préfixe 6)"
    },
    # 2. Géographies Camerounaises (Régions standardisées)
    {
        "type": "geography",
        "input": "Yaoundé (Mfoundi)",
        "expected": "Centre",
        "desc": "Ville avec accent et département"
    },
    {
        "type": "geography",
        "input": "BUEA",
        "expected": "Sud-Ouest",
        "desc": "Ville anglophone en majuscules"
    },
    # 3. Monnaies / Prix (Standardisation numérique FCFA)
    {
        "type": "currency",
        "input": "15 000 FCFA",
        "expected": "15000",
        "desc": "Montant avec espace et devise FCFA"
    },
    {
        "type": "currency",
        "input": "XAF 5000",
        "expected": "5000",
        "desc": "Montant avec code XAF en préfixe"
    }
]

def load_env():
    import os
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.env"))
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

def query_local_llm(prompt: str) -> str:
    """Interroge OpenRouter Cloud LLMs (Gemini 3.5 Flash avec fallback Gemma 4)."""
    load_env()
    provider = os.getenv("LLM_PROVIDER", "local")
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    primary_model = os.getenv("PRIMARY_MODEL", "google/gemini-3.5-flash")
    fallback_model = os.getenv("FALLBACK_MODEL", "google/gemma-4-26b-a4b-it")
    
    if provider == "openrouter":
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "Dataset Automator"
        }
        
        payload = {
            "model": primary_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an expert data cleaning agent. "
                        "Respond ONLY with the cleaned and normalized value. "
                        "No explanations, no wrapper, just the final raw value."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 1024
        }
        
        try:
            url = "https://openrouter.ai/api/v1/chat/completions"
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"⚠️ Primary model Gemini failed in evaluation: {e}. Trying fallback Gemma 4...", file=sys.stderr)
            
            payload_fallback = payload.copy()
            payload_fallback["model"] = fallback_model
            
            try:
                response = requests.post(url, json=payload_fallback, headers=headers, timeout=30)
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            except Exception as fe:
                print(f"❌ Fallback model Gemma 4 also failed in evaluation: {fe}", file=sys.stderr)
                return ""
    else:
        url = "http://127.0.0.1:1234/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": "google/gemma-4-12b-qat",
            "messages": [
                {
                    "role": "system",
                    "content": "Tu es un agent expert en nettoyage de données. Réponds UNIQUEMENT avec la valeur nettoyée. Pas de phrases explicatives."
                },
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 100
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"❌ Erreur lors de l'appel LM Studio : {e}", file=sys.stderr)
            return ""

def evaluate_agent():
    load_env()
    provider = os.getenv("LLM_PROVIDER", "local")
    model_name = os.getenv("PRIMARY_MODEL", "google/gemini-3.5-flash") if provider == "openrouter" else "google/gemma-4-12b-qat"
    
    print(f"🚀 Démarrage de l'évaluation de l'agent ({model_name})...")
    
    with mlflow.start_run(run_name=f"Eval_{model_name.replace('/', '_')}_{int(time.time())}"):
        mlflow.log_param("model_name", model_name)
        mlflow.log_param("dataset_size", len(GOLDEN_DATASET))
        mlflow.log_param("temperature", 0.1)
        
        correct_count = 0
        total_latency = 0.0
        
        for item in GOLDEN_DATASET:
            prompt = ""
            if item["type"] == "phone":
                prompt = f"Normalise ce numéro de téléphone camerounais: '{item['input']}'"
            elif item["type"] == "geography":
                prompt = f"Associe cette ville du Cameroun à sa région administrative: '{item['input']}'"
            elif item["type"] == "currency":
                prompt = f"Extrais uniquement la valeur numérique de ce montant monétaire: '{item['input']}'"
                
            start_time = time.time()
            predicted = query_local_llm(prompt)
            latency = time.time() - start_time
            total_latency += latency
            
            is_correct = (predicted.lower() == item["expected"].lower())
            if is_correct:
                correct_count += 1
                
            # Log détaillé par item
            print(f"[{item['type'].upper()}] Input: '{item['input']}' | Expected: '{item['expected']}' | Predicted: '{predicted}' | Correct: {is_correct} | Latency: {latency:.2f}s")
            
        accuracy = correct_count / len(GOLDEN_DATASET)
        avg_latency = total_latency / len(GOLDEN_DATASET)
        
        # Enregistrement des métriques globales dans MLflow
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("avg_latency_seconds", avg_latency)
        
        print("\n=== RÉSULTATS DE L'ÉVALUATION ===")
        print(f"🎯 Précision globale (Accuracy) : {accuracy * 100:.1f}%")
        print(f"⏱️ Latence moyenne : {avg_latency:.2f} secondes")
        print("✅ Résultats enregistrés avec succès dans MLflow !")

if __name__ == "__main__":
    evaluate_agent()
