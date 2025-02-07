#!/bin/bash

# First, make sure you're logged into wandb
python -c "import torch; print('CUDA',torch.cuda.is_available())"

# Count the number of GPUs and set N_GPUS
N_GPUS=$(nvidia-smi -L | wc -l)
export N_PROC=$((N_GPUS - 1))
export VLLM_CUDA_IDX=$((N_GPUS - 1))

# Create directories for autotuning results
mkdir -p autotuning_results
mkdir -p autotuning_exps

echo "Starting DeepSpeed autotuning..."

# Launch autotuning
deepspeed --autotuning tune \
    --num_nodes=1 \
    --num_gpus=$N_PROC \
    training/scripts/run_r1_grpo.py \
    --config training/receipes/grpo-qwen-2.5-0.5b-deepseek-r1-countdown.yaml \
    --deepspeed training/configs/ds_config_autotune.json

echo "Autotuning completed!"
echo "You can find the optimal configuration in: ./autotuning_results/ds_config_optimal.json"
echo "The autotuning experiment logs are in: ./autotuning_exps/" 