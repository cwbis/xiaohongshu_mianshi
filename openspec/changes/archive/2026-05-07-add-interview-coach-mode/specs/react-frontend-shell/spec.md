## MODIFIED Requirements

### Requirement: React 前端提供面试 Agent 页面
系统 SHALL 在现有 React 前端中提供问答模式和训练模式两种面试 Agent 交互方式。

#### Scenario: 进入训练模式
- **WHEN** 用户从面试 Agent 页面切换到训练模式
- **THEN** 前端展示目标输入、主动出题、作答输入、评估反馈和阶段总结所需的界面区域

#### Scenario: 保留问答模式
- **WHEN** 用户选择继续使用自由问答
- **THEN** 前端仍保留当前问答式交互，不强制用户进入训练闭环

### Requirement: 回答展示适合复习
系统 SHALL 以适合面试复习的方式展示 Agent 回答，并在训练模式下额外展示训练反馈和下一步动作。

#### Scenario: 展示训练反馈
- **WHEN** 训练模式完成一轮回答评估
- **THEN** 前端展示优点、缺口、下一步建议，以及当前动作是追问、下一题、切专题还是总结
