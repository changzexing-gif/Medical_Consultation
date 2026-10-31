import pandas as pd
import plotly.express as px
import streamlit as st

from core.monitoring import monitor
from ui.common import setup_page


setup_page("Agent 监控", "📈")
st.title("📈 Agent 监控面板")
hours = st.selectbox("统计窗口", [1, 6, 24, 72, 168], index=2, format_func=lambda x: f"最近 {x} 小时")
data = monitor.dashboard(hours)

a, b, c, d = st.columns(4)
a.metric("检索平均 latency", f"{data['avg_latency']:.1f} ms")
b.metric("检索 p99 latency", f"{data['p99_latency']:.1f} ms")
c.metric("召回失败率", f"{data['no_hit_rate']:.1%}")
d.metric("检索请求数", data["retrieval_count"])

st.subheader("索引规模")
if data["index_state"]:
    st.dataframe(pd.DataFrame(data["index_state"]), use_container_width=True, hide_index=True)
else:
    st.info("尚未建立索引。")

left, right = st.columns(2)
with left:
    st.subheader("失败模式")
    if data["failures"]:
        frame = pd.DataFrame(data["failures"])
        st.plotly_chart(px.bar(frame, x="mode", y="count"), use_container_width=True)
    else:
        st.success("当前窗口无失败事件")
with right:
    st.subheader("质量信号")
    feedback = {int(x["value"]): int(x["count"]) for x in data["feedback"]}
    up, down = feedback.get(1, 0), feedback.get(-1, 0)
    rate = up / max(1, up + down)
    st.metric("👍 反馈率", f"{rate:.1%}", help=f"👍 {up} / 👎 {down}")
    if up + down:
        st.plotly_chart(px.pie(names=["👍", "👎"], values=[up, down]), use_container_width=True)

st.subheader("LLM 成本（按 Agent / 用户 / Query）")
if data["costs"]:
    costs = pd.DataFrame(data["costs"])
    st.dataframe(costs, use_container_width=True, hide_index=True)
else:
    st.info("当前为本地规则模式，尚无 LLM 成本记录。配置 LLM_API_KEY 后自动采集 token 与调用事件。")

st.subheader("按时间聚合")
if data["timeline"]:
    timeline = pd.DataFrame(data["timeline"])
    st.plotly_chart(px.line(timeline, x="hour", y=["calls", "failures"], markers=True), use_container_width=True)
