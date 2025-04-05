import streamlit as st
import uuid
import logging
import socket

st.set_page_config(
    page_title="Ассистент по Госзакупкам",
    page_icon="🤖",
    layout="wide",
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

if 'session_id' not in st.session_state:
    st.session_state['session_id'] = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.flow_initialized = False
    st.session_state.init_error = None
    st.session_state.internet_checked = False
    st.session_state.run_agent = None
    logger.info(f"STREAMLIT: Новая сессия Streamlit создана: {st.session_state['session_id']}")

@st.cache_data(show_spinner=False)
def check_internet_connection(host="8.8.8.8", port=53, timeout=3):
    logger.debug("STREAMLIT: Проверка интернет-соединения...")
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        logger.debug("STREAMLIT: Проверка интернета: Успешно.")
        return True
    except socket.error as ex:
        logger.warning(f"STREAMLIT: Проверка интернета: Не удалось подключиться ({ex}).")
        return False

@st.cache_resource(show_spinner="Инициализация ассистента...")
def initialize_flow_components():
    """
    Импортирует зависимости, загружает конфиг и инициализирует LLM.
    Возвращает кортеж (run_agent_func, settings_object, error_message).
    """
    logger.info("STREAMLIT: Попытка инициализации компонентов (внутри @st.cache_resource)...")
    run_agent_local_func = None
    settings_local = None
    error_msg = None
    success = False
    try:
        from src.config import settings
        settings_local = settings
        if not settings_local:
             raise ValueError("Объект настроек (settings) не был загружен из src.config.")

        log_level_numeric = getattr(logging, settings_local.log_level.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level_numeric)
        for lib_logger in ["httpx", "httpcore", "google.api_core", "google.auth", "urllib3", "langchain_community.utils.user_agent"]:
            logging.getLogger(lib_logger).setLevel(logging.WARNING)
        logger.info(f"STREAMLIT: Уровень логирования установлен в {settings_local.log_level}.")

        from src.agent.executor import initialize_flow, run_agent as agent_runner
        run_agent_local_func = agent_runner

        logger.debug("STREAMLIT: Вызов initialize_flow()...")
        success, error_msg_init = initialize_flow()
        logger.debug(f"STREAMLIT: initialize_flow() вернул: success={success}, error='{error_msg_init}'")

        if success:
            logger.info("STREAMLIT: Инициализация компонентов прошла успешно.")
            return run_agent_local_func, settings_local, None
        else:
            error_msg = error_msg_init or "Неизвестная ошибка при инициализации потока."
            logger.error(f"STREAMLIT: Ошибка инициализации: {error_msg}")
            return (lambda q, sid: f"Ошибка: {error_msg}"), settings_local, error_msg

    except ImportError as e:
         error_msg = f"Критическая ошибка импорта при инициализации: {e}"
         logger.critical(error_msg, exc_info=True)
         class DummySettings:
            llm_provider = "Ошибка импорта"
            local_llm = type('obj', (object,), {'model_gguf_path': 'N/A'})()
            gemini_llm = type('obj', (object,), {'gemini_model_name': 'N/A'})()
            agent_verbose = "N/A"; log_level = "ERROR"
         settings_local = DummySettings()
         return (lambda q, sid: error_msg), settings_local, error_msg
    except Exception as e:
        error_msg = f"Неожиданная ошибка при инициализации: {e}"
        logger.critical(error_msg, exc_info=True)
        class DummySettings:
             llm_provider = "Ошибка инициализации"; local_llm = type(...); gemini_llm = type(...); agent_verbose = "N/A"; log_level = "ERROR"
        settings_local = DummySettings()
        return (lambda q, sid: error_msg), settings_local, error_msg


run_agent_func_from_init, settings_loaded, init_error_msg = initialize_flow_components()
has_internet = check_internet_connection()

if not init_error_msg and run_agent_func_from_init and settings_loaded:
    st.session_state.flow_initialized = True
    st.session_state.init_error = None
    st.session_state.run_agent = run_agent_func_from_init
    logger.info("STREAMLIT: Состояние обновлено - компоненты инициализированы.")
else:
    st.session_state.flow_initialized = False
    st.session_state.init_error = init_error_msg or st.session_state.get('init_error') or "Неизвестная ошибка инициализации."
    def error_stub(query: str, session_id: str) -> str:
        error_message = st.session_state.get('init_error', "Компоненты не инициализированы.")
        return f"Ошибка: {error_message}"
    st.session_state.run_agent = error_stub
    logger.error(f"STREAMLIT: Состояние обновлено - ошибка инициализации: {st.session_state.init_error}")


st.title("🤖 Ассистент по Госзакупкам (44-ФЗ / 223-ФЗ)")

if settings_loaded:
    provider_info = f"Провайдер LLM: `{settings_loaded.llm_provider}`"
    model_info = f"Модель: `{settings_loaded.local_llm.model_gguf_path if settings_loaded.llm_provider=='local' else settings_loaded.gemini_llm.gemini_model_name}`"
    st.caption(f"{provider_info} | {model_info}")
else:
    st.caption("Провайдер LLM: Не удалось загрузить конфигурацию")

if st.session_state.init_error:
    st.error(st.session_state.init_error, icon="🚨")

if not has_internet:
    st.warning("Нет подключения к Интернету. Поиск в реальном времени будет недоступен.", icon="🌐")


st.sidebar.title("Опции")
if st.sidebar.button("Новый диалог", key="new_chat"):
    logger.info(f"STREAMLIT: Сброс диалога для сессии: {st.session_state['session_id']}")
    st.session_state.messages = []
    logger.info(f"STREAMLIT: Диалог сброшен для сессии: {st.session_state['session_id']}")
    st.rerun()

st.sidebar.info(f"ID сессии: {st.session_state['session_id'][:8]}...")
st.sidebar.markdown("---")
if settings_loaded:
    st.sidebar.markdown(f"**Настройки:**")
    st.sidebar.markdown(f"*   LLM: `{settings_loaded.llm_provider}`")
    st.sidebar.markdown(f"*   Agent Verbose: `{settings_loaded.agent_verbose}`")
    st.sidebar.markdown(f"*   Log Level: `{settings_loaded.log_level}`")
else:
    st.sidebar.warning("Настройки не загружены.")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


prompt_disabled = not st.session_state.flow_initialized
prompt_placeholder = "Ассистент недоступен..." if prompt_disabled else "Задайте ваш вопрос..."

if prompt := st.chat_input(prompt_placeholder, disabled=prompt_disabled):

    current_run_agent_func = st.session_state.get('run_agent')

    if not st.session_state.flow_initialized or not current_run_agent_func:
        st.error("Ассистент недоступен или произошла ошибка. Невозможно обработать запрос.", icon="🚫")
        logger.error("STREAMLIT: Попытка использовать ассистента, когда он не инициализирован или функция run_agent отсутствует в состоянии.")
    else:
        logger.info(f"STREAMLIT: Получен новый запрос от пользователя (сессия: {st.session_state['session_id']}): '{prompt[:100]}...'")
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Думаю... 🧠")

            try:
                assistant_response = current_run_agent_func(prompt, session_id=st.session_state['session_id'])
                message_placeholder.markdown(assistant_response)
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                logger.info(f"STREAMLIT: Ответ ассистента успешно отображен (сессия: {st.session_state['session_id']}).")
            except Exception as e:
                error_msg = f"Неожиданная ошибка в Streamlit при обработке ответа: {e}"
                logger.error(error_msg, exc_info=True)
                message_placeholder.error(error_msg, icon="🚨")
                st.session_state.messages.append({"role": "assistant", "content": f"Произошла ошибка: {error_msg}"})


elif prompt_disabled and st.session_state.init_error:
     pass
elif prompt_disabled:
     st.warning("Ассистент недоступен, хотя явных ошибок при инициализации не было. Проверьте логи.", icon="⚠️")