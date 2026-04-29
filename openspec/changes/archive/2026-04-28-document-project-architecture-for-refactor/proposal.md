## Why

当前项目已经从一个简单的本地页面逐步演进为包含前端工作台、Python 本地服务、SQLite 持久化、小红书搜索能力、浏览器扩展桥接和 OpenSpec 变更记录的组合系统。后续如果要整体重构，仅靠 README 和零散技术文档很难快速判断模块边界、数据流、风险点和优先级。

本次变更的目标是形成一份面向重构的项目说明文档，把现有功能、关键文件、运行链路、数据模型、接口边界、已知问题和重构建议整理到同一份文档中，作为后续拆分、重构和验收的共同参照。

## What Changes

- 新增一份面向后续重构的项目梳理文档，建议位置为 `docs/project-refactor-guide.md`。
- 文档覆盖当前项目的业务目标、运行方式、前端模块、后端模块、数据存储、外部依赖、扩展桥接、OpenSpec 状态和测试方式。
- 文档明确现有架构的主要痛点，例如 `app.js` 职责过重、搜索页和帖子库交互快速演化、部分旧桥接代码仍残留、主规范文档存在历史编码问题。
- 文档给出可执行的重构拆分建议，帮助后续按阶段重构，而不是一次性大改。
- 文档不改变现有运行行为、不新增业务接口、不删除功能代码。

## Capabilities

### New Capabilities

- `project-refactor-knowledge-base`: 定义项目梳理文档应覆盖的内容、准确性要求和后续重构可用性要求。

### Modified Capabilities

- 无。

## Impact

- 影响文档目录：新增 `docs/project-refactor-guide.md`。
- 影响 OpenSpec：新增 `openspec/changes/document-project-architecture-for-refactor/` 下的 proposal、design、tasks 和 spec。
- 不影响前端运行逻辑、后端 API、数据库 schema、浏览器扩展或桌面启动器。
- 后续重构将以该文档作为项目现状和重构路径的基础资料。
