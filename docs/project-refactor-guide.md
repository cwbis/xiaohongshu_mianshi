# OfferScope 项目梳理与后续重构说明

最后更新：2026-04-29

本文档用于后续继续重构 OfferScope。当前项目已经迁移到 React + Vite，旧版根目录全局前端脚本已从当前运行项目中移除；如需追溯历史设计，可查看 OpenSpec 归档和早期中文文档。

## 当前运行形态

- 前端：React + Vite，源码位于 `src/`。
- 构建产物：`dist/`，由 `npm run build` 生成，默认不提交到 GitHub。
- 本地服务：`local_app_server.py`，负责托管 React 构建产物并提供 `/api/*`。
- 数据库：`data/offerscope.db`，SQLite 本地持久化，默认不提交到 GitHub。
- 桌面入口：`start_offerscope.cmd` 调用 `desktop_launcher.py`，减少手动启动服务的操作。

## 推荐命令

安装依赖：

```powershell
cd d:\codex\demo_xiaohongshu
npm install
```

开发模式：

```powershell
python local_app_server.py
npm run dev
```

生产构建与本地运行：

```powershell
npm run build
python local_app_server.py
```

验证：

```powershell
npm run build
python -m unittest test_local_app_server.py
```

## 主要目录职责

| 路径 | 当前职责 | 后续关注点 |
| --- | --- | --- |
| `src/app/` | React 根组件、启动状态、路由状态、跨页面状态 | 后续可继续拆成 context 或轻量 store |
| `src/pages/` | 采集、帖子库、分析、大模型四个页面 | 每个页面可进一步拆细组件 |
| `src/components/` | Shell、帖子卡片等可复用组件 | 建议继续沉淀表单、弹层、空状态组件 |
| `src/api/` | storage、xhs、llm API client | 保持接口契约稳定，减少页面直接 fetch |
| `src/domain/` | 帖子归一化、分组、分析、AI payload、模型预设 | 业务规则优先放这里，避免组件变重 |
| `src/styles/` | React 专用补充样式 | 目前仍复用根目录 `styles.css` |
| `styles.css` | 当前共享全局样式 | 后续可按组件逐步迁移和裁剪 |
| `local_app_server.py` | API、SQLite repository、XHS runtime、静态托管 | 后续适合拆成 repository/handlers/runtime |
| `desktop_launcher.py` | 启动本地服务并打开桌面窗口 | 重构时要保留自动启动与退出清理 |
| `XhsSkills-master/` | 小红书 API 脚本依赖 | 体积大，不建议混入业务重构 |
| `openspec/` | 变更提案、设计、任务和归档 | 每次重要重构继续走 change |

## React 前端结构

当前 React 应用保留四个核心入口：

- `collect`：搜索小红书帖子、刷新、翻页、查看候选详情、勾选入库。
- `library`：按公司优先分组，岗位作为公司下的子标签，使用小红书式卡片和详情弹层浏览。
- `analysis`：基于本地规则生成主题统计、典型问题、复习建议和 Markdown 报告。
- `llm`：配置兼容 `chat/completions` 的大模型接口，生成面试回答和专题题库。

路由目前使用 hash，不引入 React Router，目的是保持重构轻量并兼容桌面壳。

## 数据流

启动流程：

1. React 应用调用 `GET /api/storage/bootstrap`。
2. 后端返回 `posts`、`settings`、`storage`。
3. 如果旧版 `localStorage` 仍存在且尚未迁移，前端调用 `POST /api/storage/import-local`。
4. 页面状态从 SQLite 恢复，后续帖子和配置都写回本地数据库。

采集入库：

1. 采集页调用 `POST /api/xhs/search`。
2. 后端通过 `XhsSkills-master` 中的小红书脚本完成搜索。
3. 前端展示候选帖子，用户勾选后归一化为帖子记录。
4. 前端调用 `PUT /api/storage/posts` 覆盖保存去重后的帖子库。

帖子库浏览：

1. `src/domain/posts.js` 按公司分组。
2. 公司下再按岗位分组。
3. 当前公司和岗位筛选由 React 状态保存。
4. 详情弹层独立滚动，避免滚动穿透到首页。

分析与大模型：

1. `src/domain/analysis.js` 做本地规则分析。
2. `src/domain/ai.js` 构造大模型 prompt 和 JSON payload。
3. `src/api/llm.js` 调用兼容 OpenAI `chat/completions` 的接口。

## 本地 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查 |
| `GET` | `/api/storage/bootstrap` | 启动数据 |
| `GET` | `/api/storage/posts` | 帖子列表 |
| `GET` | `/api/storage/settings` | 设置列表 |
| `PUT` | `/api/storage/posts` | 保存帖子库 |
| `PUT` | `/api/storage/settings/xhsConfig` | 保存小红书配置 |
| `PUT` | `/api/storage/settings/llmConfig` | 保存大模型配置 |
| `POST` | `/api/storage/import-local` | 导入旧 localStorage 数据 |
| `POST` | `/api/xhs/search` | 搜索小红书帖子 |
| `POST` | `/api/xhs/note-detail` | 获取帖子详情 |

## 已完成清理

- 旧版根目录全局前端入口已移除，当前前端入口为 `index.html` 和 `src/main.jsx`。
- 旧 Node 检查脚本已移除，当前验证入口为 `npm run build` 和 `python -m unittest test_local_app_server.py`。
- `dist/`、`node_modules/`、`data/*.db`、日志和环境文件默认通过 `.gitignore` 排除。

## 后续重构建议

1. 将 `styles.css` 拆成 `src/styles/base.css`、`src/styles/layout.css`、页面样式和组件样式。
2. 将 React 状态从 `App.jsx` 继续拆成 `runtime`、`collect`、`library`、`analysis`、`llm` 五个 hook。
3. 将 `local_app_server.py` 拆为 storage repository、API handler、XHS runtime 和 server bootstrap。
4. 增加前端 smoke test，至少覆盖页面可渲染、帖子库分组、详情弹层、分析报告生成。
5. 为帖子记录建立更明确的字段说明和 schema，减少前后端去重规则漂移。

## 重构必须保留的行为

- 启动时从 SQLite 恢复帖子和配置。
- 旧 `localStorage` 数据可自动迁移。
- 搜索结果不会自动入库，必须由用户勾选或确认。
- 帖子库按公司优先浏览，岗位是公司下的子方向。
- 详情弹层内容可独立上下滚动。
- 大模型配置持久化在本地 SQLite。
- 桌面启动器仍能自动启动和关闭本地服务。
