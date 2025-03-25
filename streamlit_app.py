import streamlit as st
from src.agent.executor import run_agent

st.set_page_config(page_title="Ассистент по Госзакупкам", layout="wide")
st.title("🤖 Ассистент по Госзакупкам (44-ФЗ / 223-ФЗ)")
st.caption("На базе локальной LLM с поиском по доверенным источникам")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Задайте ваш вопрос по 44-ФЗ или 223-ФЗ..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Думаю... 🧠")

        assistant_response = run_agent(prompt)

        message_placeholder.markdown(assistant_response)

    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

if st.button("Очистить диалог"):
    st.session_state.messages = []
    st.rerun()