FROM nvidia/cuda:12.1.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive


RUN apt update && apt install -y \
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-dev \
    cmake \
    wget \
    curl \
    libopenblas-dev

# директория
WORKDIR /deploy_LLMS

# Копируем код
COPY . /deploy_LLMS

RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn \
    Cython

# Установка llama-cpp-python с поддержкой cuBLAS
RUN pip3 install llama-cpp-python --no-cache-dir

# Качаем модель
RUN mkdir -p models && \
    wget -O models/mistral-7b-instruct-v0.1.Q4_K_M.gguf \
    https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf


CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9090"]
