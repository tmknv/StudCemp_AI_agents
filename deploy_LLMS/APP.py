from fastapi import FastAPI, Request
from llama_cpp import Llama
from scripts.classes import PromptInput
from contextlib import asynccontextmanager
import logging 

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("⏳ Загружаем модель...")
    app.state.model = Llama(
        model_path="models/mistral-7b-instruct-v0.1.Q4_K_M.gguf",
        n_ctx=4096,
        n_threads=8,  # 8 потоки
        n_gpu_layers=0, #0 тк тока цпу 
        seed=42,
        verbose=False
    )
    logger.info("✅ Модель загружена!")
    yield
    logger.info("🛑 Освобождаем ресурсы...")
    del app.state.model

app = FastAPI(lifespan=lifespan)

@app.post("/api/generate")
async def generate_text(data: PromptInput, request: Request):
    model: Llama = request.app.state.model

    full_prompt = f"{data.system_prompt}\n{data.prompt}"
    output = model(
        prompt=full_prompt,
        max_tokens=data.max_tokens,
        temperature=data.temperature,
        top_p=data.top_p,
        echo=False,
    )
    return {
        "output": output["choices"][0]["text"].strip()
    }
