import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pygame
from game import SpaceRocks
import random

class SpaceRocksEnv(gym.Env):

    metadata = {"render_modes" : ["human","rgb_array"], "render_fps" : 60}

    def __init__(self, render_mode = None, frame_skip = 1):
        super(SpaceRocksEnv, self).__init__()

        self.frame_skip = frame_skip
        self.render_mode = render_mode
        self.game = SpaceRocks(render_mode=(render_mode == "human"))

        self.action_space = spaces.Discrete(6)

        self.observation_space = spaces.Box(
            low = -np.inf,
            high = np.inf, 
            shape = (31,), # 7 for spaceship + 4 per asteroid x 3 asteroids +  4 per bullet x 3 bullets
            dtype = np.float32
        )

    def reset(self, seed = None, options = None):
        """ Reset game starting state"""

        # Standard Gymnasium seed handling
        super().reset(seed = seed)

        # Lock down gloabal random modeule with seed
        if seed is not None:
            random.seed(seed)

        # Reset the underlying game engine
        obs = self.game.reset()

        # Gymnasium reset must return (observation, info_dict)
        return obs, {}
    
    def step(self, action):
        """Advances the game by multiple frames, repeating the same action."""
        
        total_reward = 0.0
        accumulated_components = {}

        for i in range(self.frame_skip):

            # execute action in engine
            obs, reward, done, info = self.game.step(action)
            total_reward += reward

            if self.render_mode == "human":
                self.game.render()

            if 'reward_components' in info:
                for comp_name, comp_val in info['reward_components'].items():
                    accumulated_components[comp_name] = accumulated_components.get(comp_name, 0.0) + comp_val
        
            # terminanted - episode ended - ship crash
            terminated = info.get('died', False)

            # truncated - episode forced to end on number of steps
            truncated = self.game.truncated

            if terminated or truncated:
                break

        info['reward_components'] = accumulated_components

        return obs, total_reward, info.get('died', False), self.game.truncated, info
    

    def render(self):
        """Renders the game for the user."""
        return self.game.render()
    
    def close(self):
        pygame.quit()