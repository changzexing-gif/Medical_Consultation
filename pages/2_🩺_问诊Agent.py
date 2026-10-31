import streamlit as st

from agents.consultation_agent import ConsultationAgent
from agents.types import UserContext
from core.memory import conversation_store
from ui.common import init_session, safety_banner, setup_page


setup_page("问诊 Agent", "🩺")
init_session()
safety_banner()
st.title("🩺 问诊 Agent")
st.caption("症状标准化、动态追问、初步鉴别和红旗征筛查；历史由 LangChain InMemoryChatMessageHistory 管理。")

message = st.chat_input("继续描述症状或回答追问")
history = conversation_store.history(st.session_state.session_id)
for item in history.messages:
    with st.chat_message("user" if item.type == "human" else "assistant"):
        st.write(item.content)
if message:
    with st.chat_message("user"):
        st.write(message)
    context = UserContext(session_id=st.session_state.session_id)
    result = ConsultationAgent().run(message, context)
    with st.chat_message("assistant"):
        if result.success:
            st.write("已完成结构化问诊：")
            st.json(result.data)
            for question in result.data.get("need_followup", []):
                st.write("-", question)
        else:
            st.error(result.error)
if st.button("清空本会话历史"):
    conversation_store.clear(st.session_state.session_id)
    st.rerun()
