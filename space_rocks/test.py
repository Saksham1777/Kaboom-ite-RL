import gymnasium as gym
from stable_baselines3 import PPO
from game_env import SpaceRocksEnv
import os
import argparse
import csv
import numpy as np


def run_visual_mode(model, env, num_episodes):
    """ Visual analysis"""
    print(f"Starting visual mode model- {model}, for {num_episodes} times")

    for ep in range(num_episodes):

        obs, info = env.reset()
        done = False

        while not done:
            action, _states = model.predict(obs, deterministic = True)
            obs, reward, terminated, truncated, info = env.step(action)
            env.render()

            if terminated or truncated:
                print(f"Episode {ep + 1} Finished | Score: {info['score']} | Time: {info['survival_time_ms']} ms")
                done = True


def run_benchmark_mode(model, env, version, test_seeds, episodes_per_seed):
    """Testing against multiple seeds to see generic learning"""
    print("Benchmark mode")
    print(f"Testing {len(test_seeds)} seeds, {episodes_per_seed} episodes per seed.")

    # csv saving
    csv_file = "benchmark_results.csv"
    file_exists = os.path.isfile(csv_file)

    # append data
    with open(csv_file, mode = 'a', newline= '') as file:
        writer = csv.writer(file)
        
        if not file_exists:
            # create - happens 1st time 
            writer.writerow(["Model_Version", "Seed", "Avg_Score", "Avg_Survival_ms", "Episodes_Tested"])

        total_benchmark_score = 0

        for current_seed in test_seeds:
            seed_score = []
            seed_times = []

            for ep in range(episodes_per_seed):

                obs, info = env.reset(seed=current_seed)
                done = False

                while not done:
                    action, _states = model.predict(obs, deterministic = True)
                    obs, reward, terminated, truncated, info = env.step(action)

                    if terminated or truncated:
                        seed_score.append(info['score'])
                        seed_times.append([info['survival_time_ms']])
                        done = True

            avg_score = np.mean(seed_score)
            avg_time = np.mean(seed_times)
            total_benchmark_score += avg_score


            print(f"Seed {current_seed} Complete | Avg Score: {avg_score:.1f} | Time: {avg_time:.2f}")

            writer.writerow([f"v{version}", current_seed, avg_score, avg_time, episodes_per_seed])

    print(f"\nBenchmark Complete! Overall Average Score: {total_benchmark_score / len(test_seeds):.1f}")
    print(f"\n Overall avg time : {avg_time}")
    print(f"Results appended to {csv_file}")


def main():

    # argument parsing
    parser = argparse.ArgumentParser(description= "Test SpaceRocks RL Agent")
    parser.add_argument( '--mode', type=str, choices =  ['v', 'b'], default= 'v', 
                        help = "Choose v for visual and b for run test")
    parser.add_argument('--version', type = int, required= True,
                        help = "Model number")
    parser.add_argument('--episodes', type = int, default=25,
                        help = "Number of episodes per seed")

    args = parser.parse_args()

    models_dir = "./saved_models/"
    model_path = os.path.join(models_dir, f"spacerocks_ai_v{args.version}")
    
    try:
        model = PPO.load(model_path)
        print(f"Successfully loaded {model_path}: version: {args.version}")
    except Exception as e:
        print(f"Error: Could not find the model file.")
        return

    if args.mode == 'v':
        env = SpaceRocksEnv(render_mode= "human", frame_skip=4)
        run_visual_mode(model, env, args.episodes)
        env.close()
    elif args.mode == 'b':
        env = SpaceRocksEnv(render_mode=None)
        test_seeds = [101, 202, 303, 404, 505]
        run_benchmark_mode(model, env, args.version, test_seeds, args.episodes)
        env.close()


if __name__ == "__main__":
    main()