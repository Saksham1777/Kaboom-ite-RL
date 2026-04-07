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
        self.action_counts = {i: 0 for i in range(6)}

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

            # Calculate and log accuracy
            shots = info.get('ep_shots_fired', 0)
            hits = info.get('ep_asteroids_hit', 0)

            if shots > 0:
                accuracy_pct = (hits / shots) * 100.0
            else:
                accuracy_pct = 0.0
                
            self.logger.record("game/shots_fired", shots)
            self.logger.record("game/accuracy_pct", accuracy_pct)

            # Record action distribution percentage
            total = sum(self.action_counts.values())
            for act, count in self.action_counts.items():
                self.logger.record(f"actions/act_{act}_pct", count / total)

            self.action_counts = {i: 0 for i in range(6)}
        
        return True
    

# MAIN TRAIN LOOP

def linear_schedule(start_lr: float, end_lr: float):
    def func(progress_remaining: float) -> float:
        # When progress_remaining is 1, return start_lr
        # When progress_remaining is 0, return end_lr
        return end_lr + (start_lr - end_lr) * progress_remaining
    return func

version = 52

log_dir = "./logs/spacerocks_tensorboard/"
os.makedirs(log_dir, exist_ok=True)

models_dir = "./saved_models/"
os.makedirs(models_dir, exist_ok=True)

# 2. Setup Environment
env = SpaceRocksEnv(render_mode=None)

policy_kwargs = dict(
    net_arch=dict(pi=[256, 256], vf=[256, 256])
)

# 3. Initialize Model (PPO)
model = PPO(
    "MlpPolicy", 
    env, 
    verbose=1, 
    tensorboard_log=log_dir,
    learning_rate=3e-4,
    gamma=0.995,
    n_steps=4096, # Collect 2048 frames before updating
    batch_size = 128,
    n_epochs = 10,
    ent_coef=0.01,
    clip_range=0.2,
    policy_kwargs=policy_kwargs,
)

# 4. Train with the Callback
print("Training started. Open TensorBoard to see results.")
model.learn(
    total_timesteps=600000, 
    callback=SpaceRocksCallback(),
    tb_log_name=f"PPO_run_{version}"
)

# 5. Save the trained brain
save_path = os.path.join(models_dir, f"spacerocks_ai_v{version}")
model.save(save_path)
print(f"Model saved successfully to {save_path}.zip")

