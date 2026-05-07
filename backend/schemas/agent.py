from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


TrainingMode = Literal["speed", "deep"]
SessionMode = Literal["qa", "training"]
CoachState = Literal["GOAL_SET", "TOPIC_PICK", "ASK", "WAIT_ANSWER", "EVALUATE", "DECIDE_NEXT", "SUMMARY_READY", "ANSWER_READY"]
NextAction = Literal["FOLLOW_UP", "NEXT_QUESTION", "SWITCH_TOPIC", "SUMMARY"]
FollowUpType = Literal["none", "clarify", "repair", "deepen"]
AnswerQuality = Literal["poor", "fair", "good"]
CoverageLevel = Literal["low", "medium", "high"]
RiskLevel = Literal["low", "medium", "high"]
ClarityLevel = Literal["weak", "okay", "strong"]
ConfidenceLevel = Literal["low", "medium", "high"]


class FilterPayload(BaseModel):
    company: str = ""
    role: str = ""


class LlmConfigPayload(BaseModel):
    providerId: str = ""
    model: str = ""
    baseUrl: str = ""
    apiKey: str = ""


class AgentClassifyRequest(BaseModel):
    question: str = Field(min_length=1)
    sessionId: Optional[str] = None
    previousQuestion: str = ""
    previousAnswer: str = ""


class AgentClassifyResponse(BaseModel):
    ok: bool = True
    domain: str
    tags: List[str]
    intent: str
    matchedRules: List[str] = Field(default_factory=list)


class AgentRetrieveRequest(BaseModel):
    question: str = Field(min_length=1)
    domain: str = ""
    tags: List[str] = Field(default_factory=list)
    filters: FilterPayload = Field(default_factory=FilterPayload)
    limit: int = 5


class AgentSource(BaseModel):
    type: Literal["post", "question", "knowledge"]
    id: str
    title: str
    summary: str = ""
    company: str = ""
    role: str = ""
    score: float = 0.0
    reason: str = ""


class AgentRetrieveResponse(BaseModel):
    ok: bool = True
    domain: str
    tags: List[str]
    sources: List[AgentSource]
    contextInsufficient: bool = False


class AgentAnswerRequest(BaseModel):
    question: str = Field(min_length=1)
    llmConfig: Optional[LlmConfigPayload] = None
    filters: FilterPayload = Field(default_factory=FilterPayload)
    topN: int = 5


class AgentSection(BaseModel):
    title: str
    content: str


class AgentAnswerResponse(BaseModel):
    ok: bool = True
    sessionId: str
    mode: SessionMode = "qa"
    state: str = "ANSWER_READY"
    domain: str
    tags: List[str]
    summary: str
    sections: List[AgentSection]
    projectExample: str = ""
    pitfalls: List[str] = Field(default_factory=list)
    followUps: List[str] = Field(default_factory=list)
    sources: List[AgentSource] = Field(default_factory=list)
    contextInsufficient: bool = False


class AgentFollowUpRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    question: str = Field(min_length=1)
    llmConfig: Optional[LlmConfigPayload] = None


class AgentGoalPayload(BaseModel):
    company: str = ""
    role: str = ""
    mode: TrainingMode = "speed"
    preferredTopics: List[str] = Field(default_factory=list)


class TopicProgressPayload(BaseModel):
    topic: str
    sourceType: str = ""
    priority: int = 0
    questionCount: int = 0
    poorCount: int = 0
    fairCount: int = 0
    goodCount: int = 0
    followUpCount: int = 0
    completed: bool = False


class ActiveQuestionPayload(BaseModel):
    topic: str = ""
    prompt: str = ""
    sourceHints: List[AgentSource] = Field(default_factory=list)
    questionNumber: int = 1
    followUpCount: int = 0
    kind: str = "main"


class KeyPointCoveragePayload(BaseModel):
    coverageLevel: CoverageLevel = "low"
    expectedKeyPoints: List[str] = Field(default_factory=list)
    hitKeyPoints: List[str] = Field(default_factory=list)
    missingKeyPoints: List[str] = Field(default_factory=list)


class AgentEvaluationFeedbackPayload(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    suggestion: str = ""


class AgentEvaluationPayload(BaseModel):
    answerQuality: AnswerQuality = "fair"
    keyPointCoverage: KeyPointCoveragePayload = Field(default_factory=KeyPointCoveragePayload)
    factualRisk: RiskLevel = "low"
    expressionClarity: ClarityLevel = "okay"
    shouldFollowUp: FollowUpType = "none"
    weaknessTags: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = "medium"
    feedback: AgentEvaluationFeedbackPayload = Field(default_factory=AgentEvaluationFeedbackPayload)


class ReviewTopicPerformancePayload(BaseModel):
    topic: str
    questionCount: int = 0
    result: str = ""


class ReviewSummaryPayload(BaseModel):
    headline: str = ""
    topicPerformance: List[ReviewTopicPerformancePayload] = Field(default_factory=list)
    nextSuggestion: str = ""


class AgentTrainingStartRequest(BaseModel):
    goal: AgentGoalPayload = Field(default_factory=AgentGoalPayload)
    filters: FilterPayload = Field(default_factory=FilterPayload)


class AgentTrainingAnswerRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    llmConfig: Optional[LlmConfigPayload] = None


class AgentTrainingAdvanceRequest(BaseModel):
    sessionId: str = Field(min_length=1)
    action: NextAction


class AgentSessionSummaryResponse(BaseModel):
    id: str
    title: str
    question: str
    mode: SessionMode = "qa"
    state: str = ""
    domain: str = ""
    tags: List[str] = Field(default_factory=list)
    goal: AgentGoalPayload = Field(default_factory=AgentGoalPayload)
    updatedAt: str


class AgentMessageResponse(BaseModel):
    role: str
    content: dict
    createdAt: str


class AgentAttemptResponse(BaseModel):
    id: str
    topic: str
    question: str
    answer: str
    evaluation: AgentEvaluationPayload = Field(default_factory=AgentEvaluationPayload)
    nextAction: str = ""
    createdAt: str


class AgentSessionDetailResponse(BaseModel):
    ok: bool = True
    session: AgentSessionSummaryResponse
    messages: List[AgentMessageResponse]
    activeQuestion: Optional[ActiveQuestionPayload] = None
    topicProgress: List[TopicProgressPayload] = Field(default_factory=list)
    reviewSummary: Optional[ReviewSummaryPayload] = None
    lastEvaluation: Optional[AgentEvaluationPayload] = None
    suggestedAction: str = ""
    attempts: List[AgentAttemptResponse] = Field(default_factory=list)
    sources: List[AgentSource] = Field(default_factory=list)


class AgentTrainingSessionResponse(BaseModel):
    ok: bool = True
    sessionId: str
    mode: SessionMode = "training"
    state: str
    goal: AgentGoalPayload
    topicProgress: List[TopicProgressPayload] = Field(default_factory=list)
    activeQuestion: Optional[ActiveQuestionPayload] = None
    lastEvaluation: Optional[AgentEvaluationPayload] = None
    suggestedAction: str = ""
    reviewSummary: Optional[ReviewSummaryPayload] = None
    availableActions: List[NextAction] = Field(default_factory=list)
    attemptCount: int = 0
    sources: List[AgentSource] = Field(default_factory=list)
