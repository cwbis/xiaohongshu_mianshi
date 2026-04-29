import { generateAnswer } from "../domain/ai.js";
import { applyProviderSelection, PROVIDERS } from "../domain/modelPresets.js";

export function LLMPage({ llmConfig, setLLMConfig, llmState, setLLMState, analysis }) {
  function updateProvider(providerId) {
    setLLMConfig(applyProviderSelection(llmConfig, providerId));
  }

  async function askModel() {
    if (!llmConfig.apiKey) {
      setLLMState({ ...llmState, status: "请先填写 API Key。" });
      return;
    }
    if (!llmState.question.trim()) {
      setLLMState({ ...llmState, status: "请先填写问题。" });
      return;
    }
    setLLMState({ ...llmState, loading: true, status: "正在请求大模型..." });
    try {
      const result = await generateAnswer(llmConfig, llmState.question, analysis.report);
      setLLMState({ ...llmState, loading: false, status: "已生成回答。", result });
    } catch (error) {
      setLLMState({ ...llmState, loading: false, status: error.message });
    }
  }

  return (
    <>
      <div className="section-head">
        <h2>大模型辅助</h2>
        <p className="page-description">配置供应商、模型和 Key 后，可以基于帖子库分析生成面试回答。</p>
      </div>
      <div className="page-grid">
        <section className="panel">
          <div className="panel-title">
            <h3>模型配置</h3>
            <p>配置会保存到本地 SQLite 的 settings 表。</p>
          </div>
          <div className="form-grid">
            <label>
              <span>供应商</span>
              <select value={llmConfig.providerId} onChange={(event) => updateProvider(event.target.value)}>
                {PROVIDERS.map((provider) => <option key={provider.id} value={provider.id}>{provider.name}</option>)}
              </select>
            </label>
            <label>
              <span>模型</span>
              <input value={llmConfig.model} onChange={(event) => setLLMConfig({ ...llmConfig, model: event.target.value })} />
            </label>
            <label className="full">
              <span>Base URL</span>
              <input value={llmConfig.baseUrl} onChange={(event) => setLLMConfig({ ...llmConfig, baseUrl: event.target.value })} />
            </label>
            <label className="full">
              <span>API Key</span>
              <input
                type="password"
                value={llmConfig.apiKey}
                onChange={(event) => setLLMConfig({ ...llmConfig, apiKey: event.target.value })}
                placeholder="仅保存到本地数据库"
              />
            </label>
          </div>
        </section>

        <section className="panel">
          <div className="panel-title">
            <h3>提问</h3>
            <p>建议贴近真实面试问题，例如“Redis 扣减库存如何保证一致性”。</p>
          </div>
          <textarea
            className="compact-area"
            value={llmState.question}
            onChange={(event) => setLLMState({ ...llmState, question: event.target.value })}
          />
          <div className="actions textarea-wrap">
            <button type="button" disabled={llmState.loading} onClick={askModel}>
              {llmState.loading ? "生成中..." : "生成答案"}
            </button>
          </div>
          <p className="inline-hint">{llmState.status}</p>
        </section>

        <section className="panel full-span">
          <div className="panel-title">
            <h3>回答结果</h3>
          </div>
          {llmState.result ? (
            <div className="report-box tall">
              <h4>{llmState.result.summary || "回答摘要"}</h4>
              <ol className="answer-list">
                {(llmState.result.answer || []).map((item) => <li key={item}>{item}</li>)}
              </ol>
              {llmState.result.pitfalls?.length ? <p>易错点：{llmState.result.pitfalls.join("；")}</p> : null}
              {llmState.result.followUps?.length ? <p>追问：{llmState.result.followUps.join("；")}</p> : null}
            </div>
          ) : (
            <div className="empty-state">还没有生成回答。</div>
          )}
        </section>
      </div>
    </>
  );
}
