# local-persistent-store Specification

## Purpose

定义 OfferScope 本地持久化能力，包括帖子、配置、旧数据迁移，以及面试知识 Agent 相关的存储与检索索引。

## Requirements

### Requirement: 后端托管帖子持久化
系统 SHALL 将 OfferScope 的帖子记录保存到后端托管的轻量数据库中，而不是继续依赖浏览器 `localStorage` 作为长期存储。

#### Scenario: 启动时加载已持久化帖子
- **WHEN** 前端启动并请求持久化数据
- **THEN** 后端返回数据库中当前已保存的帖子集合

#### Scenario: 保存合并后的帖子集合
- **WHEN** 用户新增、导入或编辑帖子并导致存储集合发生变化
- **THEN** 前端通过后端持久化 API 写入更新后的集合，且后端以事务方式保存标准化后的记录

### Requirement: 后端托管配置持久化
系统 SHALL 将应用的长期配置，包括 `xhsConfig` 和 `llmConfig`，保存到后端托管数据库中。

#### Scenario: 按 scope 加载已保存配置
- **WHEN** 前端在 bootstrap 阶段请求长期配置
- **THEN** 后端返回每个受支持配置 scope 的最新保存值

#### Scenario: 更新单个配置 scope 不影响其他配置
- **WHEN** 用户更新某一个配置 scope，例如 `xhsConfig`
- **THEN** 后端只持久化该 scope，并保留其他 scope 之前已保存的值

### Requirement: 兼容旧版浏览器数据迁移
系统 SHALL 支持将旧版浏览器存储数据一次性迁移到数据库中。

#### Scenario: 在空数据库中导入旧版浏览器数据
- **WHEN** 后端数据库中尚无已保存帖子或配置，且前端提供了旧版浏览器数据
- **THEN** 后端导入其中合法的历史记录，并返回迁移结果

#### Scenario: 迁移时避免重复记录
- **WHEN** 导入的旧版数据中包含数据库里已存在的帖子
- **THEN** 后端根据应用定义的身份识别规则对记录去重，并保证每篇帖子只保留一份

### Requirement: 持久化 API 健康度与错误反馈
系统 SHALL 为持久化 API 提供明确的成功或错误响应，以便前端能够正确处理存储失败场景。

#### Scenario: 报告存储写入失败
- **WHEN** 某次持久化操作因非法 payload 或数据库错误而失败
- **THEN** 后端返回描述失败原因的错误响应，且前端不能静默假设写入成功

#### Scenario: 提供统一 bootstrap 数据
- **WHEN** 前端向本地服务请求 bootstrap 数据
- **THEN** 后端返回单个响应，其中包含已保存帖子、已保存配置以及启动所需的存储元数据

### Requirement: 持久化面试知识 Agent 数据
系统 SHALL 在现有 SQLite 数据库中保存面试题目、知识点、Agent 会话和消息历史，且不得破坏现有帖子和设置数据。

#### Scenario: 初始化 Agent 数据表
- **WHEN** 本地服务启动且数据库缺少 Agent 相关表
- **THEN** 系统自动创建题目、知识点、会话、消息和必要索引表

#### Scenario: 保留现有数据
- **WHEN** 系统执行数据库初始化或迁移
- **THEN** 现有 `posts`、`settings` 和存储元数据保持可读可写

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
