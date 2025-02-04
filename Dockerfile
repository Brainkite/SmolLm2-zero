# Use NVIDIA PyTorch container as base image
FROM nvcr.io/nvidia/pytorch:25.01-py3

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
# First upgrade setuptools to meet vllm requirements
RUN pip install --no-cache-dir setuptools>=74.1.1 && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

# Set default command
CMD ["python3"]
