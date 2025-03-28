import logging
from typing import Optional, Dict, Any

from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage

from src.config import settings
from src.agent.models import load_llm
from src.agent.prompts import (
    DECIDE_SEARCH_PROMPT,
    GENERATE_SEARCH_QUERY_PROMPT,
    SYNTHESIZE_ANSWER_PROMPT
)
from src.agent.tools import search_and_rag_chain

logger = logging.getLogger(__name__)


_llm_instance: Optional[BaseLanguageModel] = None

def get_llm() -> BaseLanguageModel:
    """Возвращает инициализированный экземпляр LLM."""
    global _llm_instance
    if _llm_instance is None:
        logger.info("EXECUTOR: Первая инициализация LLM...")
        try:
            _llm_instance = load_llm()
            logger.info("EXECUTOR: LLM успешно инициализирована.")
        except Exception as e:
             logger.critical("EXECUTOR: КРИТИЧЕСКАЯ ОШИБКА при инициализации LLM!", exc_info=True)
             raise RuntimeError("Не удалось инициализировать LLM") from e
    return _llm_instance


def run_query_flow(query: str, session_id: str = "default_session") -> str:
    """
    Обрабатывает запрос пользователя: решает, нужен ли поиск, выполняет его (если нужен),
    и синтезирует финальный ответ с помощью LLM.
    """
    logger.info(f"EXECUTOR: Начало обработки запроса (сессия: {session_id}): '{query[:100]}...'")
    llm = get_llm()


    search_needed = False
    try:
        prompt_decide = DECIDE_SEARCH_PROMPT.format(user_query=query)
        logger.debug(f"EXECUTOR: Запрос к LLM для решения о поиске:\n{prompt_decide}")

        llm_response_decide = llm.invoke(prompt_decide)
        logger.debug(f"EXECUTOR: Ответ LLM (решение): {llm_response_decide}")

        if isinstance(llm_response_decide, AIMessage):
            decision_str = llm_response_decide.content.strip().upper()
        elif isinstance(llm_response_decide, str):
             decision_str = llm_response_decide.strip().upper()
        else:
             logger.warning(f"EXECUTOR: Неожиданный тип ответа LLM (решение): {type(llm_response_decide)}")
             decision_str = ""

        logger.info(f"EXECUTOR: Решение LLM о поиске (обработано): '{decision_str}'")
        if "YES" in decision_str:
            search_needed = True
    except Exception as e:
        logger.error(f"EXECUTOR: Ошибка на шаге решения о поиске: {e}", exc_info=True)
        search_needed = True
        logger.warning("EXECUTOR: Не удалось получить решение LLM о поиске, предполагаем, что поиск нужен.")


    search_results_context = "Поиск не проводился, так как был оценен как ненужный для данного запроса."
    if search_needed:
        try:
            prompt_generate_query = GENERATE_SEARCH_QUERY_PROMPT.format(user_query=query)
            logger.debug(f"EXECUTOR: Запрос к LLM для генерации поискового запроса:\n{prompt_generate_query}")

            llm_response_gen_query = llm.invoke(prompt_generate_query)
            logger.debug(f"EXECUTOR: Ответ LLM (генерация запроса): {llm_response_gen_query}")
            if isinstance(llm_response_gen_query, AIMessage):
                 search_query = llm_response_gen_query.content.strip().strip('"\'')
            elif isinstance(llm_response_gen_query, str):
                 search_query = llm_response_gen_query.strip().strip('"\'')
            else:
                 logger.warning(f"EXECUTOR: Неожиданный тип ответа LLM (генерация запроса): {type(llm_response_gen_query)}")
                 search_query = ""

            logger.info(f"EXECUTOR: Сгенерированный поисковый запрос: '{search_query}'")

            if not search_query:
                 logger.warning("EXECUTOR: LLM сгенерировала пустой поисковый запрос.")
                 search_results_context = "Не удалось сгенерировать поисковый запрос."
            else:
                logger.debug(f"EXECUTOR: Вызов цепочки search_and_rag_chain с запросом: '{search_query}'")
                search_results_context = search_and_rag_chain.invoke(search_query)
                logger.info("EXECUTOR: Цепочка search_and_rag_chain успешно выполнена.")
                logger.debug(f"EXECUTOR: Полученные результаты поиска/RAG (для контекста):\n{str(search_results_context)[:500]}...")

        except Exception as e:
            logger.error(f"EXECUTOR: Ошибка на шаге генерации запроса или выполнения поиска: {e}", exc_info=True)
            search_results_context = f"Произошла ошибка при попытке поиска информации: {e}"


    try:
        prompt_synthesize = SYNTHESIZE_ANSWER_PROMPT.format(
            user_query=query,
            search_results_context=search_results_context
        )
        logger.debug(f"EXECUTOR: Запрос к LLM для синтеза финального ответа (контекст ~{len(str(search_results_context))} симв.).")
        logger.debug(f"EXECUTOR: Начало промпта синтеза:\n{prompt_synthesize[:1000]}...")


        llm_response_final = llm.invoke(prompt_synthesize)
        logger.debug(f"EXECUTOR: Ответ LLM (синтез): {llm_response_final}")
        if isinstance(llm_response_final, AIMessage):
             final_answer = llm_response_final.content.strip()
        elif isinstance(llm_response_final, str):
             final_answer = llm_response_final.strip()
        else:
             logger.error(f"EXECUTOR: Неожиданный тип ответа LLM (синтез): {type(llm_response_final)}")
             final_answer = "Ошибка: Не удалось получить финальный ответ от языковой модели."


        logger.info("EXECUTOR: Финальный ответ успешно сгенерирован.")
        logger.debug(f"EXECUTOR: Сгенерированный финальный ответ:\n{final_answer[:500]}...")
        return final_answer

    except Exception as e:
        logger.error(f"EXECUTOR: Ошибка на шаге синтеза финального ответа: {e}", exc_info=True)
        return f"Произошла ошибка при генерации финального ответа: {e}"


def run_agent(query: str, session_id: str = "default_session") -> str:
    """Точка входа для Streamlit, вызывает run_query_flow."""
    try:
        return run_query_flow(query, session_id)
    except Exception as e:
        logger.critical(f"EXECUTOR: Необработанная ошибка в run_agent: {e}", exc_info=True)
        return f"Критическая внутренняя ошибка: {e}"


def initialize_flow():
    """Загружает LLM для подготовки к работе."""
    try:
        get_llm()
        return True, None
    except Exception as e:
        error_msg = f"Ошибка при инициализации LLM: {e}"
        logger.critical(f"EXECUTOR/INIT: {error_msg}", exc_info=True)
        return False, error_msg