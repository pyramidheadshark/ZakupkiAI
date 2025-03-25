import os
from pathlib import Path
from dotenv import load_dotenv
from src.utils.helpers import load_verified_sources # Импортируем из helpers

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# !! ВАЖНО: Укажите корректный путь к скачанной модели !!
MODEL_GGUF_PATH = str(BASE_DIR.parent / "models" / "gguf_models" / "DeepSeek-R1-Distill-Qwen-7B-Q5_K_L.gguf")
EMBEDDING_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", 20))
N_BATCH = int(os.getenv("N_BATCH", 512))
N_CTX = int(os.getenv("N_CTX", 4096))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.5))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))

VERIFIED_SOURCES_FILE = str(BASE_DIR.parent / "data" / "raw" / "verified_sources.txt")
VERIFIED_DOMAINS = load_verified_sources(VERIFIED_SOURCES_FILE)
MAX_SEARCH_RESULTS = 3
MAX_PAGE_CHUNKS = 3

if not Path(MODEL_GGUF_PATH).is_file():
    print(f"!!! ВНИМАНИЕ: Файл модели не найден по пути: {MODEL_GGUF_PATH}")
    print("!!! Пожалуйста, скачайте модель и поместите ее в указанную директорию.")
