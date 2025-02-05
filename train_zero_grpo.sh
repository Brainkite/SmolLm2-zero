# First, make sure you're logged into wandb
python -c "import torch; print('CUDA',torch.cuda.is_available())"

accelerate launch \
  --num_processes $N_GPUS \
  --config_file training/configs/accelerate_configs/deepspeed_zero3.yaml \
  training/scripts/run_r1_grpo.py \
  --config training/receipes/grpo-qwen-2.5-0.5b-deepseek-r1-countdown.yaml