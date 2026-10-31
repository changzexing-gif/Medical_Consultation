from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIR = ROOT / ".runtime"
RUNTIME_DIR.mkdir(exist_ok=True)


@dataclass(frozen=True)
class Settings:
    app_name: str = "医疗问诊多智能体协作系统"
    bge_model: str = os.getenv("BGE_MODEL", "BAAI/bge-small-zh-v1.5")
    chroma_path: Path = Path(os.getenv("CHROMA_PATH", str(RUNTIME_DIR / "chroma")))
    collection_name: str = os.getenv("CHROMA_COLLECTION", "medical_knowledge_bge")
    monitor_db: Path = Path(os.getenv("MONITOR_DB", str(RUNTIME_DIR / "monitoring.db")))
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_input_cost_per_1m: float = float(os.getenv("LLM_INPUT_COST_PER_1M", "0"))
    llm_output_cost_per_1m: float = float(os.getenv("LLM_OUTPUT_COST_PER_1M", "0"))
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "600"))
    request_timeout: float = float(os.getenv("REQUEST_TIMEOUT", "30"))


settings = Settings()
