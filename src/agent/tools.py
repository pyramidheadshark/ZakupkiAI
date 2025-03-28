import re
import logging
from typing import List, Dict, Any, Optional, Union
import json
import requests

from tavily import TavilyClient


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_community.document_transformers import BeautifulSoupTransformer


from src.config import settings, VERIFIED_DOMAINS

from src.agent.models import load_embedding_model

from src.utils.helpers import get_domain_from_url

logger = logging.getLogger(__name__)


tavily_client: Optional[TavilyClient] = None
tavily_api_key_present = settings and settings.tavily and settings.tavily.tavily_api_key and settings.tavily.tavily_api_key.get_secret_value()

if tavily_api_key_present:
    try:

        tavily_client = TavilyClient(api_key=settings.tavily.tavily_api_key.get_secret_value())
        logger.info("Клиент TavilyClient успешно инициализирован.")
    except ImportError:
         logger.error("Библиотека tavily-python не установлена, хотя ключ API есть. Поиск будет недоступен.")
         tavily_client = None
    except Exception as e:
         logger.error(f"Ошибка инициализации TavilyClient: {e}", exc_info=True)
         tavily_client = None
else:
    logger.warning("Ключ TAVILY_API_KEY не найден. Поиск Tavily недоступен.")




def run_tavily_search(query: str) -> Union[List[Dict[str, Any]], str]:
    """
    Запускает поиск Tavily НАПРЯМУЮ через КЛИЕНТ.
    Использует 'advanced' поиск.
    Возвращает список словарей с результатами или строку с ошибкой/сообщением.
    """
    logger.debug(f"TOOL: Вызов run_tavily_search с запросом: '{query}'")
    if tavily_client:
        try:
            max_results_to_fetch = settings.tools.max_search_results
            search_depth = "advanced"
            logger.debug(f"TOOL: Запрос к Tavily API с max_results={max_results_to_fetch}, search_depth='{search_depth}'")

            search_params = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results_to_fetch,
                "include_answer": False,
                "include_raw_content": False,
                "include_images": False,
            }
            try:
                payload_str = json.dumps(search_params, ensure_ascii=False, indent=2)
                logger.debug(f"TOOL: Параметры для Tavily API:\n{payload_str}")
            except TypeError:
                 logger.error(f"TOOL: Не удалось сериализовать параметры для лога: {search_params}")

            results_data = tavily_client.search(**search_params)

            if "results" in results_data and results_data["results"]:
                extracted_results = [
                    {"url": r.get("url"), "content": r.get("content")}
                    for r in results_data["results"]
                    if r.get("url")
                ]
                if not extracted_results:
                     logger.warning("TOOL: Tavily API вернул результаты, но без URL.")
                     return "Поиск Tavily не дал результатов с URL."

                logger.info(f"TOOL: Tavily API вернул {len(extracted_results)} результатов с URL.")
                raw_urls_found = [res.get("url", "N/A") for res in extracted_results]
                logger.info(f"TOOL: Найденные URL от Tavily: {raw_urls_found}")
                logger.debug(f"TOOL: Пример первого результата Tavily: {str(extracted_results[0])[:200]}...")
                return extracted_results
            else:
                logger.warning("TOOL: Поиск Tavily не вернул результатов в ключе 'results'.")
                logger.debug(f"TOOL: Полный ответ Tavily без результатов: {results_data}")
                return "Поиск Tavily не дал результатов."

        except Exception as e:

            if isinstance(e, requests.exceptions.HTTPError) and e.response is not None:
                 try:
                      error_detail = e.response.json()
                      logger.error(f"TOOL: Ошибка HTTP при выполнении поиска Tavily ({e.response.status_code}): {error_detail}", exc_info=False)
                      return f"Ошибка поиска Tavily ({e.response.status_code}): {json.dumps(error_detail)}"
                 except requests.exceptions.JSONDecodeError:
                      logger.error(f"TOOL: Ошибка HTTP при выполнении поиска Tavily ({e.response.status_code}): {e.response.text}", exc_info=True)
                      return f"Ошибка поиска Tavily ({e.response.status_code}): {e.response.text}"
            else:
                 logger.error(f"TOOL: Ошибка при выполнении поиска Tavily ({type(e).__name__}): {e}", exc_info=True)
                 return f"Ошибка поиска Tavily ({type(e).__name__}): {e}"
    else:
        logger.warning("TOOL: Клиент поиска Tavily недоступен (не инициализирован).")
        return "Инструмент поиска Tavily недоступен."


