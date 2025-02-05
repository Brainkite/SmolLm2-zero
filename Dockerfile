# Use NVIDIA PyTorch container as base image
FROM nvcr.io/nvidia/pytorch:25.01-py3

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir setuptools>=74.1.1 && \
    pip uninstall -y pynvml && \
    pip install --no-cache-dir nvidia-ml-py && \
    # Uninstall any existing flash-attn
    pip uninstall -y flash-attn && \
    # Install flash-attn with specific CUDA architectures
    FLASH_ATTENTION_FORCE_BUILD=TRUE pip install --no-cache-dir flash-attn==2.5.5 --no-build-isolation && \
    # Install other dependencies
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

# Set default command
CMD ["python3"]
