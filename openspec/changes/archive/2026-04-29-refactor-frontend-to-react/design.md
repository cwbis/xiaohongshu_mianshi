## Context

当前 OfferScope 前端是无构建的原生 JavaScript 应用：`index.html` 通过固定顺序加载多个全局脚本，最后由 `app.js` 接管全局状态、路由、渲染、事件绑定和业务动作。近期功能快速增长后，`app.js` 已超过十万字符，搜索、帖子库、分析、大模型和历史扩展桥接逻辑互相靠近，后续继续加功能会越来越难控。

后端已经相对稳定：`local_app_server.py` 提供静态文件、SQLite 存储 API、小红书 API 代理和桌面启动器支持。本次 React 重构应优先重建前端组织方式，保持后端 API、SQLite schema 和启动入口稳定。

## Goals / Non-Goals

**Goals:**

- 引入 React 前端工程，将当前工作台迁移到组件化结构。
- 保留现有四个页面能力：采集、帖子库、分析、大模型。
- 保留现有本地 API 契约：`/api/storage/*`、`/api/xhs/*`。
- 将当前全局 `state` 拆成更清晰的 React 状态层。
- 将 API 调用、分析逻辑、模型配置迁移为可测试的模块。
- 让 `python local_app_server.py` 和桌面启动器仍能打开可用前端。

**Non-Goals:**

- 不在本次变更中修改 SQLite schema。
- 不重写小红书 API runtime。
- 不改变帖子记录字段含义和入库确认规则。
- 不引入用户登录、远程数据库或云端部署。
- 不把后端改成 Node 服务。

## Decisions

### Decision: 使用 Vite + React

Vite 适合小型前端工程迁移，开发服务器和构建配置都比较轻，能快速接入 React。相比手写构建脚本或直接使用 CDN React，Vite 更利于后续组件拆分、模块导入和测试。

备选方案是直接在现有 `index.html` 里用 CDN React 渐进接管 DOM。这个方案初期改动小，但会继续保留全局脚本和无构建模式，无法真正解决 `app.js` 职责过重的问题。

### Decision: 保持 Python API 为后端边界

React 前端通过 fetch 继续调用现有本地 API，不把 SQLite 或小红书 runtime 逻辑搬到前端。这样可以让重构集中在前端组织方式上，也能继续复用已通过测试的 `StorageRepository` 和 API handler。

### Decision: 采用分阶段迁移

第一阶段建立 React 工程、API client、布局壳和路由；第二阶段迁移采集页和帖子库；第三阶段迁移分析和大模型页面；第四阶段移除旧全局脚本入口。这样每个阶段都能保留可运行状态，并方便回滚。

### Decision: 状态按业务域拆分

将当前 `state` 拆为：

- `runtime`: bootstrap、storageMeta、错误状态。
- `collect`: 搜索配置、候选结果、勾选状态、分页状态。
- `library`: 帖子列表、公司/岗位筛选、详情弹层状态。
- `analysis`: 规则分析缓存、专题题库。
- `llm`: 模型配置、回答结果、调用状态。

初期可以使用 React `useReducer` 和 Context，避免过早引入 Redux、Zustand 等额外依赖。等状态边界稳定后再评估是否需要状态库。

### Decision: 分离纯业务逻辑和 UI

规则分析、模型 payload 构造、帖子分组、帖子去重、日期归一化等逻辑应放在 `src/domain/` 或 `src/lib/`，React 组件只负责展示和交互。这能降低组件测试难度，也避免新 `App.jsx` 变成另一个 `app.js`。

### Decision: 构建产物由 Python 服务托管

开发时可使用 Vite dev server；正式本地运行时由 `npm run build` 生成静态产物，并让 `local_app_server.py` 服务构建后的入口。为了保持桌面启动器体验，最终用户仍应能通过 `start_offerscope.cmd` 进入应用。

## Risks / Trade-offs

- [Risk] 一次迁移页面过多导致回归难定位 -> [Mitigation] 按页面迁移，保留每阶段 smoke test。
- [Risk] React 状态层复刻旧全局状态，复杂度没有下降 -> [Mitigation] 先按业务域拆 reducer，再写组件。
- [Risk] Vite dev server 与 Python API 不同源导致请求问题 -> [Mitigation] 开发环境配置 proxy 到本地 Python 服务，生产环境使用同源路径。
- [Risk] 构建产物路径影响桌面启动器 -> [Mitigation] 在实现阶段明确 `dist/` 托管策略，并测试 `desktop_launcher.py`。
- [Risk] 旧扩展桥接代码未迁移导致隐藏能力丢失 -> [Mitigation] 先记录现有桥接函数，确认当前 UI 不再依赖后再删除。
- [Risk] 大模型和分析模块存在历史乱码 -> [Mitigation] React 迁移时不要照搬乱码文案，应先恢复正常中文或封装为可替换常量。

## Migration Plan

1. 新增 React 工程骨架和构建脚本。
2. 建立 `src/api/`，迁移 `store.js`、`xhs-service.js`、`llm-service.js` 的接口封装。
3. 建立 `src/domain/`，迁移分析、帖子分组、记录归一化等纯逻辑。
4. 建立 `src/app/`，实现 bootstrap、路由、布局和全局状态。
5. 迁移采集页，确保搜索、刷新、加载更多、分页、详情和入库可用。
6. 迁移帖子库，确保公司导航、岗位筛选、详情弹层、导入导出、删除和载入草稿可用。
7. 迁移分析页和大模型页，确保本地规则分析和大模型调用可用。
8. 更新 Python 静态服务和桌面启动器使用 React 构建产物。
9. 删除或停用旧 `app.js` 全局入口，保留必要兼容文件直到确认无引用。
10. 更新 README 和项目梳理文档。

## Open Questions

- 是否在第一版 React 重构中保留浏览器扩展桥接能力，还是作为后续独立清理项处理？
- 是否继续使用 hash route，还是迁移到 React Router 的 hash router？
- 是否将 `analysis-core.js` 的乱码修复纳入 React 迁移第一阶段，还是先保持行为等价后单独修？
- React 构建产物是否放在 `dist/`，还是放入专门的 `frontend/dist/`？