def check_urls_against_verified_list(inputs: dict) -> dict:
    """
    Извлекает URL из результатов Tavily, НЕ ФИЛЬТРУЕТ их,
    но считает и логирует, сколько из них входят в доверенный список.
    Все извлеченные URL передаются дальше.
    """
    search_results = inputs.get("search_results_structured", [])
    logger.debug(f"TOOL: Вызов check_urls_against_verified_list...")

    all_extracted_urls: List[str] = []

    if not search_results or not isinstance(search_results, list):
        logger.warning("TOOL: Результаты поиска Tavily пусты или имеют неверный формат (ожидался список словарей). Проверка URL невозможна.")
        if isinstance(search_results, str):
            inputs["search_status"] = search_results
        inputs["urls"] = all_extracted_urls
        inputs["verified_count"] = 0
        return inputs


    found_links = [result.get("url") for result in search_results if isinstance(result, dict) and result.get("url")]
    logger.info(f"TOOL: Извлечено URL для проверки и RAG: {len(found_links)}")
    logger.debug(f"TOOL: URL, которые будут переданы в RAG: {found_links}")

    if not found_links:
        logger.warning("TOOL: Не удалось извлечь URL из структурированных результатов Tavily.")
        inputs["urls"] = []
        inputs["verified_count"] = 0
        return inputs


    verified_count = 0
    if VERIFIED_DOMAINS:
        logger.debug(f"TOOL: Проверка {len(found_links)} URL по {len(VERIFIED_DOMAINS)} доверенным доменам...")
        unique_verified_domains_found = set()

        for url in found_links:
            domain = get_domain_from_url(url)
            if domain and domain in VERIFIED_DOMAINS:
                verified_count += 1
                unique_verified_domains_found.add(domain)

                logger.debug(f"TOOL: +++ URL '{url}' (домен: '{domain}') соответствует доверенному списку.")
            else:
                 logger.debug(f"TOOL: --- URL '{url}' (домен: '{domain}') НЕ соответствует доверенному списку.")
        logger.info(f"TOOL: Количество URL, соответствующих доверенному списку: {verified_count} из {len(found_links)} (Уникальных доменов: {len(unique_verified_domains_found)})")
    else:
        logger.warning("TOOL: Список доверенных доменов пуст, проверка не проводилась.")
        verified_count = 0


    inputs["urls"] = found_links
    inputs["verified_count"] = verified_count
    return inputs



WEB_LOADER_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'DNT': '1',
    'Upgrade-Insecure-Requests': '1',
}
bs_transformer = BeautifulSoupTransformer()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, length_function=len, add_start_index=True
)
MAX_PAGE_CHUNKS = settings.tools.max_page_chunks
WEB_LOADER_TIMEOUT = settings.tools.web_loader_timeout

def load_web_page_robust(url: str) -> List[Document]:
    """Загружает веб-страницу с таймаутом, логированием статуса и контента."""
    logger.debug(f"TOOL/LOADER: Попытка загрузки {url} (Таймаут: {WEB_LOADER_TIMEOUT} сек)")
    docs = []
    try:
        loader = WebBaseLoader(
            web_paths=[url],
            bs_kwargs={"parse_only": None},
            requests_kwargs={"headers": WEB_LOADER_HEADERS, "timeout": WEB_LOADER_TIMEOUT}
        )
        docs = loader.load()
        if not docs:
             logger.warning(f"TOOL/LOADER: WebBaseLoader не вернул документы для {url}")
             return [Document(page_content="", metadata={"source": url, "load_error": "Loader returned no documents"})]
        page_content_raw = docs[0].page_content
        if not page_content_raw or not page_content_raw.strip():
            logger.warning(f"TOOL/LOADER: Загруженная страница {url} пуста или не содержит текста (длина: {len(page_content_raw)}).")
            docs[0].metadata["load_error"] = f"Page content is empty (length: {len(page_content_raw)})"

        else:
            logger.info(f"TOOL/LOADER: Страница {url} успешно загружена (сырой контент ~{len(page_content_raw)} симв.)")
            logger.debug(f"TOOL/LOADER: Начало сырого контента {url}:\n{page_content_raw[:500]}...")
        return docs
    except requests.exceptions.Timeout:
         logger.error(f"TOOL/LOADER: Ошибка ТАЙМАУТА ({WEB_LOADER_TIMEOUT} сек) при загрузке {url}", exc_info=False)
         return [Document(page_content="", metadata={"source": url, "load_error": f"Timeout after {WEB_LOADER_TIMEOUT}s"})]
    except requests.exceptions.RequestException as req_err:
         status_code = getattr(req_err.response, 'status_code', 'N/A')
         logger.error(f"TOOL/LOADER: Ошибка HTTP/Соединения ({status_code}) при загрузке {url}: {req_err}", exc_info=False)
         return [Document(page_content="", metadata={"source": url, "load_error": f"HTTP/Connection Error ({status_code}): {req_err}"})]
    except Exception as e:
        error_message = f"Неожиданная ошибка WebBaseLoader при обработке {url}: {e}"
        logger.error(f"TOOL/LOADER: {error_message}", exc_info=True)
        return [Document(page_content="", metadata={"source": url, "load_error": error_message})]


