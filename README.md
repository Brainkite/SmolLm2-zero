# 🧠 SmolLM2-zero: Teaching SmolLM2 to "Think Before Answering"

This repository is a fork dedicated to reproducing the "aha moment" observed in DeepSeek R1 model training, using the SmolLM2 1.7B model and Group Relative Policy Optimization (GRPO).

## 🔍 Project Overview

The DeepSeek R1 release demonstrated that through pure reinforcement learning, language models can be taught to allocate more thinking time to problems and develop better reasoning strategies - without explicit human feedback or demonstrations. This project aims to reproduce this phenomenon with the smaller SmolLM2 1.7B model, demonstrating that even smaller models can learn to "think before answering" through reinforcement learning.

We use the Countdown Game (a numbers puzzle) as our training task, and leverage GRPO, a reinforcement learning approach introduced in the [DeepSeekMath paper](https://arxiv.org/abs/2402.03300), to teach the model to:

1. Show its reasoning process inside `<think>...</think>` tags
2. Provide final solutions inside `<answer>...</answer>` tags

## ⚙️ How It Works

The training process works by:

1. Starting with the SmolLM2 1.7B model that has basic instruction following capability
2. Using GRPO to optimize the model to solve Countdown Game math puzzles
3. Designing rule-based reward functions that score both formatting and correctness
4. Training the model to maximize these rewards using reinforcement learning

The model learns not just to solve problems, but to articulate its thinking process - a capability that emerges purely from reinforcement learning without explicit demonstrations.