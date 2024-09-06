import gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from agar_gym_env import AgarEnv  # Assurez-vous que c'est le bon chemin vers votre environnement
import matplotlib.pyplot as plt

# Charger l'environnement avec le mode de rendu
env = AgarEnv(render_mode="human")  # Ajoutez render_mode="human" pour voir le rendu

# Environnement vectorisé
vec_env = DummyVecEnv([lambda: env])

# Charger le modèle entraîné à partir du fichier .zip
model = PPO.load("logs/ppo_agar_10000_steps.zip")

# Réinitialiser l'environnement
obs = vec_env.reset()

# Activer la caméra globale, si nécessaire
env.game_state.cam.toggle_global_view()

# Boucle pour tester l'agent
for _ in range(100):
    # Prendre l'action la plus probable (déterministe)
    action, _states = model.predict(obs, deterministic=True)  
    obs, reward, done, info = vec_env.step(action)

    # Afficher l'environnement
    vec_env.render()
    # Si l'agent atteint une condition de fin, réinitialiser l'environnement
    if done[0]:  # Note: 'done' est une liste dans un DummyVecEnv
        print("L'agent a atteint une condition de fin.")
        obs = vec_env.reset()

# Fermer proprement l'environnement
vec_env.close()