def rag_on_single_page(inputs: Dict[str, Any]) -> str:
    """Загружает, очищает, чанкирует страницу и ищет релевантные фрагменты. С ИСПРАВЛЕННОЙ ОЧИСТКОЙ и ДЕТАЛЬНЫМ ЛОГИРОВАНИЕМ."""
    url = inputs.get("url")
    query = inputs.get("query")
    log_prefix = f"TOOL/RAG [{url[:50]}...]:"
    logger.debug(f"{log_prefix} Начало обработки. Запрос: '{query[:50]}...'")

    if not url or not query:
        logger.error(f"{log_prefix} Отсутствует URL или запрос.")
        return f"Ошибка RAG [{url}]: Отсутствует URL или запрос."

    try:
        current_embedding_model = load_embedding_model()
        if not current_embedding_model: raise ValueError("Модель эмбеддингов не загружена.")
        logger.debug(f"{log_prefix} Модель эмбеддингов получена.")
    except Exception as emb_err:
        logger.error(f"{log_prefix} Ошибка загрузки модели эмбеддингов!", exc_info=True)
        return f"Критическая ошибка RAG [{url}]: Сбой эмбеддингов. {emb_err}"

    page_content_to_split = ""
    raw_content = ""
    raw_content_len = 0

    try:

        docs_raw = load_web_page_robust(url)
        if not docs_raw:
            logger.error(f"{log_prefix} load_web_page_robust вернул пустой список!")
            return f"Ошибка RAG [{url}]: Не удалось получить документ после загрузки."
        load_error = docs_raw[0].metadata.get("load_error")
        if load_error:
            logger.warning(f"{log_prefix} Ошибка на этапе загрузки: {load_error}")

            if "Page content is empty" in load_error and (not docs_raw[0].page_content or not docs_raw[0].page_content.strip()):
                 return f"Ошибка RAG [{url}]: Не удалось загрузить контент. Причина: {load_error}"


        raw_content = docs_raw[0].page_content if docs_raw[0].page_content else ""
        raw_content_len = len(raw_content)
        logger.info(f"{log_prefix} Этап ЗАГРУЗКИ пройден (сырой контент: {raw_content_len} симв).")


        cleaned_content = ""
        try:
            logger.debug(f"{log_prefix} Попытка очистки HTML (без tags_to_extract)...")
            unwanted_tags = ["script", "style", "nav", "footer", "aside", "header", "form", "button", "img", "svg", "iframe", "figure", "noscript"]

            if raw_content and raw_content.strip():
                docs_transformed = bs_transformer.transform_documents(
                    docs_raw,
                    unwanted_tags=unwanted_tags
                )
                cleaned_content = " ".join([doc.page_content for doc in docs_transformed if doc.page_content and doc.page_content.strip()])
                cleaned_len = len(cleaned_content)

                if cleaned_content:
                     page_content_to_split = cleaned_content
                     logger.info(f"{log_prefix} Этап ОЧИСТКИ пройден успешно (очищенный контент: {cleaned_len} симв).")
                     logger.debug(f"{log_prefix} Начало очищенного контента:\n{page_content_to_split[:500]}...")
                else:
                     page_content_to_split = raw_content
                     logger.warning(f"{log_prefix} Очистка HTML не дала результата (0 симв). Используется сырой текст ({raw_content_len} симв).")
            else:

                page_content_to_split = ""
                logger.warning(f"{log_prefix} Исходный сырой контент пуст. Очистка невозможна.")

        except Exception as clean_err:

             page_content_to_split = raw_content
             logger.error(f"{log_prefix} Ошибка при очистке HTML! Используется сырой текст ({raw_content_len} симв). Ошибка: {clean_err}", exc_info=False)


        if not page_content_to_split or not page_content_to_split.strip():
             logger.error(f"{log_prefix} Текст для чанкинга пуст ПОСЛЕ ВСЕХ ПОПЫТОК!")

             if load_error: return f"Ошибка RAG [{url}]: Не удалось загрузить. Причина: {load_error}"
             return f"Ошибка RAG [{url}]: Не найден текстовый контент для обработки."

        logger.debug(f"{log_prefix} Попытка чанкинга текста (~{len(page_content_to_split)} симв)...")
        try:
            chunks = text_splitter.create_documents([page_content_to_split], metadatas=[{"source": url}])
            if not chunks:
                logger.error(f"{log_prefix} Чанкинг не создал ни одного чанка!")
                return f"Ошибка RAG [{url}]: Не удалось разбить контент на чанки."
            logger.info(f"{log_prefix} Этап ЧАНКИНГА пройден ({len(chunks)} чанков создано).")
            logger.debug(f"{log_prefix} Пример первого чанка:\n{chunks[0].page_content[:300]}...")
        except Exception as split_err:
            logger.error(f"{log_prefix} Ошибка при чанкинге текста!", exc_info=True)
            return f"Ошибка RAG [{url}]: Сбой при разбиении на чанки. {split_err}"


        logger.debug(f"{log_prefix} Попытка создания FAISS индекса и поиска...")
        try:
            vectorstore = FAISS.from_documents(chunks, current_embedding_model)
            logger.debug(f"{log_prefix} FAISS индекс создан. Поиск релевантных чанков (k={MAX_PAGE_CHUNKS})...")
            results = vectorstore.similarity_search(query, k=MAX_PAGE_CHUNKS)
            found_chunks_count = len(results)
            logger.info(f"{log_prefix} Этап ПОИСКА ПО ЧАНКАМ пройден ({found_chunks_count} релевантных чанков найдено).")
            if not results:
                 return f"RAG Результат [{url}]: На странице не найдено информации, точно соответствующей запросу '{query[:50]}...'."
            logger.debug(f"{log_prefix} Пример первого найденного релевантного чанка:\n{results[0].page_content[:300]}...")
        except Exception as faiss_err:
            logger.error(f"{log_prefix} Ошибка при создании FAISS или поиске!", exc_info=True)
            return f"Ошибка RAG [{url}]: Сбой векторного поиска. {faiss_err}"


        logger.debug(f"{log_prefix} Формирование итогового контекста...")
        context_parts = []
        empty_chunks_found = 0
        for i, doc in enumerate(results):
            source_info = doc.metadata.get('source', url)
            start_index = doc.metadata.get('start_index', 'N/A')
            if doc.page_content and doc.page_content.strip():
                context_parts.append(f"... (источник: {source_info}, чанк #{i+1}, начало ~: {start_index}) ...\n{doc.page_content}\n...")
            else:
                 empty_chunks_found += 1; logger.warning(f"{log_prefix} Найден пустой релевантный чанк #{i+1}, пропуск.")
        if not context_parts:
             logger.error(f"{log_prefix} Все найденные ({found_chunks_count}) релевантные чанки оказались пустыми!")
             return f"Ошибка RAG [{url}]: Найденные релевантные фрагменты пусты."
        context = "\n\n".join(context_parts)
        final_len = len(context)
        logger.info(f"{log_prefix} Итоговый контекст успешно сформирован ({len(context_parts)} фрагментов, ~{final_len} симв).")
        if empty_chunks_found > 0: logger.warning(f"{log_prefix} При формировании контекста пропущено {empty_chunks_found} пустых чанков.")
        return context

    except Exception as e:
        logger.error(f"{log_prefix} НЕОЖИДАННАЯ ОШИБКА на верхнем уровне rag_on_single_page!", exc_info=True)
        return f"Критическая ошибка RAG [{url}]: Неожиданная ошибка при обработке. {e}"


