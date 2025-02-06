# First, make sure you're logged into wandb
python -c "import torch; print('CUDA',torch.cuda.is_available())"

# Count the number of GPUs and set N_GPUS
N_GPUS=$(nvidia-smi -L | wc -l)
export N_PROC=$((N_GPUS - 1))
export VLLM_CUDA_IDX=$((N_GPUS - 1))

accelerate launch \
  --num_processes 1 \
  --config_file training/configs/accelerate_configs/deepspeed_zero3.yaml \
  training/scripts/run_r1_grpo.py \
  --config training/receipes/grpo-qwen-2.5-3b-deepseek-r1-countdown.yaml

rm -rf runs
rm -rf wandb