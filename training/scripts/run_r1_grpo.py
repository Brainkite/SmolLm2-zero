import logging
import os
from dataclasses import dataclass
from datetime import datetime
import logging
import os

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
import random
import re
import torch
from transformers.trainer_utils import get_last_checkpoint
from transformers import AutoTokenizer, TrainerCallback
from datasets import load_dataset
from trl import GRPOConfig, GRPOTrainer, get_peft_config, ModelConfig, TrlParser
import wandb


########################
# Custom dataclasses
########################
@dataclass
class ScriptArguments:
    dataset_id_or_path: str = "Jiayi-Pan/Countdown-Tasks-3to4"
    dataset_splits: str = "train"
    tokenizer_name_or_path: str = None
    wandb_project: str = "countdown-math"
    wandb_name: str = None


########################
# Setup logging
########################
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)

########################
# Helper functions
########################


def format_reward_func(completions, target, **kwargs):
    """
    Format: <think>...</think><answer>...</answer>
    Args:
        completions (list[str]): Generated outputs
        target (list[str]): Expected answers

      Returns:
          list[float]: Reward scores
    """
    rewards = []

    for completion, gt in zip(completions, target):

        try:
            # add synthetic <think> as its already part of the prompt and prefilled for the assistant to more easily match the regex
            completion = "<think>" + completion
            if random.random() < 0.1:  # 1% chance to write samples into a file
                os.makedirs("completion_samples", exist_ok=True)
                log_file = os.path.join("completion_samples", "completion_samples.txt")
                with open(log_file, "a") as f:
                    f.write(f"\n\n==============\n")
                    f.write(completion)

            # Check if the format is correct
            regex = r"^<think>([^<]*(?:<(?!/?think>)[^<]*)*)<\/think>\n<answer>([\s\S]*?)<\/answer>$"

            match = re.search(regex, completion, re.DOTALL)
            # if the format is not correct, reward is 0
            if match is None or len(match.groups()) != 2:
                rewards.append(0.0)
            else:
                rewards.append(1.0)
        except Exception:
            rewards.append(0.0)
    return rewards


def equation_reward_func(completions, target, nums, **kwargs):
    """
    Evaluates completions based on:
    2. Mathematical correctness of the answer

    Args:
        completions (list[str]): Generated outputs
        target (list[str]): Expected answers
        nums (list[str]): Available numbers

    Returns:
        list[float]: Reward scores
    """
    rewards = []
    for completion, gt, numbers in zip(completions, target, nums):
        try:
            # add synthetic <think> as its already part of the prompt and prefilled for the assistant to more easily match the regex
            completion = "<think>" + completion
            # Check if the format is correct
            match = re.search(r"<answer>(.*?)<\/answer>", completion)
            if match is None:
                rewards.append(0.0)
                continue
            # Extract the "answer" part from the completion
            equation = match.group(1).strip()
            # Extract all numbers from the equation
            used_numbers = [int(n) for n in re.findall(r"\d+", equation)]

            # Check if all numbers are used exactly once
            if sorted(used_numbers) != sorted(numbers):
                rewards.append(0.0)
                continue
            # Define a regex pattern that only allows numbers, operators, parentheses, and whitespace
            allowed_pattern = r"^[\d+\-*/().\s]+$"
            if not re.match(allowed_pattern, equation):
                rewards.append(0.0)
                continue

            # Evaluate the equation with restricted globals and locals
            result = eval(equation, {"__builtins__": None}, {})
            # Check if the equation is correct and matches the ground truth
            if abs(float(result) - float(gt)) < 1e-5:
                rewards.append(1.0)
                if (
                    random.random() < 0.10
                ):  # 10% chance to write fully successful samples into a file
                    os.makedirs("completion_samples", exist_ok=True)
                    log_file = os.path.join(
                        "completion_samples", "success_completion_samples.txt"
                    )
                    with open(log_file, "a") as f:
                        f.write(f"\n\n==============\n")
                        f.write(completion)
            else:
                rewards.append(0.0)
        except Exception:
            # If evaluation fails, reward is 0
            rewards.append(0.0)
    return rewards


def get_checkpoint(training_args: GRPOConfig):
    last_checkpoint = None
    if os.path.isdir(training_args.output_dir):
        last_checkpoint = get_last_checkpoint(training_args.output_dir)
    return last_checkpoint

class MemoryProfileCallback(TrainerCallback):
    def on_step_end(self, args, state, control, **kwargs):
        # Dump a memory profile every 10 steps
        if True: # state.global_step % 10 == 0:
            if torch.cuda.is_available():
                rank_suffix = f"_{torch.distributed.get_rank()}" if torch.distributed.is_initialized() else ""
                profile_filename = f"profile_step_{state.global_step}{rank_suffix}.pkl"
                torch.cuda.memory._dump_snapshot(profile_filename)
                logger.info(f"[MemoryProfileCallback] Memory profile saved to {profile_filename}")
        return control

