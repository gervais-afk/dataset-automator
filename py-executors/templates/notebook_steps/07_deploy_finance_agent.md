# 🚀 Étape 7 — Déploiement : Assistant Boursier IA avec LangChain & FastAPI

Objectif : Exposer notre modèle d'analyse financière sous forme d'API et l'intégrer au sein d'un agent conversationnel LangChain connecté à Yahoo Finance avec une interface utilisateur dynamique générée en streaming (SSE).

> [!NOTE]
> Cette étape est présentée sous forme de guide pédagogique et de code de production. Les cellules ci-dessous ne sont pas exécutées dans le notebook pour éviter de bloquer l'exécution avec le démarrage d'un serveur web local.

## 1. Concepts de l'Architecture de l'Agent IA

L'architecture se compose d'un backend FastAPI gérant un agent LangChain et d'un frontend React dynamique (Thesis C1Chat).
L'agent utilise le modèle d'OpenAI configuré pour router les requêtes d'interface utilisateur dynamique (via des balises XML générées par le LLM).

```
   ┌─────────────────┐       (SSE Stream)        ┌──────────────────┐
   │  Frontend React │ <──────────────────────── │  Backend FastAPI │
   │ (Thesis C1Chat) │ ────────────────────────> │ (LangChain Agent)│
   └─────────────────┘      (POST /chat)         └──────────────────┘
                                                          │
                                            ┌─────────────┴─────────────┐
                                            ▼                           ▼
                                    ┌──────────────┐            ┌──────────────┐
                                    │ Outils Agent │            │  Auto-ARIMA  │
                                    │  (yfinance)  │            │  (Prévision) │
                                    └──────────────┘            └──────────────┘
```

## 2. Définition des Outils de l'Agent (Tools)

Ces outils permettent à l'agent conversationnel d'aller chercher de l'information financière fraîche en temps réel sur Yahoo Finance.

```python
# CODE DE PRODUCTION BACKEND - À intégrer dans votre service d'agent
from langchain_core.tools import tool
import yfinance as yf

@tool
def get_stock_price(ticker: str) -> str:
    """Prend un symbole boursier (ticker) et retourne le prix actuel en temps réel de l'action."""
    try:
        stock = yf.Ticker(ticker)
        price = stock.fast_info['lastPrice']
        return f"Le prix actuel de {ticker} est de {price:.2f} USD."
    except Exception as e:
        return f"Erreur lors de la récupération du prix pour {ticker} : {e}"

@tool
def get_historical_stock_price(ticker: str, start_date: str, end_date: str) -> str:
    """Récupère l'historique des prix d'un ticker sur une plage de dates (format YYYY-MM-DD) pour tracer des graphiques."""
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if not df.empty:
            summary = df['Close'].describe().to_string()
            return f"Historique pour {ticker} du {start_date} au {end_date} :\n{summary}"
        return f"Aucune donnée trouvée pour {ticker}."
    except Exception as e:
        return f"Erreur historique : {e}"

@tool
def get_balance_sheet(ticker: str) -> str:
    """Retourne les données clés du bilan comptable (Balance Sheet) pour un ticker donné."""
    try:
        stock = yf.Ticker(ticker)
        balance = stock.balance_sheet
        if not balance.empty:
            return balance.iloc[:, :2].to_string() # Retourne les deux dernières années
        return f"Bilan introuvable pour {ticker}."
    except Exception as e:
        return f"Erreur bilan : {e}"
```

## 3. Initialisation de l'Agent et Point de Terminaison FastAPI (Streaming SSE)

Ce script configure l'agent avec une mémoire de session et montre comment FastAPI envoie en streaming les tokens et les composants d'interface générés.

```python
# CODE DE PRODUCTION BACKEND - Serveur FastAPI
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

app = FastAPI(title="FastAPI Stock Agent API")

# Initialisation de la mémoire et du modèle via LM Studio (100% Local)
memory = MemorySaver()
model = ChatOpenAI(
    model="qwen2.5-coder-3b-instruct", 
    temperature=0, 
    base_url="http://localhost:1234/v1", 
    api_key="lm-studio"
)

# Liste des outils utilisables par l'agent
tools = [get_stock_price, get_historical_stock_price, get_balance_sheet]
agent = create_react_agent(model, tools=tools, checkpointer=memory)

class ChatRequest(BaseModel):
    message: str
    thread_id: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    config = {"configurable": {"thread_id": req.thread_id}}
    
    # Prompt système définissant les capacités de l'agent
    system_message = (
        "You are a stock analysis assistant. You have the ability to get real-time stock prices, "
        "historical stock prices, news, and balance sheet data for a given ticker symbol."
    )
    
    def event_stream():
        inputs = {"messages": [("system", system_message), ("user", req.message)]}
        # Mode messages pour streamer directement les réponses textuelles et composants d'UI XML
        for token, _ in agent.stream(inputs, config=config, stream_mode="messages"):
            yield token.content

    # StreamingResponse utilise text/event-stream pour du SSE en temps réel
    return StreamingResponse(
        event_stream(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache", 
            "Connection": "keep-alive"
        }
    )
```
