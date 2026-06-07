# Kaboom-ite RL Agent

An iterative Reinforcement Learning project focused on building an autonomous agent capable of playing **Kaboom-ite**, a custom 2D space shooter. This environment is based on the same game developed in my companion repository, **Kaboom-ite**.

Built entirely from scratch, this project tackles the challenge of translating custom Pygame mechanics into a standardized Gymnasium environment and training a **Proximal Policy Optimization (PPO)** agent to navigate a toroidal (wrap-around) space, avoid asteroids, and strategically engage targets.

---

## Project Overview

The primary goal of this project was to have fun and to investigate how reinforcement learning agents adapt to non-traditional game mechanics such as:

- Toroidal (screen-wrap) navigation
- Momentum-based movement physics
- Sparse combat opportunities
- Dynamic obstacle avoidance
- Continuous spatial reasoning

The project serves as both an RL research playground and a practical exercise in designing custom environments, reward functions, and training pipelines.

---

## Tech Stack

- **Python 3**
- **Pygame** – Custom 2D game engine and physics mechanics
- **Gymnasium** – Custom environment wrapper (`SpaceRocksEnv`)
- **Stable-Baselines3** – PPO algorithm implementation
- **TensorBoard** – Training metrics tracking and visualization

---

## The Environment (`SpaceRocksEnv`)

The environment converts raw game physics into a continuous observation vector:

```python
Box(31,)
```

### Spaceship (7 Features)

- Position (`x`, `y`)
- Velocity (`vx`, `vy`)
- Orientation represented using:
  - `sin(angle)`
  - `cos(angle)`
- Additional ship state information

### Asteroids (12 Features)

Tracks the **3 closest asteroids**:

- 4 features per asteroid
- Total: `12`

### Bullets (12 Features)

Tracks up to **3 active bullets**:

- 4 features per bullet
- Total: `12`

> **Note:** All distance calculations utilize toroidal math to account for the screen-wrap effect. This ensures the agent correctly understands when an asteroid is effectively "behind" it across a screen boundary.

---

## Action Space

The agent selects from a `Discrete(6)` action space:

| Action | Description |
|----------|-------------|
| `NOOP` | Do nothing |
| `FORWARD` | Apply forward thrust |
| `BACKWARD` | Apply reverse thrust |
| `ROT_L_BG` | Rotate left |
| `ROT_R_BG` | Rotate right |
| `SHOOT` | Fire weapon |

---

## Training Pipeline

The agent is trained using **Proximal Policy Optimization (PPO)**.

### Frame Skipping

The environment operates with:

```python
frame_skip = 4
```

This allows the agent to hold an action for multiple frames, which:

- Stabilizes physical maneuver learning
- Encourages smoother navigation
- Reduces action jitter
- Speeds up training

### Custom TensorBoard Metrics

A custom `SpaceRocksCallback` records:

- Survival Time
- Overall Score
- Shooting Accuracy (%)
- Action Distribution
- Segmented Reward Components

---

## The Training Journey

Building this agent has been highly iterative. Much of the work involved identifying unexpected strategies discovered by the model and redesigning the environment to encourage genuine skill development.

### Early Hurdles & Physics Fixes (v9 – v20)

The first major obstacle was the screen-wrap mechanic.

Initially, when an asteroid crossed one side of the screen and reappeared on the opposite side, the agent perceived an enormous distance change. This caused reward instability and prevented meaningful learning.

The solution was implementing proper **toroidal vectors and distance calculations**, allowing the agent to reason about wrap-around space correctly.

### The "Spinning Turret" Exploit (v26 – v36)

Once shooting mechanics were introduced, the agent discovered an unintended strategy:

> Remain stationary, rotate continuously, and spam bullets.

From the model's perspective, this maximized survival while minimizing movement risk.

To address this exploit:

- Reward shaping was redesigned
- Static behavior penalties were introduced
- Movement and avoidance incentives were strengthened

This forced the model to actively navigate the environment rather than exploit a stationary strategy.

### Humanizing the Movement (v58 – v79)

Another challenge emerged as the agent became increasingly reactive.

Because actions were selected every frame, movement appeared extremely jittery and robotic. The ship constantly changed direction in unnatural ways.

Introducing **frame skipping** solved this problem by forcing the policy to commit to actions for multiple frames.

The result was:

- Smoother navigation
- More realistic drifting
- Better dodge behavior
- Increased training stability

---

## How to Run

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Train the Agent

```bash
python train.py
```

### Monitor Training

```bash
tensorboard --logdir ./logs/spacerocks_tensorboard/
```

Open the generated local URL in your browser to inspect training metrics.

---


Expected benefits:

- Improved late-stage convergence
- More stable policy refinement
- Better long-term performance

---

## Features

- Custom Gymnasium environment
- Pygame-based physics simulation
- PPO training with Stable-Baselines3
- TensorBoard integration
- Toroidal-distance-aware observations
- Frame-skipping optimization
- Custom reward shaping
- Detailed training analytics


