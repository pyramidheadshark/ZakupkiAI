import logging
import os
from pathlib import Path
from typing import Literal, Optional

# Явно импортируем load_dotenv
from dotenv import load_dotenv
from pydantic import Field, ValidationError, field_validator, SecretStr 
from pydantic_settings import BaseSettings, SettingsConfigDict

# Определяем корневую директорию проекта
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# --- Загрузка .env ---
dotenv_path = PROJECT_ROOT / '.env'
# Загружаем .env ЯВНО перед инициализацией Pydantic
load_status = load_dotenv(dotenv_path=dotenv_path, override=True, verbose=False) # Убираем verbose
# Можно добавить лог статуса загрузки, если нужно
# logging.info(f"Статус загрузки .env: {load_status}")


# --- Модели Настроек (Pydantic) ---

class LocalLLMSettings(BaseSettings):
    """Настройки для локальной LLM (LlamaCpp)."""
    model_gguf_path: Optional[str] = Field(
        default=str(PROJECT_ROOT / "models" / "gguf_models" / "placeholder.gguf"),
        description="Путь к файлу модели GGUF"
    )
    n_gpu_layers: int = Field(default=0, description="Кол-во слоев на GPU (-1 = все)")
    n_batch: int = Field(default=512, description="Размер батча для промпта")
    n_ctx: int = Field(default=4096, description="Размер контекста LLM")

    @field_validator('model_gguf_path')
    def check_model_path(cls, v, info): # Добавлен info для Pydantic v2
        values = info.data # Получаем уже загруженные значения
        provider = values.get('llm_provider')
        if provider == 'local' and v and not Path(v).is_file():
            # Используем logging, который будет настроен позже
            logging.error(f"Локальная модель LLM не найдена: {v}")
        elif provider == 'local' and not v:
             logging.warning("Выбран локальный провайдер, но путь к модели не указан (model_gguf_path).")
        return v

class GeminiLLMSettings(BaseSettings):
    """Настройки для Gemini API."""
    google_api_key: str = Field(..., description="API ключ Google AI") # Обязательное поле
    gemini_model_name: str = Field("gemini-1.5-flash-latest", description="Имя модели Gemini")

class EmbeddingSettings(BaseSettings):
    """Настройки модели эмбеддингов."""
    embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"
    
class TavilySettings(BaseSettings):
    tavily_api_key: Optional[SecretStr] = Field(default=None, description="API ключ Tavily Search") # Используем SecretStr

class ToolSettings(BaseSettings):
    """Настройки инструментов агента."""
    verified_sources_file: str = str(PROJECT_ROOT / "data" / "raw" / "verified_sources.txt")
    max_search_results: int = 7
    max_page_chunks: int = 3
    web_loader_timeout: int = 15

class AgentSettings(BaseSettings):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    llm_provider: Literal["local", "gemini"] = "local"
    temperature: float = 0.6
    max_tokens: int = 1536
    llm_verbose: bool = False
    agent_verbose: bool = True # Оставим для отладки executor если понадобится

    local_llm: LocalLLMSettings = LocalLLMSettings()
    gemini_llm: GeminiLLMSettings = GeminiLLMSettings()
    tavily: TavilySettings = TavilySettings() # <--- ДОБАВЛЕНО
    embeddings: EmbeddingSettings = EmbeddingSettings()
    tools: ToolSettings = ToolSettings()

    model_config = SettingsConfigDict(
        env_nested_delimiter='__',
        extra='ignore',
        # Загрузка переменных окружения с префиксом APP_ или без него
        # env_prefix='APP_', # Если ваши переменные имеют префикс
    )

    # Валидаторы для ключей API
    @field_validator('gemini_llm')
    def check_gemini_key_if_provider_is_gemini(cls, v, info):
        values = info.data
        provider = values.get('llm_provider')
        if provider == 'gemini' and (not v or not v.google_api_key):
             raise ValueError("Выбран провайдер 'gemini', но GOOGLE_API_KEY отсутствует или пуст.")
        return v

    # Валидатор для Tavily (просто проверка наличия, т.к. он не зависит от провайдера LLM)
    @field_validator('tavily')
    def check_tavily_key(cls, v):
        if not v or not v.tavily_api_key:
            # Выдаем предупреждение, а не ошибку, т.к. поиск может быть не всегда нужен
            logging.warning("TAVILY_API_KEY не найден в окружении или .env файле. Поиск Tavily будет недоступен.")
        return v


