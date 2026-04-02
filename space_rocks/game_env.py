import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pygame
from game import SpaceRocks

class SpaceRocksEnv(gym.Env):

    metadata = {"render_modes" : ["human","rgb_array"], "render_fps" : 60}

    def __init__(self, render_mode = None):
        super(SpaceRocksEnv, self).__init__()

        self.render_mode = render_mode
        self.game = SpaceRocks(render_mode=(render_mode == "human"))

        self.action_space = spaces.Discrete(6)

        self.observation_space = spaces.Box(
            low = -np.inf,
            high=np.inf, 
            shape=(31,), # 7 for spaceship + 4 per asteroid x 3 asteroids +  4 per bullet x 3 bullets
            dtype=np.float32
        )

    def reset(self, seed = None, options = None):
        """ Reset game starting state"""

        # Standard Gymnasium seed handling
        super().reset(seed = seed)

        # Reset the underlying game engine
        obs = self.game.reset()

        # Gymnasium reset must return (observation, info_dict)
        return obs, {}
    
    def step(self, action):
        """Advances the game by one frame based on the AI's action."""

        # execute action in engine
        obs, reward, done, info = self.game.step(action)

        # terminanted - episode ended - ship crash
        terminated = info.get('died', False)

        # truncated - episode forced to end on number of steps
        truncated = self.game.truncated

        return obs, reward, terminated, truncated, info
    

    def render(self):
        """Renders the game for the user."""
        if self.render_mode == "human":
            return self.game.render()
        elif self.render_mode == "rgb_array":
            return pygame.surfarray.array3d(self.game.screen)
    
    def close(self):
        pygame.quit()