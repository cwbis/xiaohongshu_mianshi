# project-refactor-knowledge-base Specification

## Purpose
TBD - created by archiving change document-project-architecture-for-refactor. Update Purpose after archive.
## Requirements
### Requirement: 项目说明文档覆盖核心系统边界
系统 SHALL 提供一份面向后续重构的项目说明文档，覆盖前端、后端、存储、扩展桥接、外部依赖、启动方式和测试方式。

#### Scenario: 阅读者查看项目边界
- **WHEN** 开发者打开项目说明文档
- **THEN** 文档展示当前系统包含的主要模块、核心文件和它们之间的职责关系

#### Scenario: 阅读者查找运行链路
- **WHEN** 开发者需要理解应用如何启动和加载数据
- **THEN** 文档说明桌面启动器、本地 Python 服务、前端页面、SQLite bootstrap 和旧数据迁移的顺序

### Requirement: 项目说明文档描述关键数据流
系统 SHALL 在项目说明文档中描述帖子采集、候选结果、帖子入库、规则分析、大模型总结和帖子库浏览的关键数据流。

#### Scenario: 阅读者追踪搜索入库流程
- **WHEN** 开发者需要重构搜索页或帖子库
- **THEN** 文档说明小红书搜索结果如何从 `/api/xhs/search` 进入前端候选池，并如何转换为本地帖子记录

#### Scenario: 阅读者追踪持久化流程
- **WHEN** 开发者需要调整存储逻辑
- **THEN** 文档说明 `AppStore`、`/api/storage/*`、`StorageRepository` 和 SQLite 表之间的关系

### Requirement: 项目说明文档标注重构风险和建议顺序
系统 SHALL 在项目说明文档中提供重构风险清单和建议执行顺序，帮助后续重构控制范围。

#### Scenario: 阅读者制定重构计划
- **WHEN** 开发者准备拆分项目
- **THEN** 文档按阶段给出建议，例如先文档和死代码清理，再拆分前端状态和渲染，再调整后端服务边界

#### Scenario: 阅读者识别高风险区域
- **WHEN** 开发者查看风险清单
- **THEN** 文档明确标注高风险模块，例如 `app.js`、`local_app_server.py`、SQLite schema、小红书运行时代理和扩展桥接

### Requirement: 项目说明文档记录已知技术债
系统 SHALL 在项目说明文档中记录当前已知技术债，并区分“影响运行”和“影响维护”的问题。

#### Scenario: 阅读者查看技术债
- **WHEN** 开发者查看项目说明文档
- **THEN** 文档列出历史乱码文档、旧桥接代码、重复函数、全局状态膨胀和测试覆盖不足等维护问题

#### Scenario: 阅读者判断是否立即修复
- **WHEN** 技术债不影响当前运行
- **THEN** 文档将其标记为后续重构事项，而不是要求在本次文档变更中修复

### Requirement: 项目说明文档保持可验证
系统 SHALL 让项目说明文档中的文件路径、命令和接口可以被当前仓库验证。

#### Scenario: 开发者执行文档中的命令
- **WHEN** 文档给出启动或测试命令
- **THEN** 命令使用当前仓库已有入口，例如 `python local_app_server.py`、`start_offerscope.cmd`、`python -m unittest test_local_app_server.py`

#### Scenario: 开发者查找文档中的文件
- **WHEN** 文档引用核心文件
- **THEN** 所有文件路径都对应当前仓库中的真实文件

