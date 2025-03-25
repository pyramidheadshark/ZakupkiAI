from langchain_community.llms import LlamaCpp
from src.config import (
    MODEL_GGUF_PATH,
    N_GPU_LAYERS,
    N_BATCH,
    N_CTX,
    TEMPERATURE,
    MAX_TOKENS
)
import logging

logger = logging.getLogger(__name__)

def load_llm() -> LlamaCpp:
    """Загружает локальную LLM с использованием LlamaCpp."""
    try:
        logger.info(f"Загрузка LLM из: {MODEL_GGUF_PATH}")
        logger.info(f"Параметры LlamaCpp: n_gpu_layers={N_GPU_LAYERS}, n_batch={N_BATCH}, n_ctx={N_CTX}")
        llm = LlamaCpp(
            model_path=MODEL_GGUF_PATH,
            n_gpu_layers=N_GPU_LAYERS,
            n_batch=N_BATCH,
            n_ctx=N_CTX,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            verbose=False,
            streaming=True,
        )
        logger.info("LLM успешно загружена.")
        return llm
    except Exception as e:
        logger.error(f"Ошибка при загрузке LLM", exc_info=True)
        raise e

llm = load_llm()