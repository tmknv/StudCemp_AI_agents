FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
    build-essential \
    git \
    cmake \
    wget \
    curl \
    libopenblas-dev \
    python3-dev


COPY ./deploy_LLMS /deploy_LLMS

WORKDIR /deploy_LLMS


RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir \
    fastapi \
    uvicorn \
    Cython

# llama-cpp-python для CPU
RUN pip3 install llama-cpp-python --no-cache-dir

# Качаем модель
RUN mkdir -p models && \
    wget -O models/mistral-7b-instruct-v0.1.Q4_K_M.gguf \
    https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf


CMD uvicorn APP:app --reload --port 9090 --host 0.0.0.0