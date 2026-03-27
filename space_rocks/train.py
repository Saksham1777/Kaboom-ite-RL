import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback
from game_env import SpaceRocksEnv
import os

class SpaceRocksCallback(BaseCallback):
    """
    Custom callback for logging extra game metrics to TensorBoard.
    """
    def __init__(self, verbose = 0):
        super(SpaceRocksCallback, self).__init__(verbose)
        self.action_counts = {i: 0 for i in range(7)}

    def _on_step(self):
        # Log Action Distribution
        last_action = self.locals['actions'][0]
        self.action_counts[int(last_action)] += 1

        # Log Reward Components (at end of episode)
        info = self.locals['infos'][0]
        if 'reward_components' in info:
            for name, val in info['reward_components'].items():
                self.logger.record(f"reward_comp/{name}:", val)
        
        # Log Survival Time and Score
        if self.locals['dones'][0]: # episode just ended
            self.logger.record("game/survival_time", info['survival_time_ms'])
            self.logger.record("game/score", info['score'])

            # Record action distribution percentage
            total = sum(self.action_counts.values())
            for act, count in self.action_counts.items():
                self.logger.record(f"actions/act_{act}_pct", count / total)

            self.action_counts = {i: 0 for i in range(7)}
        
        return True
    

# MAIN TRAIN LOOP

log_dir = "./logs/spacerocks_tensorboard/"
os.makedirs(log_dir, exist_ok=True)

# 2. Setup Environment
env = SpaceRocksEnv(render_mode=None)

# 3. Initialize Model (PPO)
model = PPO(
    "MlpPolicy", 
    env, 
    verbose=1, 
    tensorboard_log=log_dir,
    learning_rate=3e-4,
    n_steps=2048 # Collect 2048 frames before updating
)

# 4. Train with the Callback
print("Training started. Open TensorBoard to see results.")
model.learn(
    total_timesteps=200000, 
    callback=SpaceRocksCallback(),
    tb_log_name="PPO_run_1"
)

# 5. Save the trained brain
model.save("spacerocks_ai_v1")

