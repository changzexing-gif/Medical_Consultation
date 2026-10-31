import json

import streamlit as st

from core.config import settings
from rag.indexer import MedicalIndexer
from ui.common import setup_page


setup_page("知识库管理", "🗄️")
st.title("🗄️ BGE / Chroma 知识库管理")
st.write(f"嵌入模型：`{settings.bge_model}`")
st.write(f"集合：`{settings.collection_name}`")
st.write(f"持久化目录：`{settings.chroma_path}`")

indexer = MedicalIndexer()
try:
    st.metric("当前 chunks", indexer.count())
except Exception as exc:
    st.info(f"索引尚未就绪：{exc}")

if st.button("构建 / 更新内置知识库", type="primary"):
    try:
        with st.spinner("正在加载 BGE、切块并写入 Chroma……"):
            count = indexer.build()
        st.success(f"完成，共 {count} chunks")
    except Exception as exc:
        st.error(f"构建失败：{exc}")

uploaded = st.file_uploader("追加 JSON 文档", type=["json"], help="JSON 数组，每项需包含 id/title/source/content")
if uploaded and st.button("校验并追加上传内容"):
    try:
        docs = json.load(uploaded)
        required = {"id", "title", "source", "content"}
        if not isinstance(docs, list) or any(not required.issubset(d) for d in docs):
            raise ValueError("格式不正确：必须为文档数组，并包含 id/title/source/content")
        count = indexer.build(docs)
        st.success(f"追加完成，集合当前共 {count} chunks")
    except Exception as exc:
        st.error(str(exc))
