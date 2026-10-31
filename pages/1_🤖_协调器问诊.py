from __future__ import annotations

import streamlit as st

from core.monitoring import monitor
from core.workflow import MedicalWorkflow
from ui.common import context_form, init_session, safety_banner, setup_page, show_evidences


setup_page("协调器问诊", "🤖")
init_session()
safety_banner()


@st.cache_resource
def get_workflow() -> MedicalWorkflow:
    return MedicalWorkflow()


st.title("🤖 协调器问诊")
st.caption("LangGraph 按依赖关系调度 6 个 Agent，并执行统一冲突仲裁。")
context = context_form()

examples = ["我头痛3天，发热38.2℃，还有点恶心", "胸口压榨样疼痛伴大汗并放射左臂", "咳嗽流涕两天，没有呼吸困难"]
example = st.selectbox("示例", ["自定义"] + examples)
user_input = st.text_area("请描述症状", value="" if example == "自定义" else example, height=120,
                          placeholder="症状、持续时间、严重程度、伴随症状……")

if st.button("开始多 Agent 分析", type="primary", use_container_width=True, disabled=not user_input.strip()):
    with st.status("正在执行多智能体工作流……", expanded=True) as status:
        st.write("问诊信息结构化 → BGE 检索 → 分诊/用药/风险 → 随访 → 仲裁")
        try:
            result = get_workflow().invoke(user_input, context)
            st.session_state.last_result = result
            status.update(label="分析完成", state="complete")
        except Exception as exc:
            status.update(label="分析失败", state="error")
            st.error(f"执行失败：{exc}")

result = st.session_state.last_result
if result:
    final = result["final"]
    urgency = final["urgency_level"]
    color = {"极高": "red", "高": "orange", "中": "orange", "低": "green"}.get(urgency, "gray")
    st.header("最终建议")
    st.markdown(f"### :{color}[风险等级：{urgency}]")
    st.write(final["recommendation"])
    if final["conflicts"]:
        for conflict in final["conflicts"]:
            st.warning(conflict)
    tab_summary, tab_agents, tab_sources, tab_followup = st.tabs(["问诊小结", "Agent 轨迹", "循证依据", "随访计划"])
    with tab_summary:
        c = final["consultation"]
        st.write("**症状：**", "、".join(c.get("symptoms", [])) or "待补充")
        st.write("**持续时间：**", c.get("duration", "待补充"))
        st.write("**初步方向（非诊断）：**")
        st.dataframe(c.get("suspected_diagnosis", []), use_container_width=True, hide_index=True)
        if c.get("need_followup"):
            st.write("**建议补充：**", "；".join(c["need_followup"]))
        medication = final.get("medication", {})
        st.write("**用药安全审查：**")
        if medication.get("recommended_drugs"):
            st.dataframe(medication["recommended_drugs"], use_container_width=True, hide_index=True)
        else:
            st.info("本次未提供自动用药建议。")
        for warning in medication.get("warnings", []) + medication.get("contraindications", []):
            st.warning(warning)
    with tab_agents:
        for name, agent_result in result["results"].items():
            icon = "✅" if agent_result.success else "❌"
            with st.expander(f"{icon} {name} · {agent_result.latency_ms:.1f} ms"):
                st.json(agent_result.data if agent_result.success else {"error": agent_result.error})
    with tab_sources:
        show_evidences(final.get("evidences", []))
    with tab_followup:
        st.json(final.get("followup", {}))
    st.caption(final["disclaimer"])
    st.write("这次回答有帮助吗？")
    a, b, _ = st.columns([1, 1, 8])
    if a.button("👍", key=f"up-{result['query_id']}"):
        monitor.add_feedback(result["query_id"], 1, context.user_id)
        st.toast("感谢反馈")
    if b.button("👎", key=f"down-{result['query_id']}"):
        monitor.add_feedback(result["query_id"], -1, context.user_id)
        st.toast("已记录，将用于质量改进")
