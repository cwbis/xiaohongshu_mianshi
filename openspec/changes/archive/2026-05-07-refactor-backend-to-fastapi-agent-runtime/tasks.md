## 1. 后端框架基础

- [x] 1.1 新增 Python 后端依赖文件，包含 FastAPI、Uvicorn、Pydantic 等运行所需依赖。
- [x] 1.2 创建 `backend/` 目录结构，拆分 `api`、`services`、`repositories`、`schemas` 模块。
- [x] 1.3 实现 FastAPI 应用入口和 `/api/health`，确认本地服务可以启动并返回健康状态。
- [x] 1.4 实现 React 构建产物静态托管和非 API 路径回退到前端入口。
- [x] 1.5 保留 `local_app_server.py` 兼容启动入口，使旧命令可以启动新 FastAPI 服务。

## 2. 迁移现有存储能力

- [x] 2.1 将 SQLite 连接、初始化和通用 JSON 响应逻辑迁移到 `backend/repositories/db.py`。
- [x] 2.2 迁移 `posts` 存储读写逻辑，保持 `GET /api/storage/posts` 和 `PUT /api/storage/posts` 兼容。
- [x] 2.3 迁移 `settings` 存储读写逻辑，保持 `xhsConfig` 和 `llmConfig` 持久化兼容。
- [x] 2.4 迁移 `GET /api/storage/bootstrap`，确保前端启动数据结构不变。
- [x] 2.5 迁移 `POST /api/storage/import-local` 和旧 `localStorage` 清理兼容逻辑。

## 3. 迁移 XHS 和 LLM 能力

- [x] 3.1 将小红书脚本加载和调用封装到 `backend/services/xhs_service.py`。
- [x] 3.2 迁移 `POST /api/xhs/search`，保持搜索请求和候选结果兼容。
- [x] 3.3 迁移 `POST /api/xhs/note-detail`，保持详情请求和归一化结果兼容。
- [x] 3.4 将大模型请求封装到 `backend/services/llm_service.py`，复用现有模型配置语义。
- [x] 3.5 增加后端错误响应规范，确保前端可以显示可读错误。

## 4. Agent 数据模型与检索

- [x] 4.1 新增题目、知识点、Agent 会话和消息历史相关 SQLite 表初始化逻辑。
- [x] 4.2 为帖子、题目和知识点创建 SQLite FTS5 全文索引，并提供 FTS5 不可用时的关键词检索降级。
- [x] 4.3 实现 `knowledge_repo` 和 `session_repo`，支持题目、知识点、会话和消息读写。
- [x] 4.4 实现知识领域规则表，覆盖 Redis、MySQL、MQ、高并发、分布式事务、系统设计等初始领域。
- [x] 4.5 实现 `retrieval_service`，支持按问题关键词、领域标签、公司和岗位检索 Top N 上下文。

## 5. 面试知识 Agent API

- [x] 5.1 实现 `POST /api/agent/classify`，返回主领域、相关标签和问题意图。
- [x] 5.2 实现 `POST /api/agent/retrieve`，返回相关帖子、题目和知识点来源。
- [x] 5.3 实现 `POST /api/agent/answer`，生成结构化面试回答并保存会话。
- [x] 5.4 实现 `POST /api/agent/follow-up`，复用会话上下文生成追问回答。
- [x] 5.5 实现 `GET /api/agent/sessions` 和会话详情读取接口，支持历史复盘。

## 6. React 前端接入

- [x] 6.1 新增 Agent API client，封装分类、检索、回答、追问和历史会话请求。
- [x] 6.2 在导航中新增“面试 Agent”页面入口，并保持现有页面可用。
- [x] 6.3 实现问题输入、分类标签、上下文来源、结构化回答和追问 UI。
- [x] 6.4 复用现有 `llmConfig`、帖子库、公司和岗位上下文作为 Agent 请求参数。
- [x] 6.5 增加会话历史展示或最近会话恢复入口。

## 7. 启动、文档与验证

- [x] 7.1 更新 `start_offerscope.cmd` 和 `desktop_launcher.py`，确保 FastAPI 服务可自动启动和关闭。
- [x] 7.2 更新 README，说明新的安装依赖、启动命令、兼容命令和 Agent 使用方式。
- [x] 7.3 更新或新增后端单元测试，覆盖健康检查、bootstrap、存储、XHS 路由兼容和 Agent 基础接口。
- [x] 7.4 运行 `npm run build`，确认 React 前端仍可构建。
- [x] 7.5 运行 Python 测试和本地 smoke test，确认首页、`/api/health`、现有 API 和 Agent API 可用。
- [x] 7.6 检查 Git 工作区，确认未误删用户数据、数据库文件或未纳入版本控制的本地配置。