def grpo_function(
    model_args: ModelConfig, script_args: ScriptArguments, training_args: GRPOConfig
):
    # Check if we're on main process using torch.distributed
    if torch.distributed.is_initialized():
        is_main = torch.distributed.get_rank() == 0
    else:
        is_main = True

    # --- Added GPU Memory Profiling Start ---
    if torch.cuda.is_available():
        torch.cuda.memory._record_memory_history(max_entries=100000)
        logger.info("Started GPU memory profiling")
    # --- End Added GPU Memory Profiling Start ---

    # Initialize wandb only on the main process
    if is_main:
        wandb.init(
            project=script_args.wandb_project,
            name=script_args.wandb_name,
            config={
                "model_name": model_args.model_name_or_path,
                "learning_rate": training_args.learning_rate,
                "batch_size": training_args.per_device_train_batch_size,
                "max_steps": training_args.max_steps,
                "beta": training_args.beta,
            },
        )

    #########################
    # Log parameters
    #########################
    logger.info(f"Model parameters {model_args}")
    logger.info(f"Training/evaluation parameters {training_args}")

    ################
    # Load tokenizer
    ################
    tokenizer = AutoTokenizer.from_pretrained(
        (
            script_args.tokenizer_name_or_path
            if script_args.tokenizer_name_or_path
            else model_args.model_name_or_path
        ),
        revision=model_args.model_revision,
        trust_remote_code=model_args.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    ###############
    # Load datasets
    ###############
    # Load dataset from Hugging Face Hub
    dataset = load_dataset(
        script_args.dataset_id_or_path, split=script_args.dataset_splits
    )
    # select a random subset of 50k samples
    dataset = dataset.shuffle(seed=42).select(range(50000))

    #####################
    # Prepare and format dataset
    #####################

    # gemerate r1 prompt with a prefix for the model to already start with the thinking process
    def generate_r1_prompt(numbers, target):
        r1_prefix = [
            {
                "role": "system",
                "content": "You are a helpful assistant. You first thinks about the reasoning process in your mind and then provides the user with the answer.",
            },
            {
                "role": "user",
                "content": f"Using the numbers {numbers}, create an equation that equals {target}. You can use basic arithmetic operations (+, -, *, /) one or multiple times but each number can only be used once. Show your work in <think> </think> tags. And return the final equation in <answer> </answer> tags, for example <answer> (1 + 2) / 3 </answer>. Think step by step inside <think> tags.",
            },
            {
                "role": "assistant",
                "content": "Let me solve this step by step.\n<think>",
            },
        ]
        return {
            "prompt": tokenizer.apply_chat_template(
                r1_prefix, tokenize=False, continue_final_message=True
            ),
            "target": target,
            "nums": numbers,
        }

    # convert our dataset to the r1 prompt
    dataset = dataset.map(lambda x: generate_r1_prompt(x["nums"], x["target"]))

    # split the dataset into train and test
    train_test_split = dataset.train_test_split(test_size=0.1)

    train_dataset = train_test_split["train"]
    test_dataset = train_test_split["test"]

    #########################
    # Instantiate DPO trainer
    #########################
    trainer = GRPOTrainer(
        model=model_args.model_name_or_path,
        reward_funcs=[format_reward_func, equation_reward_func],
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=test_dataset,
        peft_config=get_peft_config(model_args),
    )
    # --- Added Memory Profiling Callback: dump GPU memory profile every 10 steps ---
    trainer.callback_handler.add_callback(MemoryProfileCallback())

    ###############
    # Training loop
    ###############
    # Check for last checkpoint
    last_checkpoint = get_checkpoint(training_args)
    if last_checkpoint is not None and training_args.resume_from_checkpoint is None:
        logger.info(f"Checkpoint detected, resuming training at {last_checkpoint}.")

    # Train the model
    logger.info(
        f'*** Starting training {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} for {training_args.num_train_epochs} epochs***'
    )
    train_result = trainer.train(resume_from_checkpoint=last_checkpoint)

    # --- Added GPU Memory Profiling Dump ---
    if torch.cuda.is_available():
        # In distributed training, get the process rank to suffix the filename
        rank_suffix = f"_{torch.distributed.get_rank()}" if torch.distributed.is_initialized() else ""
        profile_filename = f"profile{rank_suffix}.pkl"
        torch.cuda.memory._dump_snapshot(profile_filename)
        torch.cuda.memory._record_memory_history(enabled=None)
        logger.info(f"Memory profile saved to {profile_filename}")
    # --- End Added GPU Memory Profiling Dump ---

    # Log and save metrics
    metrics = train_result.metrics
    metrics["train_samples"] = len(train_dataset)
    trainer.log_metrics("train", metrics)
    trainer.save_metrics("train", metrics)
    trainer.save_state()

    # Use is_main for the final wandb cleanup
    if is_main:
        wandb.finish()

    logger.info("*** Training complete ***")

    ##################################
    # Save model and create model card
    ##################################

    logger.info("*** Save model ***")
    trainer.model.config.use_cache = True
    trainer.save_model(training_args.output_dir)
    logger.info(f"Model saved to {training_args.output_dir}")
    training_args.distributed_state.wait_for_everyone()

    tokenizer.save_pretrained(training_args.output_dir)
    logger.info(f"Tokenizer saved to {training_args.output_dir}")

    # Save everything else on main process
    if is_main:
        trainer.create_model_card({"tags": ["rl", "grpo", "tutorial", "philschmid"]})
    # push to hub if needed
    if training_args.push_to_hub is True:
        logger.info("Pushing to hub...")
        trainer.push_to_hub()

    logger.info("*** Training complete! ***")

    # Dump the memory snapshot after training
    if is_main:
        torch.cuda.memory.snapshot()
        torch.cuda.memory.dump()


def main():
    parser = TrlParser((ModelConfig, ScriptArguments, GRPOConfig))
    model_args, script_args, training_args = parser.parse_args_and_config()

    # Run the main training loop
    grpo_function(model_args, script_args, training_args)


if __name__ == "__main__":
    main()

