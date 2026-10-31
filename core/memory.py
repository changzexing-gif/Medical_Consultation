from __future__ import annotations

from threading import RLock

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage


class WindowChatMessageHistory(BaseChatMessageHistory):
    """实现 LangChain 历史接口的有界内存存储。"""

    def __init__(self, max_messages: int):
        self.max_messages = max_messages
        self.messages: list[BaseMessage] = []

    def add_messages(self, messages: list[BaseMessage]) -> None:
        self.messages.extend(messages)
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages :]

    def clear(self) -> None:
        self.messages = []


class ConversationStore:
    """基于 LangChain 的多会话历史管理，限制窗口避免上下文无限增长。"""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._sessions: dict[str, WindowChatMessageHistory] = {}
        self._lock = RLock()

    def history(self, session_id: str) -> WindowChatMessageHistory:
        with self._lock:
            return self._sessions.setdefault(session_id, WindowChatMessageHistory(self.max_messages))

    def append(self, session_id: str, user: str, assistant: str) -> None:
        history = self.history(session_id)
        history.add_user_message(user)
        history.add_ai_message(assistant)

    def context(self, session_id: str, turns: int = 5) -> str:
        messages = self.history(session_id).messages[-turns * 2 :]
        labels = {"human": "患者", "ai": "医生"}
        return "\n".join(f"{labels.get(m.type, m.type)}：{m.content}" for m in messages)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)


conversation_store = ConversationStore()