def process_multiple_urls(inputs: dict) -> str:
    """Вызывает rag_on_single_page для ВСЕХ найденных URL и собирает результаты, включая статусы ошибок."""
    urls = inputs.get("urls", [])
    query = inputs.get("query", "")
    search_status = inputs.get("search_status", "")
    verified_count = inputs.get("verified_count", 0)
    logger.debug(f"TOOL: Вызов process_multiple_urls для {len(urls)} URL (из них {verified_count} совпали с доверенными). Запрос: '{query[:50]}...'")

    if not urls:
        logger.info("TOOL: Нет URL для RAG.");
        if search_status: logger.warning(f"TOOL: Передача статуса/ошибки поиска: {search_status}"); return search_status
        return "Поиск не предоставил URL для дальнейшей обработки."

    all_page_results_with_status = []
    processed_urls = set()
    for i, url in enumerate(urls):
        if url in processed_urls: logger.debug(f"TOOL: Пропуск дублирующего URL: {url}"); continue
        processed_urls.add(url); logger.debug(f"TOOL: Обработка URL {i+1}/{len(urls)}: {url}")
        result_content = ""; result_status = "error"
        try:
            result_content = rag_on_single_page({"url": url, "query": query})
            if result_content.startswith("Ошибка RAG") or result_content.startswith("Критическая ошибка RAG"):
                result_status = "error"; logger.warning(f"TOOL: Зафиксирована ошибка RAG для {url}: {result_content}")
            elif result_content.startswith("RAG Результат") and "не найдено информации" in result_content:
                result_status = "not_found"; logger.info(f"TOOL: RAG не нашел релевантной информации для {url}.")
            elif result_content:
                result_status = "ok"; logger.info(f"TOOL: RAG успешно извлек контент для {url} (~{len(result_content)} симв).")
            else:
                 result_content = f"Ошибка RAG [{url}]: Функция вернула пустой результат."; logger.error(f"TOOL: {result_content}"); result_status = "error"
        except Exception as e:
             result_status = "error"; result_content = f"Критическая ошибка RAG при вызове обработки {url}: {e}"; logger.error(f"TOOL: {result_content}", exc_info=True)
        finally:
             all_page_results_with_status.append({"url": url, "status": result_status, "content": result_content})

    successful_rag_results = []; error_messages = []; not_found_messages = []
    for res in all_page_results_with_status:
        if res["status"] == "ok": successful_rag_results.append(f"Информация со страницы {res['url']}:\n{res['content']}")
        elif res["status"] == "error": error_summary = res['content'].split('\n')[0]; error_messages.append(f"- {res['url']}: {error_summary}")


    verified_info_prefix = ""
    if verified_count > 0:
         plural = "а" if verified_count % 10 == 1 and verified_count % 100 != 11 else ("и" if 1 < verified_count % 10 < 5 and not (11 < verified_count % 100 < 15) else "")
         verified_info_prefix = f"(Проверено: {verified_count} из {len(urls)} найденных URL входят в список доверенных источников.)\n\n"
    elif urls: verified_info_prefix = f"(Проверено: Ни один из {len(urls)} найденных URL не входит в текущий список доверенных источников.)\n\n"

    final_result_parts = []
    if successful_rag_results: final_result_parts.append("\n\n---\n\n".join(successful_rag_results))

    if error_messages: final_result_parts.append("Возникли ошибки при обработке некоторых источников:\n" + "\n".join(error_messages))

    if not final_result_parts:
         logger.warning("TOOL: RAG не дал ни полезной информации, ни явных ошибок (возможно, все 'not_found').")

         load_errors = [res['content'] for res in all_page_results_with_status if res['status'] == "error" and "Не удалось загрузить" in res['content']]
         other_errors = [res['content'] for res in all_page_results_with_status if res['status'] == "error" and "Не удалось загрузить" not in res['content']]
         if load_errors: return verified_info_prefix + f"Не удалось загрузить контент как минимум с одной страницы. Пример ошибки: {load_errors[0].split(':')[-1].strip()}"
         if other_errors: return verified_info_prefix + f"Произошли ошибки при обработке найденных страниц. Пример ошибки: {other_errors[0].split(':')[-1].strip()}"

         return verified_info_prefix + "Поиск по найденным страницам не дал релевантных результатов по вашему запросу."

    final_result_text = "\n\n".join(final_result_parts)
    final_result_with_prefix = verified_info_prefix + final_result_text

    logger.debug(f"TOOL: Финальный результат RAG собран (~{len(final_result_with_prefix)} симв.).")
    max_len = 3500
    if len(final_result_with_prefix) > max_len:
        logger.warning(f"TOOL: Результат RAG обрезан с {len(final_result_with_prefix)} до {max_len} символов.")
        clipped_result = final_result_with_prefix[:max_len] + "\n... (результат поиска обрезан)"
        logger.debug(f"TOOL: Возврат из process_multiple_urls (обрезанный)."); return clipped_result
    else: logger.debug(f"TOOL: Возврат из process_multiple_urls."); return final_result_with_prefix



search_and_rag_chain = (
    RunnableLambda(lambda input_query: {"query": input_query})
    | RunnablePassthrough.assign(
        search_results_structured=RunnableLambda(lambda x: run_tavily_search(x["query"]))
    ).with_config(run_name="TavilyПоиск_Direct")
    | RunnableLambda(check_urls_against_verified_list).with_config(run_name="CheckURL_Verified")
    | RunnableLambda(process_multiple_urls).with_config(run_name="RAGпоСтраницам")
)


__all__ = ["search_and_rag_chain"]

logger.info("Цепочка 'search_and_rag_chain' (без фильтрации, улучшенная очистка/логи RAG) готова.")