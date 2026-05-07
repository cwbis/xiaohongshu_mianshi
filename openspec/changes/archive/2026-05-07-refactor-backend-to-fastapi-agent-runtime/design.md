## Context

OfferScope 当前已经完成 React + Vite 前端重构，并通过 `local_app_server.py` 提供本地 API、SQLite 存储、小红书采集脚本调用和静态资源托管。这个形态适合早期快速迭代，但后端职责已经集中在一个文件里，继续加入“面试知识 Agent”会让路由、数据模型、检索、LLM 编排和会话管理互相缠绕。

用户场景是个人本地使用，不需要线上部署、多租户或复杂服务编排。因此后端框架化的目标不是做重型平台，而是把本地服务整理成清晰、可测试、可扩展的模块：React 仍是界面，Python 仍是本地引擎，SQLite 仍是唯一默认持久化。

## Goals / Non-Goals

**Goals:**

- 使用 FastAPI 建立本地后端骨架，替代手写 HTTP handler。
- 保持现有 API 路径和启动方式兼容，避免前端一次性大改。
- 将后端拆分为 `api`、`services`、`repositories`、`schemas` 等职责明确的模块。
- 为面试知识 Agent 建立后端边界：分类、检索、回答生成、追问会话。
- 扩展 SQLite 数据模型，支持题目、知识点、会话、消息和 FTS5 全文检索。
- 保持个人使用的轻量体验：一个本地启动入口、一个 SQLite 文件、一个 React 应用。

**Non-Goals:**

- 不在本阶段引入 LangChain、LlamaIndex、Chroma、Milvus、Redis、Celery 或 Docker。
- 不在本阶段实现复杂向量检索；第一阶段使用 SQLite FTS5 和规则/LLM 混合检索。
- 不做线上部署、多用户权限、团队协作或云端同步。
- 不改变小红书采集脚本的核心实现，只通过服务边界封装现有能力。
- 不移除现有功能页面；采集、帖子库、分析、大模型配置必须继续可用。

## Decisions

### Decision 1: 使用 FastAPI 作为本地后端框架

采用 FastAPI + Uvicorn 承载本地 API 和静态资源托管。

理由：
- FastAPI 路由、请求校验和响应模型更清晰，适合持续扩展 `/api/agent/*` 与 `/api/knowledge/*`。
- Pydantic 模型可以约束 Agent 输入输出，减少大模型 JSON 结果不稳定带来的扩散。
- 本地运行仍然简单，可以由 `desktop_launcher.py` 或 `start_offerscope.cmd` 启动。

替代方案：
- 继续维护 `BaseHTTPRequestHandler`：依赖少，但路由、校验、错误处理和测试成本会继续上升。
- Flask：足够轻量，但类型校验和自动文档能力弱于 FastAPI。
- Django：过重，不符合个人本地工具的使用方式。

### Decision 2: 采用渐进迁移，不一次性推翻 `local_app_server.py`

先新增 `backend/` 结构，再迁移现有能力。迁移过程中可以保留兼容入口，使旧命令最终转发到新的 FastAPI 应用。

目标结构：

```text
backend/
  main.py
  api/
    health.py
    storage.py
    xhs.py
    llm.py
    knowledge.py
    agent.py
  services/
    xhs_service.py
    llm_service.py
    classifier_service.py
    retrieval_service.py
    agent_service.py
  repositories/
    db.py
    posts_repo.py
    settings_repo.py
    knowledge_repo.py
    session_repo.py
  schemas/
    posts.py
    settings.py
    knowledge.py
    agent.py
```

理由：
- 能把迁移风险分散到多个小任务。
- 可以先让现有测试通过，再逐步接入 Agent 能力。
- 保留 `python local_app_server.py` 的兼容入口，有利于用户习惯和 README 过渡。

### Decision 3: 第一阶段检索使用 SQLite FTS5

面试知识 Agent 第一阶段从帖子、题目和知识点中做本地全文检索，并结合知识领域标签和公司/岗位过滤。

理由：
- SQLite 已经是项目默认存储，FTS5 对个人本地数据量足够。
- 不需要引入向量库和 embedding 成本。
- 后续如果语义检索需求明显，可以在同一层 `retrieval_service.py` 增加 embedding rerank，不影响前端契约。

