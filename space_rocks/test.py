import gymnasium as gym
from stable_baselines3 import PPO
from game_env import SpaceRocksEnv

def main():
    # 1. Load the trained model
    # SB3 automatically looks for 'spacerocks_ai_v1.zip'
    model_name = "spacerocks_ai_v12"
    
    try:
        model = PPO.load(model_name)
        print(f"Successfully loaded {model_name}. Let's see what it learned!")
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
            
            # Apply the action (0-6) to the ship
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