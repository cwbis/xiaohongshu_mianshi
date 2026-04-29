## ADDED Requirements

### Requirement: 本地运行健康巡检
系统 SHALL 提供可重复执行的本地运行健康巡检流程，用于确认 React 前端、本地 Python 服务和核心 API 正常工作。

#### Scenario: 验证前端构建
- **WHEN** 开发者运行前端构建检查
- **THEN** 系统成功完成 `npm run build`，并生成可由本地服务托管的 React 构建产物

#### Scenario: 验证后端测试
- **WHEN** 开发者运行 `python -m unittest test_local_app_server.py`
- **THEN** 系统通过本地服务健康检查、bootstrap 和存储相关测试

#### Scenario: 验证本地服务首页
- **WHEN** 开发者临时启动 `local_app_server.py`
- **THEN** `/api/health` 返回成功响应，首页返回 React 应用页面

### Requirement: 核心功能路径可手动巡检
系统 SHALL 提供清晰的手动巡检清单，覆盖采集、帖子库、分析、大模型配置和桌面启动入口。

#### Scenario: 巡检采集与入库路径
- **WHEN** 用户提供有效小红书 Cookie 并执行搜索
- **THEN** 系统展示候选帖子，支持查看候选详情、勾选帖子并保存到本地帖子库

#### Scenario: 巡检帖子库浏览路径
- **WHEN** 帖子库存在至少一条帖子
- **THEN** 系统支持按公司切换、按岗位筛选、打开详情弹层和删除帖子

#### Scenario: 巡检分析与大模型路径
- **WHEN** 帖子库存在可分析内容并配置了大模型参数
- **THEN** 系统可以生成规则分析报告，并可请求大模型生成回答或专题题库

### Requirement: 巡检结果可追踪
系统 SHALL 在执行功能巡检后记录检查结果、失败项和后续处理建议。

#### Scenario: 巡检全部通过
- **WHEN** 构建、后端测试、首页访问和手动功能路径均无异常
- **THEN** 系统在最终输出中列出通过项和运行命令

#### Scenario: 巡检发现异常
- **WHEN** 任一检查项失败
- **THEN** 系统记录失败命令、错误摘要和建议修复方向，并优先修复阻塞核心路径的问题
