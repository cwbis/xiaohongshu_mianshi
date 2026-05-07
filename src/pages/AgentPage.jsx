import { useEffect, useMemo, useState } from "react";
import {
  advanceTrainingSession,
  generateAgentAnswer,
  generateFollowUp,
  getAgentSession,
  listAgentSessions,
  startTrainingSession,
  submitTrainingAnswer,
} from "../api/agent.js";

function createQaState() {
  return {
    question: "Redis 扣减库存时，怎么保证缓存和数据库的一致性？",
    followUp: "",
    loading: false,
    status: "",
    result: null,
    sessions: [],
    activeSessionId: "",
  };
}

function createTrainingState(filters) {
  return {
    goalCompany: filters.company || "",
    goalRole: filters.role || "",
    trainingMode: "speed",
    preferredTopics: "MySQL, Redis",
    answer: "",
    loading: false,
    status: "",
    activeSessionId: "",
    activeQuestion: null,
    topicProgress: [],
    lastEvaluation: null,
    suggestedAction: "",
    availableActions: [],
    reviewSummary: null,
    attemptCount: 0,
    sources: [],
    sessions: [],
  };
}

function parseTopicInput(value) {
  return String(value || "")
    .split(/[,\n，]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function toLabel(action) {
  switch (action) {
    case "FOLLOW_UP":
      return "继续追问";
    case "NEXT_QUESTION":
      return "下一题";
    case "SWITCH_TOPIC":
      return "切专题";
    case "SUMMARY":
      return "生成小结";
    default:
      return action;
  }
}

export function AgentPage({ llmConfig, filters }) {
  const [mode, setMode] = useState("qa");
  const [qaState, setQaState] = useState(createQaState);
  const [trainingState, setTrainingState] = useState(() => createTrainingState(filters));

  useEffect(() => {
    let cancelled = false;
    async function loadSessions() {
      try {
        const sessions = await listAgentSessions(20, mode === "qa" ? "qa" : "training");
        if (cancelled) return;
        if (mode === "qa") {
          setQaState((current) => ({ ...current, sessions: Array.isArray(sessions) ? sessions : [] }));
        } else {
          setTrainingState((current) => ({ ...current, sessions: Array.isArray(sessions) ? sessions : [] }));
        }
      } catch (error) {
        if (cancelled) return;
        if (mode === "qa") {
          setQaState((current) => ({ ...current, status: error.message }));
        } else {
          setTrainingState((current) => ({ ...current, status: error.message }));
        }
      }
    }
    loadSessions();
    return () => {
      cancelled = true;
    };
  }, [mode]);

  useEffect(() => {
    setTrainingState((current) => ({
      ...current,
      goalCompany: current.goalCompany || filters.company || "",
      goalRole: current.goalRole || filters.role || "",
    }));
  }, [filters.company, filters.role]);

  const trainingGoalPreview = useMemo(
    () => ({
      company: trainingState.goalCompany || filters.company || "",
      role: trainingState.goalRole || filters.role || "",
      mode: trainingState.trainingMode,
      preferredTopics: parseTopicInput(trainingState.preferredTopics),
    }),
    [trainingState.goalCompany, trainingState.goalRole, trainingState.trainingMode, trainingState.preferredTopics, filters.company, filters.role]
  );

  async function refreshSessions(currentMode) {
    const sessions = await listAgentSessions(20, currentMode);
    if (currentMode === "qa") {
      setQaState((current) => ({ ...current, sessions: Array.isArray(sessions) ? sessions : current.sessions }));
    } else {
      setTrainingState((current) => ({ ...current, sessions: Array.isArray(sessions) ? sessions : current.sessions }));
    }
  }

  async function askQuestion() {
    if (!qaState.question.trim()) {
      setQaState((current) => ({ ...current, status: "请先输入一个面试问题。" }));
      return;
    }
    setQaState((current) => ({ ...current, loading: true, status: "正在生成结构化回答..." }));
    try {
      const result = await generateAgentAnswer({
        question: qaState.question,
        llmConfig,
        filters,
        topN: 5,
      });
      await refreshSessions("qa");
      setQaState((current) => ({
        ...current,
        loading: false,
        status: result.contextInsufficient ? "已生成回答，但当前本地证据较少，建议继续补充帖子库。" : "回答已生成。",
        result,
        activeSessionId: result.sessionId,
        followUp: "",
      }));
    } catch (error) {
      setQaState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  async function askFollowUp() {
    if (!qaState.activeSessionId) {
      setQaState((current) => ({ ...current, status: "请先生成首轮回答。" }));
      return;
    }
    if (!qaState.followUp.trim()) {
      setQaState((current) => ({ ...current, status: "请先输入追问内容。" }));
      return;
    }
    setQaState((current) => ({ ...current, loading: true, status: "正在生成追问回答..." }));
    try {
      const result = await generateFollowUp({
        sessionId: qaState.activeSessionId,
        question: qaState.followUp,
        llmConfig,
      });
      const detail = await getAgentSession(qaState.activeSessionId);
      setQaState((current) => ({
        ...current,
        loading: false,
        status: "追问已生成。",
        result: { ...result, messages: detail.messages || [] },
        followUp: "",
      }));
    } catch (error) {
      setQaState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  async function loadQaSession(sessionId) {
    setQaState((current) => ({ ...current, loading: true, status: "正在加载历史问答..." }));
    try {
      const detail = await getAgentSession(sessionId);
      const lastAssistant = [...(detail.messages || [])].reverse().find((item) => item.role === "assistant");
      setQaState((current) => ({
        ...current,
        loading: false,
        status: "历史问答已加载。",
        activeSessionId: sessionId,
        result: lastAssistant ? { ...lastAssistant.content, sessionId, messages: detail.messages } : current.result,
      }));
    } catch (error) {
      setQaState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  async function beginTraining() {
    setTrainingState((current) => ({ ...current, loading: true, status: "正在建立训练目标并生成第一题..." }));
    try {
      const result = await startTrainingSession({
        goal: trainingGoalPreview,
        filters,
      });
      await refreshSessions("training");
      setTrainingState((current) => ({
        ...current,
        loading: false,
        status: "训练模式已开始。",
        activeSessionId: result.sessionId,
        activeQuestion: result.activeQuestion,
        topicProgress: result.topicProgress || [],
        lastEvaluation: result.lastEvaluation,
        suggestedAction: result.suggestedAction || "",
        availableActions: result.availableActions || [],
        reviewSummary: result.reviewSummary,
        attemptCount: result.attemptCount || 0,
        sources: result.sources || [],
        answer: "",
      }));
    } catch (error) {
      setTrainingState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  async function submitTraining() {
    if (!trainingState.activeSessionId) {
      setTrainingState((current) => ({ ...current, status: "请先开始一轮训练。" }));
      return;
    }
    if (!trainingState.answer.trim()) {
      setTrainingState((current) => ({ ...current, status: "请先输入你的作答内容。" }));
      return;
    }
    setTrainingState((current) => ({ ...current, loading: true, status: "正在评估你的回答..." }));
    try {
      const result = await submitTrainingAnswer({
        sessionId: trainingState.activeSessionId,
        answer: trainingState.answer,
        llmConfig,
      });
      await refreshSessions("training");
      setTrainingState((current) => ({
        ...current,
        loading: false,
        status: "已完成本题评估，可以继续推进下一步。",
        activeQuestion: result.activeQuestion,
        topicProgress: result.topicProgress || [],
        lastEvaluation: result.lastEvaluation,
        suggestedAction: result.suggestedAction || "",
        availableActions: result.availableActions || [],
        reviewSummary: result.reviewSummary,
        attemptCount: result.attemptCount || current.attemptCount,
        sources: result.sources || current.sources,
      }));
    } catch (error) {
      setTrainingState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  async function advanceTraining(action) {
    if (!trainingState.activeSessionId) {
      return;
    }
    setTrainingState((current) => ({ ...current, loading: true, status: `正在执行${toLabel(action)}...` }));
    try {
      const result = await advanceTrainingSession({
        sessionId: trainingState.activeSessionId,
        action,
      });
      await refreshSessions("training");
      setTrainingState((current) => ({
        ...current,
        loading: false,
        status: action === "SUMMARY" ? "已生成阶段小结。" : "训练已推进到下一步。",
        activeQuestion: result.activeQuestion,
        topicProgress: result.topicProgress || [],
        lastEvaluation: result.lastEvaluation,
        suggestedAction: result.suggestedAction || "",
        availableActions: result.availableActions || [],
        reviewSummary: result.reviewSummary,
        attemptCount: result.attemptCount || current.attemptCount,
        sources: result.sources || [],
        answer: action === "SUMMARY" ? current.answer : "",
      }));
    } catch (error) {
      setTrainingState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  async function loadTrainingSession(sessionId) {
    setTrainingState((current) => ({ ...current, loading: true, status: "正在加载训练会话..." }));
    try {
      const detail = await getAgentSession(sessionId);
      setTrainingState((current) => ({
        ...current,
        loading: false,
        status: "训练会话已加载。",
        activeSessionId: sessionId,
        goalCompany: detail.session.goal?.company || current.goalCompany,
        goalRole: detail.session.goal?.role || current.goalRole,
        trainingMode: detail.session.goal?.mode || current.trainingMode,
        preferredTopics: (detail.session.goal?.preferredTopics || []).join(", "),
        activeQuestion: detail.activeQuestion || null,
        topicProgress: detail.topicProgress || [],
        lastEvaluation: detail.lastEvaluation || null,
        suggestedAction: detail.suggestedAction || "",
        availableActions: detail.suggestedAction ? [detail.suggestedAction] : [],
        reviewSummary: detail.reviewSummary || null,
        attemptCount: (detail.attempts || []).length,
        sources: detail.sources || [],
      }));
    } catch (error) {
      setTrainingState((current) => ({ ...current, loading: false, status: error.message }));
    }
  }

  return (
    <>
      <div className="section-head">
        <h2>面试 Agent</h2>
        <p className="page-description">
          这里保留了原来的问答模式，也新增了教练式训练模式。你可以先快速问答，也可以围绕公司、岗位和专题进入连续训练。
        </p>
      </div>

      <div className="agent-mode-switch">
        <button type="button" className={`route-link ${mode === "qa" ? "active" : ""}`} onClick={() => setMode("qa")}>
          问答模式
        </button>
        <button type="button" className={`route-link ${mode === "training" ? "active" : ""}`} onClick={() => setMode("training")}>
          训练模式
        </button>
      </div>

      {mode === "qa" ? (
        <div className="agent-layout">
          <section className="panel agent-panel">
            <div className="panel-title">
              <h3>快速问答</h3>
              <p>延续现有单轮问答链路：分类、检索、结构化回答，再决定是否继续追问。</p>
            </div>
            <div className="agent-filter-pills">
              <span>公司：{filters.company || "全部"}</span>
              <span>岗位：{filters.role || "全部"}</span>
            </div>
            <textarea
              className="compact-area agent-question-box"
              value={qaState.question}
              onChange={(event) => setQaState((current) => ({ ...current, question: event.target.value }))}
            />
            <div className="actions">
              <button type="button" disabled={qaState.loading} onClick={askQuestion}>
                {qaState.loading ? "生成中..." : "生成面试回答"}
              </button>
            </div>
            <p className="inline-hint">{qaState.status}</p>
          </section>

          <section className="panel agent-panel">
            <div className="panel-title">
              <h3>问答历史</h3>
              <p>这里只展示问答模式下的最近会话，避免和训练记录混在一起。</p>
            </div>
            <div className="agent-session-list">
              {qaState.sessions.length ? (
                qaState.sessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    className={`agent-session-card ${qaState.activeSessionId === session.id ? "active" : ""}`}
                    onClick={() => loadQaSession(session.id)}
                  >
                    <strong>{session.title}</strong>
                    <span>{session.domain || "通用后端面试"}</span>
                  </button>
                ))
              ) : (
                <div className="empty-state">还没有问答历史。</div>
              )}
            </div>
          </section>

          <section className="panel full-span agent-answer-panel">
            <div className="panel-title">
              <h3>回答结果</h3>
              <p>结果会保留结构化回答、项目表达、易错点和来源证据，方便继续追问。</p>
            </div>
            {qaState.result ? (
              <div className="agent-answer-grid">
                <div className="agent-answer-main">
                  <div className="agent-tag-row">
                    <span className="agent-domain-chip">{qaState.result.domain || "通用后端面试"}</span>
                    {(qaState.result.tags || []).map((tag) => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                  <div className="agent-summary-card">
                    <h4>一句话总结</h4>
                    <p>{qaState.result.summary}</p>
                  </div>
                  <div className="agent-sections">
                    {(qaState.result.sections || []).map((section) => (
                      <article key={`${section.title}-${section.content}`} className="agent-section-card">
                        <h4>{section.title}</h4>
                        <p>{section.content}</p>
                      </article>
                    ))}
                  </div>
                  {qaState.result.projectExample ? (
                    <div className="agent-extra-card">
                      <h4>项目化表达</h4>
                      <p>{qaState.result.projectExample}</p>
                    </div>
                  ) : null}
                  {qaState.result.pitfalls?.length ? (
                    <div className="agent-extra-card">
                      <h4>易错点</h4>
                      <ul className="agent-plain-list">
                        {qaState.result.pitfalls.map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    </div>
                  ) : null}
                  {qaState.result.followUps?.length ? (
                    <div className="agent-extra-card">
                      <h4>可能追问</h4>
                      <ul className="agent-plain-list">
                        {qaState.result.followUps.map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    </div>
                  ) : null}
                  <div className="agent-follow-up-box">
                    <h4>继续追问</h4>
                    <textarea
                      className="compact-area"
                      value={qaState.followUp}
                      onChange={(event) => setQaState((current) => ({ ...current, followUp: event.target.value }))}
                      placeholder="例如：为什么你会优先用延迟双删而不是先删缓存？"
                    />
                    <div className="actions">
                      <button type="button" disabled={qaState.loading} onClick={askFollowUp}>
                        {qaState.loading ? "追问中..." : "提交追问"}
                      </button>
                    </div>
                  </div>
                </div>

                <aside className="agent-sources-side">
                  <h4>检索来源</h4>
                  {(qaState.result.sources || []).length ? (
                    <div className="agent-source-list">
                      {qaState.result.sources.map((source) => (
                        <article key={`${source.type}-${source.id}`} className="agent-source-card">
                          <span className="agent-source-type">{source.type}</span>
                          <strong>{source.title}</strong>
                          <p>{source.summary || source.reason}</p>
                          <small>{[source.company, source.role].filter(Boolean).join(" / ") || source.reason}</small>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">这一轮没有命中本地来源。</div>
                  )}
                </aside>
              </div>
            ) : (
              <div className="empty-state">先提一个技术问题，Agent 会生成结构化回答。</div>
            )}
          </section>
        </div>
      ) : (
        <div className="agent-layout">
          <section className="panel agent-panel">
            <div className="panel-title">
              <h3>训练目标</h3>
              <p>训练模式会先收集公司、岗位、训练节奏和专题偏好，再主动出题、评估和推进下一步。</p>
            </div>
            <div className="agent-training-form">
              <label>
                <span>目标公司</span>
                <input value={trainingState.goalCompany} onChange={(event) => setTrainingState((current) => ({ ...current, goalCompany: event.target.value }))} />
              </label>
              <label>
                <span>目标岗位</span>
                <input value={trainingState.goalRole} onChange={(event) => setTrainingState((current) => ({ ...current, goalRole: event.target.value }))} />
              </label>
              <label>
                <span>训练模式</span>
                <select value={trainingState.trainingMode} onChange={(event) => setTrainingState((current) => ({ ...current, trainingMode: event.target.value }))}>
                  <option value="speed">高频速刷</option>
                  <option value="deep">深度追问</option>
                </select>
              </label>
              <label className="full-span">
                <span>专题偏好</span>
                <textarea
                  className="compact-area agent-training-input"
                  value={trainingState.preferredTopics}
                  onChange={(event) => setTrainingState((current) => ({ ...current, preferredTopics: event.target.value }))}
                  placeholder="例如：MySQL, Redis, 场景设计"
                />
              </label>
            </div>
            <div className="agent-filter-pills">
              <span>当前帖子筛选公司：{filters.company || "全部"}</span>
              <span>当前帖子筛选岗位：{filters.role || "全部"}</span>
            </div>
            <div className="actions">
              <button type="button" disabled={trainingState.loading} onClick={beginTraining}>
                {trainingState.loading ? "准备中..." : "开始训练"}
              </button>
            </div>
            <p className="inline-hint">{trainingState.status}</p>
          </section>

          <section className="panel agent-panel">
            <div className="panel-title">
              <h3>训练历史</h3>
              <p>这里保存训练模式下的目标和推进记录，方便继续刷题或回看阶段复盘。</p>
            </div>
            <div className="agent-session-list">
              {trainingState.sessions.length ? (
                trainingState.sessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    className={`agent-session-card ${trainingState.activeSessionId === session.id ? "active" : ""}`}
                    onClick={() => loadTrainingSession(session.id)}
                  >
                    <strong>{session.title}</strong>
                    <span>{session.goal?.mode === "deep" ? "深度追问" : "高频速刷"}</span>
                  </button>
                ))
              ) : (
                <div className="empty-state">还没有训练会话。</div>
              )}
            </div>
          </section>

          <section className="panel full-span agent-answer-panel">
            <div className="panel-title">
              <h3>训练工作台</h3>
              <p>最小训练闭环是：设置目标、主动出题、提交作答、评估回答，再决定继续追问、下一题、切专题或生成小结。</p>
            </div>

            <div className="agent-training-grid">
              <div className="agent-answer-main">
                <div className="agent-summary-card">
                  <h4>当前训练目标</h4>
                  <p>
                    {(trainingGoalPreview.company || "未指定公司")} / {(trainingGoalPreview.role || "未指定岗位")} /{" "}
                    {trainingGoalPreview.mode === "deep" ? "深度追问" : "高频速刷"}
                  </p>
                  <small>专题偏好：{trainingGoalPreview.preferredTopics.join("、") || "将根据本地高频题自动选择"}</small>
                </div>

                <div className="agent-extra-card">
                  <h4>主动出题</h4>
                  {trainingState.activeQuestion ? (
                    <>
                      <div className="agent-tag-row">
                        <span className="agent-domain-chip">{trainingState.activeQuestion.topic}</span>
                        <span className="agent-source-type">
                          第 {trainingState.activeQuestion.questionNumber} 题
                        </span>
                        {trainingState.activeQuestion.followUpCount ? (
                          <span className="agent-source-type">追问 {trainingState.activeQuestion.followUpCount}</span>
                        ) : null}
                      </div>
                      <p>{trainingState.activeQuestion.prompt}</p>
                    </>
                  ) : (
                    <p>开始训练后，这里会出现当前要作答的问题。</p>
                  )}
                </div>

                <div className="agent-follow-up-box">
                  <h4>你的作答</h4>
                  <textarea
                    className="compact-area agent-question-box"
                    value={trainingState.answer}
                    onChange={(event) => setTrainingState((current) => ({ ...current, answer: event.target.value }))}
                    placeholder="先按你真实面试时会说的方式回答，后面再看 Agent 的评估和下一步建议。"
                  />
                  <div className="actions">
                    <button type="button" disabled={trainingState.loading || !trainingState.activeSessionId} onClick={submitTraining}>
                      {trainingState.loading ? "评估中..." : "提交作答"}
                    </button>
                  </div>
                </div>

                {trainingState.lastEvaluation ? (
                  <div className="agent-evaluation-stack">
                    <div className="agent-extra-card">
                      <h4>评估结果</h4>
                      <div className="agent-tag-row">
                        <span className="agent-source-type">质量：{trainingState.lastEvaluation.answerQuality}</span>
                        <span className="agent-source-type">覆盖：{trainingState.lastEvaluation.keyPointCoverage?.coverageLevel}</span>
                        <span className="agent-source-type">风险：{trainingState.lastEvaluation.factualRisk}</span>
                        <span className="agent-source-type">表达：{trainingState.lastEvaluation.expressionClarity}</span>
                      </div>
                    </div>
                    <div className="agent-extra-card">
                      <h4>你答到了什么</h4>
                      <ul className="agent-plain-list">
                        {(trainingState.lastEvaluation.feedback?.strengths || []).map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    </div>
                    <div className="agent-extra-card">
                      <h4>还欠缺什么</h4>
                      <ul className="agent-plain-list">
                        {(trainingState.lastEvaluation.feedback?.gaps || []).map((item) => <li key={item}>{item}</li>)}
                        {(trainingState.lastEvaluation.keyPointCoverage?.missingKeyPoints || []).map((item) => <li key={item}>{item}</li>)}
                      </ul>
                    </div>
                    <div className="agent-extra-card">
                      <h4>下一步建议</h4>
                      <p>{trainingState.lastEvaluation.feedback?.suggestion || "根据建议继续推进下一步。"}</p>
                      <p className="inline-hint">当前推荐动作：{toLabel(trainingState.suggestedAction || "NEXT_QUESTION")}</p>
                    </div>
                    {trainingState.availableActions.length ? (
                      <div className="agent-next-actions">
                        {trainingState.availableActions.map((action) => (
                          <button key={action} type="button" disabled={trainingState.loading} onClick={() => advanceTraining(action)}>
                            {toLabel(action)}
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}

                {trainingState.reviewSummary?.headline ? (
                  <div className="agent-summary-card">
                    <h4>阶段小结</h4>
                    <p>{trainingState.reviewSummary.headline}</p>
                    <ul className="agent-plain-list">
                      {(trainingState.reviewSummary.topicPerformance || []).map((item) => (
                        <li key={item.topic}>
                          {item.topic}：{item.questionCount} 题，{item.result}
                        </li>
                      ))}
                    </ul>
                    <p>{trainingState.reviewSummary.nextSuggestion}</p>
                  </div>
                ) : null}
              </div>

              <aside className="agent-sources-side">
                <div className="agent-extra-card">
                  <h4>训练进度</h4>
                  <p>已完成 {trainingState.attemptCount} 题</p>
                  <div className="agent-progress-list">
                    {(trainingState.topicProgress || []).map((item) => (
                      <article key={item.topic} className={`agent-progress-card ${item.completed ? "done" : ""}`}>
                        <strong>{item.topic}</strong>
                        <small>{item.sourceType || "local_hot"}</small>
                        <p>
                          题数 {item.questionCount || 0} / good {item.goodCount || 0} / fair {item.fairCount || 0} / poor {item.poorCount || 0}
                        </p>
                      </article>
                    ))}
                  </div>
                </div>

                <div className="agent-extra-card">
                  <h4>本题证据</h4>
                  {(trainingState.sources || []).length ? (
                    <div className="agent-source-list">
                      {trainingState.sources.map((source) => (
                        <article key={`${source.type}-${source.id}`} className="agent-source-card">
                          <span className="agent-source-type">{source.type}</span>
                          <strong>{source.title}</strong>
                          <p>{source.summary || source.reason}</p>
                          <small>{[source.company, source.role].filter(Boolean).join(" / ") || source.reason}</small>
                        </article>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">当前题没有额外命中的本地证据。</div>
                  )}
                </div>
              </aside>
            </div>
          </section>
        </div>
      )}
    </>
  );
}
