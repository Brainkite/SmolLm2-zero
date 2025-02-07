# Stage 1: Builder
FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 as builder

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.10
ENV PATH=/opt/conda/bin:$PATH
ENV PDSH_RCMD_TYPE=ssh

# Install basic build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    git \
    pdsh \
    build-essential \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-venv \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python${PYTHON_VERSION} -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

# Install Python dependencies
RUN python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -U pip setuptools<71.0.0 wheel && \
    pip install --no-cache-dir \
    torch==2.5.1 \
    --index-url https://download.pytorch.org/whl/cu121 && \
    pip install --no-cache-dir \
    tensorboard \
    transformers==4.48.1 \
    datasets==3.1.0 \
    accelerate==1.3.0 \
    hf-transfer==0.1.9 \
    deepspeed==0.15.4 \
    trl==0.14.0 \
    vllm==0.7.0 \
    wandb && \
    pip uninstall -y pynvml flash-attn && \
    pip install --no-cache-dir nvidia-ml-py flash-attn --no-build-isolation

# Stage 2: Runtime
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHON_VERSION=3.10
ENV PATH=/opt/venv/bin:$PATH
ENV CUDA_HOME="/usr/local/cuda"
ENV PDSH_RCMD_TYPE=ssh

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    git \
    pdsh \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Configure pdsh
RUN echo "ssh" > /etc/pdsh/rcmd_default

# Set working directory
WORKDIR /workspace

# Command
CMD ["python3"]