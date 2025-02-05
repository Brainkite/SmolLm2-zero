import os
import json
from datasets import load_dataset
from transformers import AutoTokenizer

def download_and_prepare_dataset():
    # Create dataset directory if it doesn't exist
    os.makedirs("/workspace/dataset", exist_ok=True)
    
    # Load the dataset
    dataset = load_dataset("antonin-sumner/countdown-math")
    
    # Load tokenizer for preprocessing if needed
    tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
    
    # Save dataset splits
    for split in dataset.keys():
        output_file = f"/workspace/dataset/countdown_math_{split}.jsonl"
        
        print(f"Saving {split} split to {output_file}")
        with open(output_file, 'w') as f:
            for item in dataset[split]:
                f.write(json.dumps(item) + '\n')
    
    print("Dataset preparation completed!")
    print(f"Dataset statistics:")
    for split in dataset.keys():
        print(f"{split}: {len(dataset[split])} examples")

if __name__ == "__main__":
    download_and_prepare_dataset() 