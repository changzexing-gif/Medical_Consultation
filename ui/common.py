from __future__ import annotations

import uuid
from typing import Any

import streamlit as st

from agents.types import UserContext


def setup_page(title: str, icon: str = "🩺") -> None:
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    st.markdown(
        """<style>
        .block-container{padding-top:2rem;max-width:1280px}
        [data-testid=stMetric]{background:#fff;border:1px solid #dbe7e5;padding:12px;border-radius:12px}
        .safety{padding:12px 16px;background:#fff7ed;border-left:4px solid #f97316;border-radius:6px}
        .source{padding:10px 14px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;margin:6px 0}
        </style>""",
        unsafe_allow_html=True,
    )


def safety_banner() -> None:
    st.markdown(
        '<div class="safety"><b>安全提示：</b>本系统仅用于教学和健康教育，不能替代医生诊断或处方。'
        '如有胸痛、呼吸困难、意识改变、肢体无力等危险信号，请立即拨打 120。</div>',
        unsafe_allow_html=True,
    )


def init_session() -> None:
    st.session_state.setdefault("session_id", str(uuid.uuid4()))
    st.session_state.setdefault("user_id", "demo-user")
    st.session_state.setdefault("last_result", None)


def context_form() -> UserContext:
    with st.sidebar:
        st.subheader("患者信息（可选）")
        age = st.number_input("年龄", min_value=0, max_value=120, value=None, placeholder="未填写")
        sex = st.selectbox("性别", ["未说明", "女", "男", "其他"])
        pregnant = st.checkbox("妊娠期") if sex == "女" else False
        allergies = st.text_input("药物过敏史", placeholder="如：青霉素，磺胺")
        medications = st.text_input("当前用药", placeholder="如：华法林，阿司匹林")
        history = st.text_input("既往病史", placeholder="如：冠心病，肝病")
        with st.expander("生命体征"):
            temperature = st.number_input("体温 ℃", 30.0, 45.0, 36.8, 0.1)
            systolic = st.number_input("收缩压 mmHg", 40, 260, 120)
            diastolic = st.number_input("舒张压 mmHg", 20, 180, 80)
            heart_rate = st.number_input("心率 次/分", 20, 250, 75)
            spo2 = st.number_input("血氧 %", 50, 100, 98)
    split = lambda x: [i.strip() for i in x.replace("，", ",").split(",") if i.strip()]
    return UserContext(
        session_id=st.session_state.session_id, user_id=st.session_state.user_id,
        age=int(age) if age is not None else None, sex=sex, pregnant=pregnant,
        allergies=split(allergies), current_medications=split(medications),
        medical_history=split(history),
        vitals={"temperature": temperature, "systolic_bp": systolic,
                "diastolic_bp": diastolic, "heart_rate": heart_rate, "spo2": spo2},
    )


def show_evidences(evidences: list[dict[str, Any]]) -> None:
    if not evidences:
        st.info("本次未检索到可展示的证据。")
        return
    for index, item in enumerate(evidences, 1):
        source = item.get("source", "未知来源")
        page = item.get("page", "")
        score = item.get("relevance", 0)
        st.markdown(f"**[{index}] {source} {page}** · 相关度 `{score:.3f}`")
        st.caption(item.get("content", ""))
        if item.get("url"):
            st.link_button("查看来源", item["url"])
