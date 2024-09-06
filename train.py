import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from agar_gym_env import AgarEnv  # Assurez-vous que c'est le bon chemin vers votre environnement
import argparse
import os
from stable_baselines3.common.callbacks import BaseCallback
from gymnasium.wrappers import TimeLimit

class RewardLoggerCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(RewardLoggerCallback, self).__init__(verbose)
        self.episode_rewards = []

    def _on_step(self) -> bool:
        return True
    
    def _on_rollout_end(self) -> None:
        """Fonction appelée à la fin de chaque itération de rollout."""
        # Affiche la récompense moyenne des épisodes de cette itération
        if len(self.episode_rewards) > 0:
            mean_reward = sum(self.episode_rewards) / len(self.episode_rewards)
            print(f"Fin de l'itération : récompense moyenne sur les épisodes = {mean_reward:.2f}")
            self.logger.record('mean_episode_reward', mean_reward)
        else:
            print("Fin de l'itération : aucune récompense enregistrée.")

        # Réinitialise les récompenses des épisodes pour la prochaine itération
        self.episode_rewards = []


# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("--resume", action="store_true", help="Resume training from a checkpoint")
parser.add_argument("--checkpoint_path", type=str, default="", help="Path to the checkpoint file")
args = parser.parse_args()

def create_env(render_mode=None):
    # Crée l'environnement AgarEnv
    env = AgarEnv(render_mode=render_mode)
    return env

# Utiliser render_mode=None pendant l'entraînement pour désactiver le rendu et limiter les steps par épisode
vec_env = DummyVecEnv([lambda: create_env(render_mode=None)])  # Par exemple, 10 steps par épisode

# Étape 3: Charger le modèle si on reprend l'entraînement
if args.resume and os.path.exists(args.checkpoint_path):
    print(f"Reprise de l'entraînement à partir du checkpoint : {args.checkpoint_path}")
    model = PPO.load(args.checkpoint_path, env=vec_env, verbose=1, tensorboard_log="./ppo_agar_tensorboard/")
else:
    print("Nouvel entraînement démarré.")
    model = PPO("CnnPolicy", vec_env, verbose=1, tensorboard_log="./ppo_agar_tensorboard/")

# Étape 4: Configurer un callback pour sauvegarder le modèle périodiquement
checkpoint_callback = CheckpointCallback(save_freq=10000, save_path='./logs/', name_prefix='ppo_agar')
reward_logger = RewardLoggerCallback(verbose=1)

# Étape 5: Lancer l'entraînement
model.learn(total_timesteps=int(1e6), callback=[checkpoint_callback, reward_logger])

# Sauvegarder le modèle entraîné
model.save("ppo_agar_model")

print("Entraînement terminé et modèle sauvegardé.")
