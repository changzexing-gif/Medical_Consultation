from __future__ import annotations

import json
from typing import Any

import httpx

from core.config import settings
from core.monitoring import Event, monitor


class LLMClient:
    """最小 OpenAI-compatible 客户端；无 Key 时由 Agent 使用规则模式。"""

    @property
    def enabled(self) -> bool:
        return bool(settings.llm_api_key)

    def structured(self, system: str, user: str, *, agent: str, query_id: str, user_id: str) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("LLM_API_KEY 未配置")
        payload = {
            "model": settings.llm_model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }
        with monitor.timed("llm", agent, query_id=query_id, user_id=user_id):
            response = httpx.post(
                settings.llm_base_url.rstrip("/") + "/chat/completions",
                headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                json=payload, timeout=settings.request_timeout,
            )
            response.raise_for_status()
            body = response.json()
            usage = body.get("usage", {})
            content = body["choices"][0]["message"]["content"]
        monitor.record(Event(
            "llm_usage", agent=agent, query_id=query_id, user_id=user_id,
            prompt_tokens=int(usage.get("prompt_tokens", 0)),
            completion_tokens=int(usage.get("completion_tokens", 0)),
            cost_usd=(
                int(usage.get("prompt_tokens", 0)) * settings.llm_input_cost_per_1m
                + int(usage.get("completion_tokens", 0)) * settings.llm_output_cost_per_1m
            ) / 1_000_000,
            metadata={"model": settings.llm_model},
        ))
        return json.loads(content)


llm_client = LLMClient()