检索流程：

```text
用户问题
  ↓
规则 + LLM 分类
  ↓
提取关键词和领域标签
  ↓
SQLite FTS5 检索 posts/questions/knowledge_points
  ↓
按命中、领域、公司/岗位、时间排序
  ↓
返回 Top N 上下文给回答生成
```

### Decision 4: Agent 输出使用结构化 JSON 契约

Agent 回答接口返回固定结构，而不是自由 Markdown。

建议响应结构：

```json
{
  "sessionId": "string",
  "domain": "缓存一致性",
  "tags": ["Redis", "库存扣减", "高并发"],
  "summary": "一句话总答",
  "sections": [
    {"title": "问题本质", "content": "..."}
  ],
  "projectExample": "...",
  "pitfalls": ["..."],
  "followUps": ["为什么不用强一致？"],
  "sources": [
    {"type": "post", "id": "string", "title": "string"}
  ]
}
```

理由：
- 前端可以稳定渲染总-分结构、项目落地、易错点和追问。
- 会话可以保存为可复盘的数据，而不是不可解析的大段文本。
- 后续可以基于 `followUps` 做快捷追问按钮。

### Decision 5: 保留单机体验，不做传统前后端部署

技术上有 React 前端和 FastAPI 后端，但产品上仍是一个本地应用。启动器负责启动 Python 服务并打开本地页面。

理由：
- 用户是个人使用，不希望手动管理多个服务。
- SQLite、API Key、帖子库和会话记录都保留在本机，符合当前隐私与便捷性预期。
- 后续如需分享或发布，再单独设计打包方案。

## Risks / Trade-offs

- [Risk] FastAPI 迁移可能破坏现有 API 兼容性 → 迁移时保留路径和响应结构，先让现有 `test_local_app_server.py` 通过，再新增 Agent 测试。
- [Risk] 新增依赖会提高首次安装门槛 → 将依赖写入 `requirements.txt`，README 明确安装命令，启动器失败时给出可读错误。
- [Risk] FTS5 对语义相似问题召回不足 → 第一版接受轻量检索，保留 `retrieval_service.py` 扩展点，后续再加 embedding。
- [Risk] 大模型分类和回答可能输出不稳定 JSON → 使用 Pydantic schema 校验、JSON 修复提示和明确的 system prompt。
- [Risk] 小红书内容噪音高，检索上下文质量不稳定 → 增加题目抽取和知识点标签，把原帖内容先整理为可检索题目。
- [Risk] 一次性迁移过大导致功能回归 → 按模块迁移：健康检查和静态托管、存储、XHS、LLM、Agent，逐步验证。

## Migration Plan

1. 新增 FastAPI 后端依赖和 `backend/` 目录，不删除旧入口。
2. 实现 `/api/health` 和 React 静态托管，验证首页可访问。
3. 迁移 SQLite 连接、settings、posts、bootstrap、import-local 等存储 API。
4. 迁移小红书搜索和详情 API，保持请求/响应兼容。
5. 迁移 LLM 调用封装，复用现有模型配置。
6. 新增 knowledge 数据模型和 FTS5 索引初始化。
7. 新增 Agent 分类、检索、回答、追问接口。
8. 更新前端新增“面试 Agent”页面。
9. 更新启动器、README 和测试。
10. 确认稳定后，让 `local_app_server.py` 成为兼容启动入口或归档说明中的旧入口。

Rollback 策略：
- 在迁移完成前保留旧 `local_app_server.py` 可运行路径。
- 如果 FastAPI 新入口出现阻塞，启动脚本可临时回退到旧入口。
- 数据库迁移采用向前兼容建表，不删除现有表和字段。

## Open Questions

- 第一版 Agent 是否需要保存所有问答历史，还是只保存用户主动收藏的会话？
- 知识领域树第一版采用内置规则即可，还是需要前端可编辑？
- 题目抽取是用户手动触发，还是采集入库后自动后台整理？
- 是否需要为 API Key 做更强的本地加密，还是继续保存在 SQLite settings 中？
