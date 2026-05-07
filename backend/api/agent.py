from typing import Optional

from fastapi import APIRouter

from backend.config import DB_PATH
from backend.errors import ApiError
from backend.repositories.db import StorageRepository
from backend.repositories.knowledge_repo import KnowledgeRepository
from backend.repositories.session_repo import SessionRepository
from backend.schemas.agent import (
    AgentAnswerRequest,
    AgentAnswerResponse,
    AgentClassifyRequest,
    AgentClassifyResponse,
    AgentFollowUpRequest,
    AgentRetrieveRequest,
    AgentRetrieveResponse,
    AgentSessionDetailResponse,
    AgentSessionSummaryResponse,
    AgentTrainingAdvanceRequest,
    AgentTrainingAnswerRequest,
    AgentTrainingSessionResponse,
    AgentTrainingStartRequest,
)
from backend.services.agent_service import AgentService
from backend.services.llm_service import LlmService
from backend.services.retrieval_service import RetrievalService


router = APIRouter()
storage = StorageRepository(DB_PATH)
knowledge_repo = KnowledgeRepository(storage)
session_repo = SessionRepository(storage)
retrieval_service = RetrievalService(knowledge_repo)
llm_service = LlmService()
agent_service = AgentService(
    storage=storage,
    retrieval_service=retrieval_service,
    llm_service=llm_service,
    session_repo=session_repo,
)


@router.post("/api/agent/classify", response_model=AgentClassifyResponse)
def classify(payload: AgentClassifyRequest):
    result = agent_service.classify(
        payload.question,
        previous_question=payload.previousQuestion,
        previous_answer=payload.previousAnswer,
    )
    return {"ok": True, **result}


@router.post("/api/agent/retrieve", response_model=AgentRetrieveResponse)
def retrieve(payload: AgentRetrieveRequest):
    return {
        "ok": True,
        **agent_service.retrieve(
            payload.question,
            payload.domain,
            payload.tags,
            filters=payload.filters.model_dump(),
            limit=payload.limit,
        ),
    }


@router.post("/api/agent/answer", response_model=AgentAnswerResponse)
def answer(payload: AgentAnswerRequest):
    llm_config = payload.llmConfig.model_dump() if payload.llmConfig else storage.get_setting("llmConfig", {})
    return {
        "ok": True,
        **agent_service.answer(
            payload.question,
            llm_config,
            filters=payload.filters.model_dump(),
            top_n=payload.topN,
        ),
    }


@router.post("/api/agent/follow-up", response_model=AgentAnswerResponse)
def follow_up(payload: AgentFollowUpRequest):
    llm_config = payload.llmConfig.model_dump() if payload.llmConfig else storage.get_setting("llmConfig", {})
    return {"ok": True, **agent_service.follow_up(payload.sessionId, payload.question, llm_config)}


@router.post("/api/agent/training/start", response_model=AgentTrainingSessionResponse)
def start_training(payload: AgentTrainingStartRequest):
    return {
        "ok": True,
        **agent_service.start_training(payload.goal.model_dump(), filters=payload.filters.model_dump()),
    }


@router.post("/api/agent/training/answer", response_model=AgentTrainingSessionResponse)
def submit_training_answer(payload: AgentTrainingAnswerRequest):
    llm_config = payload.llmConfig.model_dump() if payload.llmConfig else storage.get_setting("llmConfig", {})
    return {
        "ok": True,
        **agent_service.submit_training_answer(payload.sessionId, payload.answer, llm_config),
    }


@router.post("/api/agent/training/advance", response_model=AgentTrainingSessionResponse)
def advance_training(payload: AgentTrainingAdvanceRequest):
    return {"ok": True, **agent_service.advance_training(payload.sessionId, payload.action)}


@router.get("/api/agent/sessions", response_model=list[AgentSessionSummaryResponse])
def list_sessions(limit: int = 20, mode: Optional[str] = None):
    return session_repo.list(limit=limit, mode=mode)


@router.get("/api/agent/sessions/{session_id}", response_model=AgentSessionDetailResponse)
def get_session(session_id: str):
    result = session_repo.get(session_id)
    if not result:
        raise ApiError("会话不存在。")
    return {"ok": True, **result}
