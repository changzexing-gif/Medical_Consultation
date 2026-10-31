import streamlit as st

from agents.risk_agent import RiskAgent
from agents.types import UserContext
from ui.common import safety_banner, setup_page


setup_page("风险评估 Agent", "⚠️")
safety_banner()
st.title("⚠️ 风险评估 Agent")

text = st.text_area("症状描述", "胸口压榨样疼痛伴大汗并向左臂放射")
c1, c2, c3 = st.columns(3)
bp = c1.number_input("收缩压", 40, 260, 120)
hr = c2.number_input("心率", 20, 250, 75)
spo2 = c3.number_input("血氧", 50, 100, 98)
age = st.number_input("年龄", 0, 120, 50)
if st.button("评估紧急程度", type="primary"):
    ctx = UserContext("risk-demo", age=age, vitals={"systolic_bp": bp, "heart_rate": hr, "spo2": spo2})
    result = RiskAgent().run(text, ctx)
    level = result.data.get("urgency_level")
    if level in ("极高", "高"):
        st.error(f"风险等级：{level} — {result.data.get('recommendation')}")
    else:
        st.success(f"风险等级：{level} — {result.data.get('recommendation')}")
    st.json(result.data)
