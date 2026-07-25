# 🎮 Étape 3 — Apprentissage par Renforcement (PPO Policy Training)

Objectif : Entraîner un agent intelligent à prendre des décisions optimales par essai-erreur dans un environnement simulé (CartPole) pour maximiser les récompenses cumulées.

```python
import gymnasium as gym
import numpy as np
import os
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.monitor import Monitor
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🎮 APPRENTISSAGE PAR RENFORCEMENT (PPO)")
print("=" * 60)

# ── 1. Initialisation de l'Environnement de Simulation ────────────────
# Nous utilisons CartPole-v1 comme environnement de référence standard
env_id = "CartPole-v1"
print(f"⏳ Initialisation de l'environnement : {env_id}")
env = gym.make(env_id)
env = Monitor(env)

print(f"   - Espace d'observations (State space) : {env.observation_space}")
print(f"   - Espace d'actions possibles (Action space) : {env.action_space}")

# ── 2. Entraînement de l'Agent PPO ────────────────────────────────────
timesteps = 10000
print(f"\n⏳ Entraînement de l'agent PPO sur {timesteps} étapes (timesteps)...")
model = PPO("MlpPolicy", env, verbose=0, learning_rate=0.0003, random_state=42)
model.learn(total_timesteps=timesteps)
print("   ✅ Apprentissage complété.")

# ── 3. Évaluation de la Politique ────────────────────────────────────
print("\n⏳ Évaluation des performances sur 10 épisodes...")
mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10)
print(f"   - Récompense moyenne cumulée : {mean_reward:.2f} (Écart-type: {std_reward:.2f})")

# Enregistrement pour l'orchestrateur
best_name = "PPO RL Policy"
best_model = model
results = {best_name: {"score": float(mean_reward), "model": model}}
```

### Analyse des Courbes de Récompense

```python
# Extraction des historiques du moniteur
ep_rewards = env.get_episode_rewards()

plt.figure(figsize=(10, 5))
plt.plot(ep_rewards, label="Récompense par Épisode", color="teal", alpha=0.6)
# Lissage par moyenne mobile
if len(ep_rewards) > 5:
    lissage = np.convolve(ep_rewards, np.ones(5)/5, mode='valid')
    plt.plot(lissage, label="Moyenne glissante (5)", color="red", lw=2)

plt.xlabel("Épisodes")
plt.ylabel("Récompense accumulée")
plt.title("Courbe d'Apprentissage de l'Agent (Récompenses cumulatives)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(OUTPUT_DIR, '03_rl_training_rewards.png'), dpi=150)
plt.show()
```
