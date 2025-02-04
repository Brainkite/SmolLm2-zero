# First, make sure you're logged into wandb
wandb login

accelerate launch \
  --num_processes $N_GPUS \
  --config_file configs/accelerate_configs/deepspeed_zero3.yaml \
  scripts/run_r1_grpo.py \
  --config receipes/grpo-qwen-2.5-0.5b-deepseek-r1-countdown.yaml