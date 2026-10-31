import pandas as pd
import streamlit as st

from rag.evaluator import RAGEvaluator
from rag.service import retrieval_service
from ui.common import setup_page


setup_page("RAG 评估", "🧪")
st.title("🧪 RAG 离线评估")
st.caption("固定测试集评估 Hit@K、MRR、答案关键词召回和平均延迟。")
top_k = st.slider("K", 1, 10, 5)
if st.button("运行评估", type="primary"):
    try:
        with st.spinner("正在运行固定评测集……"):
            report = RAGEvaluator(retrieval_service).run(top_k=top_k)
        a, b, c, d = st.columns(4)
        a.metric(f"Hit@{top_k}", f"{report['hit_rate_at_k']:.1%}")
        b.metric("MRR", f"{report['mrr']:.3f}")
        c.metric("关键词召回", f"{report['keyword_recall']:.1%}")
        d.metric("平均延迟", f"{report['avg_latency_ms']:.1f} ms")
        rows = pd.DataFrame(report["cases"])
        st.dataframe(rows, use_container_width=True, hide_index=True)
    except Exception as exc:
        st.error(f"评估失败：{exc}")
