#!/bin/bash

echo "Starting setup script..."

# Update system packages
echo "Updating system packages..."
apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --no-cache-dir setuptools>=74.1.1

# Remove and reinstall specific NVIDIA packages
echo "Setting up NVIDIA packages..."
pip uninstall -y pynvml
pip install --no-cache-dir nvidia-ml-py

# Install flash-attention
echo "Installing flash-attention..."
pip uninstall -y flash-attn
pip install flash-attn --no-build-isolation

# Install other Python packages
echo "Installing ML frameworks and tools..."
pip install --no-cache-dir \
    tensorboard \
    transformers==4.48.1 \
    datasets==3.1.0 \
    accelerate==1.3.0 \
    hf-transfer==0.1.9 \
    deepspeed==0.15.4 \
    trl==0.14.0 \
    vllm==0.7.0 \
    wandb

echo "Setup completed successfully!" 