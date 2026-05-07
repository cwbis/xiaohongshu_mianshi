from __future__ import annotations

from typing import Optional

from backend.repositories.db import StorageRepository


class SessionRepository:
    def __init__(self, storage: StorageRepository):
        self.storage = storage

    def create(self, **kwargs) -> str:
        return self.storage.create_session(**kwargs)

    def append(self, session_id: str, question: str, answer_payload: dict) -> None:
        self.storage.append_session_messages(session_id, question, answer_payload)

    def get(self, session_id: str) -> Optional[dict]:
        return self.storage.get_session(session_id)

    def list(self, limit: int = 20, mode: Optional[str] = None) -> list[dict]:
        return self.storage.list_sessions(limit=limit, mode=mode)
