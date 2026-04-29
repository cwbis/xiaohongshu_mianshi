## Why

当前前端主要集中在 `app.js` 中，状态、页面渲染、事件绑定和业务动作混在一起，继续迭代搜索页、帖子库和大模型页面会越来越容易互相影响。用 React 重构前端可以把页面、状态和服务调用拆成清晰模块，为后续长期维护和功能扩展打基础。

## What Changes

- 引入 React 前端工程，使用组件化方式重建当前工作台页面。
- 将现有四个主要页面迁移为 React 视图：采集、帖子库、分析、大模型。
- 保留现有 Python 本地服务、SQLite API、桌面启动器和核心业务行为。
- 将 `store.js`、`xhs-service.js`、`llm-service.js` 等服务边界迁移为 React 工程内的 API client。
- 将当前 `app.js` 中的全局状态拆分为面向业务域的 React state 或 reducer。
- 保留 hash 路由或提供等价路由，确保当前页面导航能力不丢失。
- 建立 React 构建和本地开发脚本，并让 Python 服务能够托管构建后的前端产物。
- **BREAKING**：前端源码结构会从无构建的全局脚本模式迁移为 React 工程模式；开发和打包命令会发生变化。

## Capabilities

### New Capabilities

- `react-frontend-shell`: 定义 React 前端工作台的页面迁移、状态管理、API 兼容和构建托管要求。

### Modified Capabilities

- 无。

## Impact

- 影响前端文件：`index.html`、`app.js`、`styles.css`、`router.js`、`store.js`、`xhs-service.js`、`llm-service.js`、`analysis-core.js`、`analysis-ai-service.js`、`model-presets.js`。
- 影响新增工程文件：`package.json`、React 入口、组件目录、状态目录、服务 client 目录、构建配置。
- 影响后端托管方式：`local_app_server.py` 需要能继续服务前端入口，必要时支持托管 React 构建产物。
- 不改变 SQLite schema，不改变现有 `/api/storage/*`、`/api/xhs/*` 接口契约。
- 不改变 `desktop_launcher.py` 和 `start_offerscope.cmd` 的用户启动入口，除非实现阶段发现构建产物路径需要微调。
- 需要更新 README 和项目重构说明文档，说明新的开发、构建和运行方式。
