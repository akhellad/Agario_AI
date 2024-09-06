import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from agar_gym_env import AgarEnv
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--resume", action="store_true", help="Resume training from a checkpoint")
parser.add_argument("--checkpoint_path", type=str, default="", help="Path to the checkpoint file")
args = parser.parse_args()

def create_env(render_mode=None):
    env = AgarEnv(render_mode=render_mode)
    return env

# Utiliser render_mode=None pendant l'entraînement pour désactiver le rendu
vec_env = DummyVecEnv([lambda: create_env(render_mode=None)]) 

# Étape 3: Charger le modèle si on reprend l'entraînement
if args.resume and os.path.exists(args.checkpoint_path):
    print(f"Reprise de l'entraînement à partir du checkpoint : {args.checkpoint_path}")
    model = PPO.load(args.checkpoint_path, env=vec_env, verbose=1, tensorboard_log="./ppo_agar_tensorboard/")
else:
    print("Nouvel entraînement démarré.")
    model = PPO("CnnPolicy", vec_env, verbose=1, tensorboard_log="./ppo_agar_tensorboard/")

# Étape 4: Configurer un callback pour sauvegarder le modèle périodiquement
checkpoint_callback = CheckpointCallback(save_freq=10000, save_path='./logs/', name_prefix='ppo_agar')

# Étape 5: Lancer l'entraînement
model.learn(total_timesteps=int(1e6), callback=[checkpoint_callback])

# Sauvegarder le modèle entraîné
model.save("ppo_agar_model")

print("Entraînement terminé et modèle sauvegardé.")
