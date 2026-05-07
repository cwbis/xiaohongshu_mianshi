## Why

当前本地后端仍集中在 `local_app_server.py`，已经承担静态托管、SQLite 存储、小红书采集、大模型配置和 API 路由等职责。后续要把产品升级为“面试知识 Agent”，需要一个更清晰、可扩展的 Python 后端骨架来承载问题分类、知识检索、结构化回答和追问上下文。

本次变更先把后端运行时迁移到轻量框架化形态，同时保持个人本地使用体验：仍然是一个本地应用、一个启动入口、一个 SQLite 数据库，不引入线上部署复杂度。

## What Changes

- 引入 FastAPI 作为本地 Python API 框架，替代手写 `BaseHTTPRequestHandler` 路由处理。
- 保留现有 React 构建产物托管、SQLite 数据持久化、小红书采集、大模型配置和现有 API 行为。
- 新增面试知识 Agent 的后端模块边界，包括知识领域识别、帖子/题目检索、面试级回答生成和追问会话管理。
- 设计本地 SQLite 表结构扩展，用于保存面试题、知识点、Agent 会话和消息历史。
- 优先采用 SQLite FTS5 做第一阶段本地全文检索，不在本阶段引入向量数据库、Redis、Celery 或 Docker。
- 保持 `start_offerscope.cmd` / 桌面启动器的单机启动体验，用户不需要分别手动启动前后端。

## Capabilities

### New Capabilities

- `fastapi-local-runtime`: 定义 FastAPI 本地后端运行时、静态托管、现有 API 兼容和启动入口要求。
- `interview-knowledge-agent`: 定义面试知识 Agent 的问题分类、上下文检索、结构化回答和追问会话能力。

### Modified Capabilities

- `local-persistent-store`: 扩展本地 SQLite 持久化要求，支持题目、知识点、Agent 会话和消息历史。
- `managed-local-runtime`: 更新本地托管运行要求，确保迁移到 FastAPI 后仍可通过桌面启动器自动启动和关闭。
- `react-frontend-shell`: 更新前端交互要求，支持新增“面试 Agent”页面并复用现有模型配置和帖子库上下文。

## Impact

- 后端代码：新增 `backend/` 模块结构，逐步迁移 `local_app_server.py` 中的路由、存储、XHS runtime 和静态托管逻辑。
- API：保持现有 `/api/storage/*`、`/api/xhs/*`、`/api/health` 路径兼容；新增 `/api/agent/*` 和 `/api/knowledge/*` 能力。
- 数据库：在现有 SQLite 基础上新增题目、知识点、会话、消息和可选全文索引表。
- 前端：新增面试 Agent 页面，现有采集、帖子库、分析、大模型页面继续可用。
- 启动方式：更新启动脚本和 README，使个人用户仍通过一个入口启动完整本地应用。
- 依赖：新增 FastAPI、Uvicorn、Pydantic 等 Python 后端依赖，避免引入重型 Agent 框架。
