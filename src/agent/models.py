import logging
from functools import lru_cache
from pathlib import Path
from typing import Union, Optional

from langchain_community.llms import LlamaCpp
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from pydantic import SecretStr

from src.config import settings
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def load_llm() -> Union[BaseLanguageModel, BaseChatModel]:
    """Загружает LLM или ChatModel в зависимости от провайдера в настройках."""
    if not settings:
        raise ValueError("Настройки не инициализированы!")

    provider = settings.llm_provider
    logger.info(f"Загрузка LLM/ChatModel для провайдера: {provider}")

    if provider == "local":

        model_path_str = settings.local_llm.model_gguf_path
        if not model_path_str or not Path(model_path_str).is_file():
            logger.error(f"Файл локальной модели LLM не найден: {model_path_str}")
            raise FileNotFoundError(f"Модель LLM не найдена по пути: {model_path_str}")
        model_path = Path(model_path_str)
        try:
            logger.info(f"Загрузка LlamaCpp LLM из: {model_path}")
            logger.info(f"Параметры LlamaCpp: n_gpu_layers={settings.local_llm.n_gpu_layers}, ...")
            llm = LlamaCpp(
                model_path=str(model_path),
                n_gpu_layers=settings.local_llm.n_gpu_layers,
                n_batch=settings.local_llm.n_batch,
                n_ctx=settings.local_llm.n_ctx,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens,
                verbose=settings.llm_verbose,
                streaming=False,
            )
            logger.info("LlamaCpp LLM успешно загружена.")
            return llm
        except Exception as e:
            logger.error("Ошибка при загрузке LlamaCpp LLM", exc_info=True)
            raise e

    elif provider == "gemini":

        api_key_obj = settings.gemini_llm.google_api_key


        api_key_str: Optional[str] = None
        if isinstance(api_key_obj, SecretStr):
            api_key_str = api_key_obj.get_secret_value()
            logger.debug("Извлечено значение google_api_key из SecretStr.")
        elif isinstance(api_key_obj, str):
            api_key_str = api_key_obj
            logger.warning("google_api_key прочитан как строка (str), а не SecretStr. Используем как есть.")
        elif api_key_obj is None:
            logger.error("Ключ Google API (GOOGLE_API_KEY) не найден в настройках.")

        else:

            logger.error(f"Неожиданный тип для google_api_key: {type(api_key_obj)}. Не могу извлечь значение.")


        if not api_key_str:
            raise ValueError("Ключ Google API не задан или не удалось извлечь его значение для провайдера gemini.")

        try:
            logger.info(f"Инициализация ChatGoogleGenerativeAI (из langchain-google-genai)...")
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_llm.gemini_model_name,
                google_api_key=api_key_str,
                temperature=settings.temperature,
                generation_config={"max_output_tokens": settings.max_tokens},
                convert_system_message_to_human=True
            )

            logger.debug("Выполняется пробный вызов ChatGoogleGenerativeAI...")
            _ = llm.invoke([HumanMessage(content="test")])
            logger.info(f"Google ChatGoogleGenerativeAI ({settings.gemini_llm.gemini_model_name}) успешно инициализирован.")
            return llm
        except ImportError:
             logger.error("Ошибка: langchain-google-genai не установлен...")
             raise
        except Exception as e:
            logger.error(f"Ошибка при инициализации/вызове Google ChatGoogleGenerativeAI: {e}", exc_info=True)
            raise e
    else:
        raise ValueError(f"Неизвестный LLM провайдер: {provider}")



@lru_cache(maxsize=1)
def load_embedding_model() -> HuggingFaceEmbeddings:
    """Загружает модель эмбеддингов."""
    if not settings:
        raise ValueError("Настройки не инициализированы!")
    model_name = settings.embeddings.embedding_model_name
    device = settings.embeddings.embedding_device
    logger.info(f"Загрузка модели эмбеддингов: '{model_name}' на устройство: '{device}'")
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        _ = embeddings.embed_query("test")
        logger.info(f"Модель эмбеддингов '{model_name}' успешно загружена на устройство '{device}'.")
        return embeddings
    except Exception as e:
        logger.error(f"Ошибка при загрузке модели эмбеддингов ('{model_name}' на '{device}')!", exc_info=True)
        raise e


try:

    llm_instance = load_llm()

    embedding_instance = load_embedding_model()
except Exception as init_error:
     logger.critical(f"КРИТИЧЕСКАЯ ОШИБКА при загрузке моделей: {init_error}", exc_info=True)
     llm_instance = None
     embedding_instance = None

__all__ = ["llm_instance", "embedding_instance", "load_llm", "load_embedding_model"]