# --- Инициализация Конфигурации и Логирования ---
settings: Optional[AgentSettings] = None
VERIFIED_DOMAINS: list = []
# Настраиваем базовое логирование ДО загрузки настроек
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__) # Получаем логгер

try:
    # Инициализируем настройки Pydantic
    settings = AgentSettings()

    # Перенастраиваем уровень логирования на основе загруженных настроек
    log_level_numeric = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level_numeric) # Устанавливаем уровень для корневого логгера
    # Понижаем уровень внешних библиотек
    for lib_logger in ["httpx", "httpcore", "google.api_core", "google.auth", "urllib3", "chardet", "primp", "langchain_community.utils.user_agent"]:
        logging.getLogger(lib_logger).setLevel(logging.WARNING)

    logger.info(f"Конфигурация Pydantic успешно инициализирована. Уровень логирования: {settings.log_level}")
    logger.info(f"Выбранный LLM провайдер: {settings.llm_provider}")

    if settings.tavily and settings.tavily.tavily_api_key:
         logger.info(f"Ключ Tavily API: Загружен (последние 4 символа: ***{settings.tavily.tavily_api_key.get_secret_value()[-4:]})")
    else:
         logger.warning("Ключ Tavily API: НЕ ЗАГРУЖЕН!")

    # Логирование специфичных настроек
    if settings.llm_provider == 'local':
        logger.info(f"Путь к локальной модели: {settings.local_llm.model_gguf_path or 'Не указан'}")
        if not settings.local_llm.model_gguf_path or not Path(settings.local_llm.model_gguf_path).is_file():
             logger.warning("Файл локальной модели не найден или путь не указан!")
    elif settings.llm_provider == 'gemini':
        logger.info(f"Используемая модель Gemini: {settings.gemini_llm.gemini_model_name}")
        logger.info(f"Ключ Google API: {'***' + settings.gemini_llm.google_api_key[-4:] if settings.gemini_llm.google_api_key else 'ОТСУТСТВУЕТ!'}")

    # Загрузка доверенных источников
    try:
        # ИСПОЛЬЗУЕМ АБСОЛЮТНЫЙ ИМПОРТ
        from src.utils.helpers import load_verified_sources
        VERIFIED_DOMAINS = load_verified_sources(settings.tools.verified_sources_file)
        logger.info(f"Доверенные домены ({len(VERIFIED_DOMAINS)}) успешно загружены.")
    except ImportError as ie:
         logger.error(f"Ошибка импорта load_verified_sources ИЗ config.py: {ie}. Проверьте структуру проекта и __init__.py.", exc_info=True)
         VERIFIED_DOMAINS = []
    except Exception as e_sources:
         logger.error(f"Ошибка при загрузке доверенных источников: {e_sources}", exc_info=True)
         VERIFIED_DOMAINS = []


except ValidationError as e:
    logger.error("КРИТИЧЕСКАЯ ОШИБКА валидации конфигурации Pydantic!", exc_info=True)
    settings = None
except Exception as e_conf:
     logger.error(f"КРИТИЧЕСКАЯ НЕОЖИДАННАЯ ОШИБКА при инициализации конфигурации: {e_conf}", exc_info=True)
     settings = None

# Экспортируем объект настроек и домены
__all__ = ["settings", "VERIFIED_DOMAINS", "PROJECT_ROOT"]