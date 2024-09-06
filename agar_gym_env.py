import gymnasium as gym
from gymnasium import spaces
import numpy as np
import pygame
from agar import GameState, MAIN_SURFACE, SCREEN_WIDTH, SCREEN_HEIGHT, getDistance, initialize_pygame
import cv2
import matplotlib.pyplot as plt
import os  # Pour gérer les fichiers
import glob

class AgarEnv(gym.Env):
    """Environnement personnalisé pour jouer à Agar.io avec OpenAI Gym."""

    def __init__(self, render_mode=None):
        super(AgarEnv, self).__init__()

        # Set the global render mode before initializing pygame
        global RENDER_MODE
        RENDER_MODE = render_mode

        pygame.init()
        pygame.font.init()


        # Define screen dimensions
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT

        # Set the render mode
        self.render_mode = render_mode
        self.image_counter = 0  # Counter for saving images


        # Initialize Pygame and the game state
        if self.render_mode == "human":
            self.main_surface = initialize_pygame(render_mode)
            print(self.main_surface)
            self.clock = pygame.time.Clock()
        else:
            initialize_pygame(render_mode)
            self.main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.clock = None

        # Define action space: 2 continuous actions (x, y movement)
        self.action_space = spaces.Box(low=-1, high=1, shape=(2,), dtype=np.float32)

        # Define observation space: game state as an image
        self.observation_space = spaces.Box(low=0, high=255, shape=(84, 84, 3), dtype=np.uint8)

        # Initialize the game state
        self.init_game()

    def init_game(self):
        """Initializes or resets the game state."""
        self.game_state = GameState(surface=self.main_surface)

    def reset(self, seed=None, options=None):
        """Resets the environment for a new episode."""
        super().reset(seed=seed)  # Call parent method to handle the seed
        if seed is not None:
            np.random.seed(seed)

        self.init_game()

        # Render the environment if necessary
        if self.render_mode == "human":
            self.render()

        # Return the initial observation and an empty info dictionary
        return self.get_observation(), {}

    def get_observation(self):
        """Captures the game state as an image for the agent's observation."""
        if self.render_mode == "human" and self.main_surface:
            # Capture the game state from the display surface
            obs = np.array(pygame.surfarray.array3d(self.main_surface))
        else:
            # Create a dummy surface for observation when not rendering
            dummy_surface = pygame.Surface((self.width, self.height))
            self.game_state.render_to_surface(dummy_surface)
            obs = np.array(pygame.surfarray.array3d(dummy_surface))
        
        obs_resized = cv2.resize(obs, (84, 84))

        return obs_resized

    def step(self, action):
        """Executes an action in the environment with a more complete reward system."""
        dx, dy = action
        self.game_state.blob.move(dx, dy)
        previous_mass = self.game_state.blob.mass
        self.game_state.update()
        obs = self.get_observation()
        new_mass = self.game_state.blob.mass
        mass_gain = new_mass - previous_mass
        reward = 0
        if mass_gain > 0:
            reward += mass_gain

        if dx == 0 and dy == 0:
            reward -= 0.1

        for bot in self.game_state.bots[:]:  # Iterate over a copy of the bot list
            # Calculate the distance between the blob and the bot
            distance = getDistance((self.game_state.blob.x, self.game_state.blob.y), (bot.x, bot.y))
            
            # Define the threshold for "eating" the bot
            collision_threshold = (self.game_state.blob.mass / 2) + (bot.mass / 2)
        
            # Check if the blob is large enough and close enough to eat the bot
            if distance <= collision_threshold and self.game_state.blob.mass > bot.mass:
                reward += 100  # Reward for eating a bot
                print(f"Bot eaten! New reward: {reward}")
                self.game_state.bots.remove(bot)  # Remove the bot after it is eaten


        if self.game_state.blob not in self.game_state.painter.paintings:
            reward -= 1000

        for cell in self.game_state.cells.list[:]:  # Iterate over a copy of the list
            # Calculate the distance between the blob and the cell
            distance = getDistance((self.game_state.blob.x, self.game_state.blob.y), (cell.x, cell.y))

            # Define the threshold for "eating" a cell
            collision_threshold = (self.game_state.blob.mass / 2) + cell.mass / 2

            # Check if the blob is close enough to eat the cell
            if distance <= collision_threshold:
                reward += 10  # Reward for eating a cell
                self.game_state.cells.list.remove(cell)  # Remove the cell after it is eaten


        min_distance_to_wall = 20 
        x, y = self.game_state.blob.x, self.game_state.blob.y
        if x < min_distance_to_wall or x > (self.width - min_distance_to_wall) or y < min_distance_to_wall or y > (self.height - min_distance_to_wall):
            reward -= 1  # Penalty for being too close to any wall

        reward += 0.1

        terminated = self.game_state.blob.mass > 500 or self.game_state.blob not in self.game_state.painter.paintings

        truncated = False

        # Render the environment if necessary
        if self.render_mode == "human":
            self.render()

        # Return observation, reward, termination, truncation, and an empty info dictionary
        return obs, reward, terminated, truncated, {}


    def render(self, mode='human'):
        """Display the game on the screen if in human mode."""
        if self.render_mode == "human" and self.main_surface:
            # Si le mode de rendu est "human", on affiche le jeu sur l'écran principal.
            self.game_state.render()


    def close(self):
        """Ferme l'environnement."""
        pygame.quit()
    
    def toggle_global_view(self):
        """Permet à l'agent de basculer entre la vue globale et la vue du joueur."""
        self.game_state.cam.toggle_global_view()
    
    def seed(self, seed=None):
        """Fixe la graine pour la reproductibilité."""
        np.random.seed(seed)
        return [seed]

if __name__ == "__main__":
    print("Testing AgarEnv with render_mode='human'...")
    env = AgarEnv(render_mode="human")
    env.reset()

    # Run a few steps to test
    for _ in range(50):
        action = env.action_space.sample()  # Random action
        obs, reward, terminated, truncated, info = env.step(action)
        cv2.imshow("Observation", cv2.cvtColor(obs, cv2.COLOR_BGR2RGB))
        plt.imshow(obs)
        plt.show()

    env.close()