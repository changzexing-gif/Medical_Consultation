import streamlit as st

from rag.service import retrieval_service
from ui.common import safety_banner, setup_page, show_evidences


setup_page("检索 Agent", "📚")
safety_banner()
st.title("📚 BGE 检索 Agent")
st.caption("BAAI/bge-small-zh-v1.5 + ChromaDB；查询向量化、HNSW 召回、词项混合重排、TTL 缓存。未使用 LangChain。")

query = st.text_input("检索医学知识", "头痛发热颈部僵硬是否需要急诊")
top_k = st.slider("Top K", 1, 10, 5)
if st.button("向量检索", type="primary"):
    try:
        with st.spinner("正在加载 BGE 并检索……"):
            result = retrieval_service.search(query, top_k)
        a, b, c = st.columns(3)
        a.metric("命中", len(result.evidences))
        b.metric("延迟", f"{result.latency_ms:.1f} ms")
        c.metric("缓存", "命中" if result.cache_hit else "未命中")
        show_evidences([e.to_dict() for e in result.evidences])
    except Exception as exc:
        st.error(f"检索失败：{exc}")
        st.info("首次运行需要联网下载 BGE 模型。请确认已安装 requirements.txt 中的依赖。")
