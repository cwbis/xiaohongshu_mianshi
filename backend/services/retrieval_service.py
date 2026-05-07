from __future__ import annotations

from typing import List, Optional

from backend.repositories.knowledge_repo import KnowledgeRepository


class RetrievalService:
    def __init__(self, repository: KnowledgeRepository):
        self.repository = repository

    def retrieve(self, question: str, domain: str, tags: list[str], filters: Optional[dict] = None, limit: int = 5) -> List[dict]:
        query = " ".join([question, domain, *tags]).strip()
        return self.repository.search(query, filters=filters, limit=limit)
