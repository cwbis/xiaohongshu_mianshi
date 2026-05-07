const routes = [
  { id: "collect", label: "采集", desc: "搜索、刷新、翻页并入库" },
  { id: "library", label: "帖子库", desc: "按公司和岗位浏览面经" },
  { id: "analysis", label: "分析", desc: "沉淀高频题和复习报告" },
  { id: "llm", label: "大模型", desc: "配置模型并生成答案" },
  { id: "agent", label: "面试 Agent", desc: "自动分类、检索与追问" },
];

export function Shell({ route, setRoute, children, summary, runtime }) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <div className="brand-mark">OS</div>
          <div>
            <h1>OfferScope 小红书面经工作台</h1>
            <p className="inline-hint">React 前端 + 本地 SQLite + FastAPI 运行时</p>
          </div>
        </div>
        <div className="topbar-actions">
          <button className="ghost" type="button" onClick={() => window.location.reload()}>
            刷新应用
          </button>
        </div>
      </header>

      <section className="hero-banner">
        <div className="hero-copy">
          <p className="micro-copy">Interview Intelligence</p>
          <h2>把零散面经整理成可复盘、可追问、可输出的面试知识体系</h2>
          <p className="hero-text">
            从采集、入库、分析到面试 Agent，对小红书题源做结构化整理。所有数据默认只保存在本机 SQLite，
            保持个人使用的轻量和可控。
          </p>
          <div className="hero-pills">
            <span>公司导航</span>
            <span>帖子检索</span>
            <span>规则分析</span>
            <span>Agent 追问</span>
          </div>
        </div>
        <div className="hero-sidebar">
          <Metric label="帖子总数" value={summary.postCount} />
          <Metric label="公司分组" value={summary.companyCount} />
          <Metric label="存储状态" value={runtime.bootstrapping ? "启动中" : "已连接"} />
        </div>
      </section>

      <main className="workspace">
        <aside className="sidebar-card">
          <div className="sidebar-section">
            <h3>工作区</h3>
            <p className="sidebar-text">选择你现在要处理的内容，页面会共享同一套帖子、配置和本地知识上下文。</p>
            <nav className="route-nav">
              {routes.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  className={`route-link ${route === item.id ? "active" : ""}`}
                  onClick={() => setRoute(item.id)}
                >
                  <strong>{item.label}</strong>
                  <span>{item.desc}</span>
                </button>
              ))}
            </nav>
          </div>
          <div className="sidebar-section">
            <h3>本地数据</h3>
            <div className="summary-grid">
              <div className="summary-tile">
                <span>数据库</span>
                <strong>{runtime.storage?.schemaVersion ? `v${runtime.storage.schemaVersion}` : "待连接"}</strong>
              </div>
              <div className="summary-tile">
                <span>旧数据迁移</span>
                <strong>{runtime.storage?.legacyImportCompleted ? "完成" : "待检查"}</strong>
              </div>
            </div>
          </div>
        </aside>
        <section className="main-stage">{children}</section>
      </main>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="hero-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
