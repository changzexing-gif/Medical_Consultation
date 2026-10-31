import streamlit as st

from agents.followup_agent import FollowupAgent
from agents.triage_agent import TriageAgent
from agents.types import AgentResult, UserContext
from ui.common import safety_banner, setup_page


setup_page("分诊与随访 Agent", "🧭")
safety_banner()
st.title("🧭 新增 Agent：快速分诊 + 随访")
st.caption("快速分诊在复杂推理前拦截危急症；随访 Agent 根据风险等级生成复诊与监测计划。")
text = st.text_area("症状", "咳嗽流涕两天，没有呼吸困难")
urgency = st.selectbox("模拟已完成的风险等级", ["低", "中", "高", "极高"])
if st.button("运行两个新增 Agent", type="primary"):
    context = UserContext("triage-demo")
    triage = TriageAgent().run(text, context)
    upstream = {"risk": AgentResult("risk", True, {"urgency_level": urgency}, 0)}
    followup = FollowupAgent().run(text, context, upstream)
    left, right = st.columns(2)
    left.subheader("快速分诊")
    left.json(triage.data)
    right.subheader("随访计划")
    right.json(followup.data)
