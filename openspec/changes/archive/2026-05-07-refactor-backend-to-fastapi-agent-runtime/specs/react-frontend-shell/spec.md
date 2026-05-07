## ADDED Requirements

### Requirement: React 前端提供面试 Agent 页面
系统 SHALL 在现有 React 前端中新增“面试 Agent”页面，用于提问、查看分类、查看检索来源、阅读结构化回答和继续追问。

#### Scenario: 进入面试 Agent 页面
- **WHEN** 用户从应用导航进入“面试 Agent”
- **THEN** 系统展示问题输入区、回答区、上下文来源区和追问入口

#### Scenario: 发送首次问题
- **WHEN** 用户输入面试问题并点击生成
- **THEN** 前端调用 `/api/agent/answer`，并展示知识领域、标签、回答结构和来源列表

#### Scenario: 继续追问
- **WHEN** 用户在已有回答后输入追问
- **THEN** 前端调用追问接口并将回复追加到当前会话中

### Requirement: 面试 Agent 复用现有帖子库和模型配置
系统 SHALL 让面试 Agent 使用当前本地帖子库、公司/岗位上下文和大模型配置。

#### Scenario: 使用现有大模型配置
- **WHEN** 用户已经在大模型页面配置供应商、模型、Base URL 和 API Key
- **THEN** 面试 Agent 使用同一份本地配置发起回答请求

#### Scenario: 使用公司和岗位过滤
- **WHEN** 用户在帖子库中选择了公司或岗位范围
- **THEN** 面试 Agent 可以将该范围作为检索上下文过滤条件

### Requirement: 回答展示适合复习
系统 SHALL 以适合面试复习的方式展示 Agent 回答。

#### Scenario: 展示结构化回答
- **WHEN** Agent 返回回答结果
- **THEN** 前端展示一句话总结、分点回答、项目落地、易错点、可能追问和来源列表
