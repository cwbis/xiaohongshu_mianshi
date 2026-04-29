## Why

当前应用把帖子数据和关键配置保存在浏览器 `localStorage` 中，这会让数据依赖具体浏览器环境，稳定性较差，也不利于后续统一做数据约束、迁移和扩展。同时，本地 Python 服务需要用户每次手动启动，搜索和详情能力才能正常工作，这给日常使用带来了明显摩擦。

## What Changes

- 将帖子数据和关键应用配置从浏览器侧持久化迁移到由本地服务托管的轻量数据库中。
- 新增本地读写 HTTP API，使前端通过服务端加载和保存帖子记录、小红书搜索配置以及 LLM 配置，而不再直接写入 `localStorage`。
- 保持应用仍然是单机、本地优先的工作台，但把持久化规则、去重逻辑和数据结构演进收敛到后端。
- 引入桌面化启动路径，使用户打开工具时可以自动确保本地服务可用，而不需要每次手动执行 `python local_app_server.py`。
- 更新项目文档和默认操作流程，使新的启动方式成为推荐路径。

## Capabilities

### New Capabilities
- `local-persistent-store`：通过后端持久化 API，把 OfferScope 数据保存到轻量本地数据库中。
- `managed-local-runtime`：在启动 UI 的同时自动拉起本地服务，避免日常使用依赖手动命令行启动。

### Modified Capabilities
- None.

## Impact

- 受影响代码：`store.js`、`app.js`、`local_app_server.py`、启动脚本以及项目文档。
- 新增依赖/系统：Python SQLite 持久化层，以及用于自动启动本地服务的轻量桌面壳或启动器流程。
- API 影响：新增帖子与配置持久化接口，以及供前端运行时使用的启动健康检查接口。
