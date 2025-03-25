from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory

from src.agent.models import llm
from src.agent.tools import agent_tools
from src.agent.prompts import AGENT_PROMPT
import logging

logger = logging.getLogger(__name__)

try:
    agent = create_react_agent(llm=llm, tools=agent_tools, prompt=AGENT_PROMPT)
    logger.info("ReAct агент успешно создан.")
except Exception as e:
    logger.error("Ошибка при создании ReAct агента!", exc_info=True)
    agent = None

if agent:
    # memory = ConversationBufferWindowMemory(k=3, memory_key="chat_history", input_key="input", output_key="output")

    agent_executor = AgentExecutor(
        agent=agent,
        tools=agent_tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        # memory=memory,
    )
    logger.info("AgentExecutor успешно создан.")
else:
    agent_executor = None
    logger.error("AgentExecutor не может быть создан, так как агент не инициализирован.")


def run_agent(query: str) -> str:
    """Запускает агент для обработки запроса пользователя."""
    if not agent_executor:
        return "Ошибка: Агент не инициализирован."
    try:
        logger.info(f"Запуск агента для запроса: '{query[:100]}...'")
        # result = agent_executor.invoke({"input": query, "chat_history": memory.load_memory_variables({})["chat_history"]})
        result = agent_executor.invoke({"input": query})
        logger.info(f"Агент завершил работу.")
        return result.get("output", "Агент не вернул ответ.")
    except Exception as e:
        logger.error(f"Ошибка во время выполнения агента для запроса: '{query[:100]}...'", exc_info=True)
        return f"Произошла ошибка при обработке вашего запроса: {e}"