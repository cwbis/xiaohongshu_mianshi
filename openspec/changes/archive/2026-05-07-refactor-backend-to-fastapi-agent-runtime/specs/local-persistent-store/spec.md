## ADDED Requirements

### Requirement: 持久化面试知识 Agent 数据
系统 SHALL 在现有 SQLite 数据库中保存面试题、知识点、Agent 会话和消息历史，且不得破坏现有帖子和设置数据。

#### Scenario: 初始化 Agent 数据表
- **WHEN** 本地服务启动且数据库缺少 Agent 相关表
- **THEN** 系统自动创建题目、知识点、会话、消息和必要索引表

#### Scenario: 保留现有数据
- **WHEN** 系统执行数据库初始化或迁移
- **THEN** 现有 `posts`、`settings` 和存储元数据 SHALL 保持可读可写

### Requirement: 支持本地全文检索索引
系统 SHALL 使用 SQLite FTS5 或兼容降级方案为帖子、题目和知识点提供本地全文检索能力。

#### Scenario: 构建全文索引
- **WHEN** 帖子、题目或知识点被新增或更新
- **THEN** 系统更新对应全文检索索引

#### Scenario: FTS5 不可用
- **WHEN** 当前 SQLite 环境不支持 FTS5
- **THEN** 系统降级为普通关键词检索，并向运行日志记录降级原因

### Requirement: 保存 Agent 会话历史
系统 SHALL 将每次 Agent 问答保存为本地会话历史，支持后续追问和复盘。

#### Scenario: 保存首次问题
- **WHEN** 用户发起新的 Agent 问答
- **THEN** 系统创建会话记录并保存用户问题、分类结果、回答结果和来源上下文

#### Scenario: 保存追问消息
- **WHEN** 用户在已有会话中继续追问
- **THEN** 系统追加用户消息和 Agent 回复，不覆盖原始问题与上一轮回答
