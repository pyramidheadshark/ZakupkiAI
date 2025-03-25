import re
import logging
from typing import List, Dict, Any

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter # Изменен импорт
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.tools import Tool
from langchain.schema.runnable import RunnableLambda, RunnablePassthrough
from langchain.schema import Document
from langchain_community.document_transformers import BeautifulSoupTransformer

from src.config import (
    VERIFIED_DOMAINS,
    EMBEDDING_MODEL_NAME,
    MAX_SEARCH_RESULTS,
    MAX_PAGE_CHUNKS
)

logger = logging.getLogger(__name__)

try:
    search_tool_backend = DuckDuckGoSearchRun()
except ImportError:
    logger.error("Библиотека duckduckgo-search не установлена. Поиск будет недоступен.")
    search_tool_backend = None

def filter_urls(results_str: str) -> List[str]:
    """Парсит строку результатов DuckDuckGo и фильтрует URL по доверенным доменам."""
    urls = []
    if not results_str: return urls

    link_pattern = re.compile(r"link: (https?://[^\s,\]]+)")
    found_links = link_pattern.findall(results_str)
    logger.info(f"Найдено ссылок поиском: {len(found_links)}")

    if not VERIFIED_DOMAINS:
        logger.warning("Список доверенных доменов пуст, фильтрация URL отключена.")
        return found_links[:MAX_SEARCH_RESULTS]

    for url in found_links:
        try:
            domain = url.split('//')[-1].split('/')[0].split(':')[0].lower()
            if domain in VERIFIED_DOMAINS:
                if url not in urls:
                    urls.append(url)
        except Exception:
            logger.warning(f"Не удалось извлечь домен из URL: {url}", exc_info=False)
            continue
    logger.info(f"Отфильтровано доверенных URL: {len(urls)}")
    return urls[:MAX_SEARCH_RESULTS]


def load_web_page_robust(url: str) -> List[Document]:
    try:
        loader = WebBaseLoader(
            web_paths=[url],
            bs_kwargs={"parse_only": None},
            requests_kwargs={"headers": {"User-Agent": "Mozilla/5.0"}, "timeout": 15}
        )
        docs = loader.load()
        return docs
    except Exception as e:
        logger.warning(f"Не удалось загрузить страницу {url}: {e}", exc_info=False)
        return []


bs_transformer = BeautifulSoupTransformer()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len
)

try:
    logger.info(f"Загрузка модели эмбеддингов: {EMBEDDING_MODEL_NAME}")
    embeddings_model = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'}, # or 'cuda'
        encode_kwargs={'normalize_embeddings': True}
    )
    logger.info("Модель эмбеддингов загружена.")
except Exception as e:
    logger.error("Ошибка при загрузке модели эмбеддингов!", exc_info=True)
    embeddings_model = None

def rag_on_single_page(inputs: Dict[str, Any]) -> str:
    """Загружает страницу, очищает, чанкирует, ищет релевантные части по запросу."""
    url = inputs.get("url")
    query = inputs.get("query")

    if not url or not query: return "Ошибка: Отсутствует URL или запрос для RAG."
    if not embeddings_model: return "Ошибка: Модель эмбеддингов не загружена."

    logger.info(f"Обработка RAG для URL: {url} по запросу: '{query[:50]}...'")
    try:
        docs_raw = load_web_page_robust(url)
        if not docs_raw: return f"Не удалось загрузить или получить контент с {url}"

        docs_transformed = bs_transformer.transform_documents(
            docs_raw, tags_to_extract=["p", "h1", "h2", "h3", "li", "span"]
        )
        if not docs_transformed or not docs_transformed[0].page_content.strip():
             logger.warning(f"После очистки не осталось контента для {url}")

             page_content_to_split = docs_raw[0].page_content
             if not page_content_to_split.strip(): return f"Нет текстового контента на {url}"
        else:
            page_content_to_split = docs_transformed[0].page_content


        chunks = text_splitter.create_documents([page_content_to_split], metadatas=[{"source": url}])
        if not chunks:
            logger.warning(f"Не удалось разбить на чанки контент с {url}")
            return f"Не удалось обработать контент с {url}"
        logger.info(f"Разбито на {len(chunks)} чанков для {url}")

        vectorstore = FAISS.from_documents(chunks, embeddings_model)

        results = vectorstore.similarity_search(query, k=MAX_PAGE_CHUNKS)
        logger.info(f"Найдено {len(results)} релевантных чанков на {url}")

        if not results:
            return f"Не найдено релевантной информации по запросу '{query[:50]}...' на странице {url}"

        context = "\n\n".join([f"...{doc.page_content}..." for doc in results])
        return f"Найденные фрагменты с {url} по запросу '{query[:50]}...':\n{context}"

    except Exception as e:
        logger.error(f"Ошибка при RAG-обработке {url}", exc_info=True)
        return f"Произошла ошибка при обработке {url}"


def run_search_if_needed(query: str) -> str:
    """Запускает поиск только если search_tool_backend доступен."""
    if search_tool_backend:
        return search_tool_backend.run(query)
    return ""

def process_multiple_urls(inputs: dict) -> str:
    """Вызывает rag_on_single_page для списка URL."""
    urls = inputs.get("urls", [])
    query = inputs.get("query", "")
    if not urls:
        return "Поиск не дал релевантных ссылок в доверенных источниках."

    all_page_results = []
    for url in urls:
        result = rag_on_single_page({"url": url, "query": query})
        all_page_results.append(result)
    return "\n\n---\n\n".join(all_page_results)

search_and_rag_chain = (
    RunnablePassthrough()
    | RunnableLambda(lambda query: {"query": query, "search_results": run_search_if_needed(query)})
    | RunnableLambda(lambda x: {"query": x["query"], "urls": filter_urls(x["search_results"])})
    | RunnableLambda(process_multiple_urls)
)

search_and_process_tool = Tool(
    name="SearchAndProcessTrustedWeb",
    func=search_and_rag_chain.invoke,
    description=(
        "Очень важно использовать этот инструмент для поиска актуальной информации "
        "по госзакупкам (законы 44-ФЗ, 223-ФЗ, процедуры, термины, практика) "
        "в интернете на доверенных источниках (zakupki.gov.ru, consultant.ru, garant.ru и т.д.). "
        "Инструмент сам найдет релевантные страницы и извлечет из них нужные фрагменты текста. "
        "Используй его, когда не уверен в ответе или нужна самая свежая информация. "
        "Вход - точный поисковый запрос (например, 'сроки подачи заявок на электронный аукцион 44-ФЗ', "
        "'требования к участникам закупки по 223-ФЗ', 'ответственность за нарушение контракта госзакупки')."
    ),
    # coroutine=search_and_rag_chain.ainvoke
)

agent_tools = [search_and_process_tool]