import streamlit as st

from ui.common import init_session, safety_banner, setup_page


setup_page("医疗问诊多智能体系统", "🏥")
init_session()

st.title("🏥 医疗问诊多智能体协作系统")
st.caption("BGE + ChromaDB RAG · LangChain 历史会话 · LangGraph Agent 编排")
safety_banner()

st.markdown("""
### 系统如何协作

`问诊 Agent` → `BGE 检索 Agent` → `分诊 Agent` → `用药 Agent` → `风险 Agent` → `随访 Agent` → `冲突仲裁`

- 问诊 Agent 将患者表述标准化，并用 LangChain 保存多轮会话。
- 检索 Agent 从 Chroma 向量数据库召回医学资料并给出可追溯引用。
- 风险结论具有最高优先级；极高风险时自动取消用药建议并引导急诊。
- 监控面板统计延迟、无召回率、索引规模、成本、反馈和失败模式。
""")

left, middle, right = st.columns(3)
left.metric("专职 Agent", "6")
middle.metric("RAG 模型", "BGE-small-zh")
right.metric("向量数据库", "ChromaDB")

st.info("请从左侧页面导航进入“协调器问诊”。首次检索会下载模型并建立索引，耗时取决于网络与设备。")
