import { generateTopicBank } from "../domain/ai.js";

export function AnalysisPage({ analysis, llmConfig, analysisState, setAnalysisState }) {
  async function runTopicBank() {
    if (!llmConfig.apiKey) {
      setAnalysisState({ ...analysisState, status: "请先在大模型页配置 API Key。" });
      return;
    }
    setAnalysisState({ ...analysisState, loading: true, status: "正在生成专题题库..." });
    try {
      const result = await generateTopicBank(llmConfig, analysis);
      setAnalysisState({ ...analysisState, loading: false, status: "专题题库已生成。", topicBank: result });
    } catch (error) {
      setAnalysisState({ ...analysisState, loading: false, status: error.message });
    }
  }

  return (
    <>
      <div className="section-head">
        <h2>面经分析</h2>
        <p className="page-description">基于帖子库内容做规则分析，帮助你快速看出公司和岗位的高频准备方向。</p>
      </div>
      <div className="analysis-layout">
        <section className="panel">
          <div className="panel-title">
            <h3>高频主题</h3>
            <p>按照关键词规则统计，不依赖外部模型。</p>
          </div>
          {analysis.topics.length ? (
            <div className="topic-grid">
              {analysis.topics.map((topic) => (
                <div className="topic-card" key={topic.name}>
                  <div className="topic-card-head">
                    <h4>{topic.name}</h4>
                    <strong>{topic.count}</strong>
                  </div>
                  <div className="tags">
                    {topic.keys.slice(0, 4).map((key) => <span className="tag" key={key}>{key}</span>)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">暂无可分析数据。</div>
          )}
        </section>

        <section className="panel">
          <div className="panel-title">
            <h3>典型问题</h3>
            <p>从正文中提取“怎么、如何、为什么、设计”等问题句。</p>
          </div>
          {analysis.questions.length ? (
            <ol className="rank-list">
              {analysis.questions.slice(0, 12).map((item, index) => <li key={`${item.text}-${index}`}>{item.text}</li>)}
            </ol>
          ) : (
            <div className="empty-state">还没有识别到问题句。</div>
          )}
        </section>

        <section className="panel">
          <div className="panel-title">
            <h3>复习观察</h3>
          </div>
          <ul className="insight-list">
            {analysis.flows.map((item) => <li key={item}>{item}</li>)}
          </ul>
        </section>

        <section className="panel">
          <div className="panel-title">
            <h3>AI 专题题库</h3>
            <p>可选能力，会使用你配置的大模型把分析结果整理成专题题库。</p>
          </div>
          <button type="button" disabled={analysisState.loading} onClick={runTopicBank}>
            {analysisState.loading ? "生成中..." : "生成专题题库"}
          </button>
          <p className="inline-hint">{analysisState.status}</p>
          {analysisState.topicBank?.groups ? (
            <div className="topic-bank-list textarea-wrap">
              {analysisState.topicBank.groups.map((group) => (
                <div className="topic-bank-card" key={group.title}>
                  <h4>{group.title}</h4>
                  <ol className="rank-list">
                    {(group.questions || []).map((item) => (
                      <li key={item.question}>
                        <strong>{item.question}</strong>
                        <p>{item.focus} · {item.answerHint}</p>
                      </li>
                    ))}
                  </ol>
                </div>
              ))}
            </div>
          ) : null}
        </section>

        <section className="panel full-span">
          <div className="panel-title">
            <h3>Markdown 报告</h3>
          </div>
          <pre className="report-box">{analysis.report}</pre>
        </section>
      </div>
    </>
  );
}
