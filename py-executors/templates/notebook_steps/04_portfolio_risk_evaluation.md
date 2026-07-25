# ✅ Étape 4 — Évaluation Financière & Analyse de Risque

Validation quantitative du portefeuille et de la stratégie à l'aide de métriques de risque professionnelles (Sharpe, Sortino, Drawdown) via `quantstats`.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Installation de quantstats si nécessaire
try:
    import quantstats as qs
except ImportError:
    print("⏳ Installation de quantstats...")
    !pip install -q quantstats
    import quantstats as qs

print("=" * 60)
print("✅ ÉVALUATION FINANCIÈRE ET ANALYSE DE RISQUE")
print("=" * 60)

# S'assurer d'avoir les séries temporelles pour y_test
y_test_s = pd.Series(y_test) if not isinstance(y_test, pd.Series) else y_test

# ── 1. CALCUL DES RENDEMENTS (RETURNS) ──────────────────────────────
print("\n📈 1. Calcul des Rendements Journaliers...")

# Rendements de l'actif (réel)
asset_returns = y_test_s.pct_change().dropna()

# Rendements de la stratégie basée sur les prédictions
# Stratégie simple : Position Longue (1) si la prédiction monte, Courte (-1) si elle baisse
y_pred_series = pd.Series(y_pred_final, index=y_test_s.index)
pred_change = y_pred_series.diff()
position = np.sign(pred_change).shift(1).fillna(1) # Décision au jour t-1 pour le jour t

# Rendements de la stratégie = Rendement de l'actif * Position
strategy_returns = asset_returns * position.loc[asset_returns.index]
strategy_returns.name = 'Strategie_AutoARIMA'

# ── 2. RÉCUPÉRATION DU BENCHMARK (S&P 500 via yfinance) ──────────────
print("\n🔍 2. Téléchargement du Benchmark (S&P 500)...")
try:
    import yfinance as yf
    # Télécharger le S&P 500 sur la même période que y_test
    start_date = y_test_s.index.min().strftime('%Y-%m-%d')
    end_date = (y_test_s.index.max() + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    
    benchmark_df = yf.download("^GSPC", start=start_date, end=end_date, progress=False)
    
    if not benchmark_df.empty:
        benchmark_returns = benchmark_df['Close'].pct_change().dropna()
        # Alignement des index temporels (jointure interne)
        strategy_returns, benchmark_returns = strategy_returns.align(benchmark_returns, join='inner')
        print("   ✅ Benchmark S&P 500 aligné avec succès.")
    else:
        benchmark_returns = asset_returns # Fallback
        print("   ⚠️ Benchmark vide, utilisation de l'actif comme baseline.")
except Exception as e:
    print(f"   ⚠️ Échec de récupération du benchmark : {e}")
    benchmark_returns = asset_returns

# ── 3. CALCUL DES MÉTRIQUES CLÉS DE RISQUE ──────────────────────────
print("\n📊 3. Indicateurs de Performance Quantitatifs :")
print("-" * 60)

sharpe = qs.stats.sharpe(strategy_returns)
sortino = qs.stats.sortino(strategy_returns)
max_drawdown = qs.stats.max_drawdown(strategy_returns) * 100
calmar = qs.stats.calmar(strategy_returns)
omega = qs.stats.omega(strategy_returns)

print(f"   Sharpe Ratio      : {sharpe:.4f} (Indice de rendement vs volatilité globale)")
print(f"   Sortino Ratio     : {sortino:.4f} (Indice de rendement vs volatilité baissière)")
print(f"   Max Drawdown      : {max_drawdown:.2f}% (Pire perte historique crête-à-creux)")
print(f"   Calmar Ratio      : {calmar:.4f} (Performance vs Max Drawdown)")
print(f"   Omega Ratio       : {omega:.4f} (Gains extrêmes vs pertes extrêmes)")

# Log dans MLflow
import mlflow
with mlflow.start_run(run_name="Evaluation_Financiere", nested=True):
    mlflow.log_metric("Sharpe_Ratio", sharpe)
    mlflow.log_metric("Sortino_Ratio", sortino)
    mlflow.log_metric("Max_Drawdown", max_drawdown)
    mlflow.log_metric("Calmar_Ratio", calmar)

# ── 4. GÉNÉRATION DU RAPPORT VISUEL ET HTML ─────────────────────────
print("\n📊 4. Génération des Graphiques de Rendements cumulés...")

# Tracé des rendements cumulés
plt.figure(figsize=(12, 6))
qs.plots.returns(strategy_returns, benchmark=benchmark_returns, show=False)
plt.title("Rendements Cumulés : Stratégie vs S&P 500")
plt.grid(True, alpha=0.3)

save_plot_path = os.path.join(OUTPUT_DIR, "04_rendements_cumules.png")
plt.savefig(save_plot_path, dpi=150, bbox_inches='tight')
plt.show()

# Export HTML complet
report_html_path = os.path.join(OUTPUT_DIR, "rapport_performance.html")
print(f"📂 Génération du rapport complet HTML ici : {report_html_path}")
qs.reports.html(strategy_returns, benchmark=benchmark_returns, output=report_html_path, title="Rapport de Performance MLOps Finance")
```

## 🧠 Rapport Qualitatif RAG (Agent IA Senior)

{LLM_INTERPRETATION}
