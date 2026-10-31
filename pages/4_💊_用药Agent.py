import streamlit as st

from agents.medication_agent import MedicationAgent
from agents.types import AgentResult, UserContext
from ui.common import safety_banner, setup_page


setup_page("用药 Agent", "💊")
safety_banner()
st.title("💊 用药安全 Agent")
st.caption("检查相互作用、过敏禁忌、特殊人群与重复成分；不生成处方。")

symptoms = st.multiselect("症状", ["发热", "头痛", "咳嗽", "咽痛"], ["发热"])
allergies = st.text_input("过敏史", "")
current = st.text_input("当前用药", "")
history = st.text_input("既往病史", "")
age = st.number_input("年龄", 0, 120, 30)
pregnant = st.checkbox("妊娠期")
if st.button("执行用药安全审查", type="primary"):
    split = lambda x: [i.strip() for i in x.replace("，", ",").split(",") if i.strip()]
    context = UserContext("medication-demo", age=age, allergies=split(allergies),
                          current_medications=split(current), medical_history=split(history), pregnant=pregnant)
    upstream = {"consultation": AgentResult("consultation", True, {"symptoms": symptoms}, 0)}
    result = MedicationAgent().run("用药审查", context, upstream)
    st.json(result.data)
