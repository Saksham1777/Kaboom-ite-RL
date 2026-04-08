import gymnasium as gym
from stable_baselines3 import PPO
from game_env import SpaceRocksEnv
import os

def main():

    version_to_test = 55
    models_dir = "./saved_models/"
    
    model_path = os.path.join(models_dir, f"spacerocks_ai_v{version_to_test}")
    
    try:
        model = PPO.load(model_path)
        print(f"Successfully loaded {model_path}. Let's see what it learned!")
    except Exception as e:
        print(f"Error: Could not find the model file.")
        return

    # 2. Initialize the environment in 'human' mode
    # This triggers the display.set_mode() in your game engine
    env = SpaceRocksEnv(render_mode="human")

    # 3. The Inference Loop
    obs, info = env.reset()
    
    try:
        while True:
            # Ask the model for the best action based on current observations
            # deterministic=True ensures it picks the most confident move
            action, _states = model.predict(obs, deterministic=True)
            
            # Apply the action (0-7) to the ship
            obs, reward, terminated, truncated, info = env.step(action)
            
            # Draw the frame to the window
            env.render()
            
            # If the ship hits an asteroid or reaches max steps, reset
            if terminated or truncated:
                print(f"Episode Finished. Score: {info['score']}. Time: {info['survival_time_ms']}")
                obs, info = env.reset()
                
    except KeyboardInterrupt:
        print("\nClosing...")
    finally:
        env.close()

if __name__ == "__main__":
    main()