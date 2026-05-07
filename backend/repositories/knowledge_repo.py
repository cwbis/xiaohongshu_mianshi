from __future__ import annotations

from typing import List, Optional

from backend.repositories.db import StorageRepository


class KnowledgeRepository:
    def __init__(self, storage: StorageRepository):
        self.storage = storage

    def search(self, query: str, filters: Optional[dict] = None, limit: int = 5) -> List[dict]:
        return self.storage.search_context(query, filters=filters, limit=limit)
