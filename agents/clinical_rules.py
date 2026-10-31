from __future__ import annotations

import re
from typing import Any


SYMPTOM_ALIASES = {
    "脑壳痛": "头痛", "头疼": "头痛", "发烧": "发热", "烧": "发热",
    "胸闷": "胸部不适", "喘不上气": "呼吸困难", "气短": "呼吸困难",
    "拉肚子": "腹泻", "肚子疼": "腹痛", "想吐": "恶心", "吐": "呕吐",
    "咳": "咳嗽", "嗓子疼": "咽痛", "心慌": "心悸",
}

RED_FLAG_RULES: list[tuple[str, list[str], int]] = [
    ("疑似急性冠脉综合征", ["胸", "压榨", "大汗"], 100),
    ("胸痛向左臂/下颌放射", ["胸", "放射"], 95),
    ("严重呼吸困难", ["呼吸困难"], 90),
    ("意识状态改变", ["意识", "不清"], 100),
    ("疑似卒中", ["口角", "歪"], 100),
    ("疑似卒中", ["肢体", "无力"], 95),
    ("疑似脑膜刺激征", ["发热", "颈", "僵"], 90),
    ("呕血/消化道出血", ["呕血"], 95),
    ("严重过敏反应", ["过敏", "呼吸困难"], 100),
    ("自伤风险", ["自杀"], 100),
]


def normalize_symptoms(text: str) -> list[str]:
    normalized = text
    for alias, standard in SYMPTOM_ALIASES.items():
        if alias in text:
            normalized += " " + standard
    candidates = [
        "头痛", "发热", "乏力", "恶心", "呕吐", "咳嗽", "咽痛", "流涕",
        "鼻塞", "胸痛", "胸部不适", "呼吸困难", "腹痛", "腹泻", "心悸",
        "头晕", "皮疹", "颈部僵硬", "大汗", "肢体无力",
    ]
    found = [s for s in candidates if s in normalized]
    temp = re.search(r"(\d{2}(?:\.\d)?)\s*(?:℃|度)", text)
    if temp:
        found.append(f"体温{temp.group(1)}℃")
    return list(dict.fromkeys(found))


def detect_red_flags(text: str, vitals: dict[str, float] | None = None) -> list[dict[str, Any]]:
    compact = text.replace(" ", "")
    flags = [{"name": name, "score": score} for name, words, score in RED_FLAG_RULES if all(w in compact for w in words)]
    vitals = vitals or {}
    if vitals.get("spo2", 100) < 92:
        flags.append({"name": "血氧饱和度低于92%", "score": 100})
    if vitals.get("systolic_bp", 120) >= 180 or vitals.get("diastolic_bp", 80) >= 120:
        flags.append({"name": "高血压危象阈值", "score": 95})
    if vitals.get("heart_rate", 80) > 130 or vitals.get("heart_rate", 80) < 40:
        flags.append({"name": "严重心率异常", "score": 90})
    if vitals.get("temperature", 37) >= 40:
        flags.append({"name": "超高热", "score": 85})
    return flags


def likely_diagnoses(symptoms: list[str]) -> list[dict[str, Any]]:
    joined = " ".join(symptoms)
    scores: dict[str, float] = {}
    if any(x in joined for x in ("咳嗽", "咽痛", "流涕", "鼻塞")):
        scores["急性上呼吸道感染"] = 0.62
    if "发热" in joined and "头痛" in joined:
        scores["病毒性感染"] = max(scores.get("病毒性感染", 0), 0.55)
    if "颈部僵硬" in joined and "发热" in joined:
        scores["脑膜炎（需紧急排除）"] = 0.72
    if "头痛" in joined and "恶心" in joined:
        scores["偏头痛"] = 0.38
    if "胸痛" in joined or "胸部不适" in joined:
        scores["急性冠脉综合征（需排除）"] = 0.55
    if "腹痛" in joined and any(x in joined for x in ("腹泻", "呕吐")):
        scores["急性胃肠炎"] = 0.60
    if not scores:
        scores["症状原因待查"] = 0.35
    return [{"disease": k, "probability": v} for k, v in sorted(scores.items(), key=lambda x: -x[1])[:5]]
