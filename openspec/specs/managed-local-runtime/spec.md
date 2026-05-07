# managed-local-runtime Specification

## Purpose

定义 OfferScope 的本地托管运行方式，包括桌面启动器、健康检查、失败提示和退出清理。

## Requirements

### Requirement: 本地运行时自动启动服务
系统 SHALL 提供一种受支持的运行方式，在用户进入 UI 前自动启动本地后端服务。

#### Scenario: 无需终端命令即可启动应用
- **WHEN** 用户打开受支持的桌面运行入口
- **THEN** 运行时自动启动本地后端服务，而不要求用户手动执行 shell 命令

#### Scenario: 仅在后端健康后展示主界面
- **WHEN** 运行时启动应用
- **THEN** 它在展示主工作流 UI 之前验证后端健康检查接口已经可用

### Requirement: 运行时清晰暴露启动失败
系统 SHALL 在后端启动失败时向用户提供清晰提示，而不是让 UI 进入看似可用但实际损坏的状态。

#### Scenario: 启动时出现依赖或端口错误
- **WHEN** 后端因缺少依赖、端口被占用或运行时异常而启动失败
- **THEN** 运行时展示明确的启动错误信息，而不是打开一个误导性的“已就绪”界面

### Requirement: 保留现有开发兜底启动方式
系统 SHALL 保留一个可文档化的兜底启动路径，供开发和故障恢复场景使用。

#### Scenario: 使用兜底本地服务命令
- **WHEN** 开发者选择不使用托管运行时
- **THEN** 现有本地服务启动方式仍然可用，并作为兜底工作流写入文档

### Requirement: 托管运行时退出时清理后台服务
系统 SHALL 在托管运行时正常退出时，清理其启动的后台服务线程或进程。

#### Scenario: 关闭桌面运行时窗口
- **WHEN** 用户关闭托管运行时窗口
- **THEN** 运行时会干净地关闭后端服务，避免留下孤儿后台进程

### Requirement: 桌面启动器兼容 FastAPI 后端
系统 SHALL 在后端迁移到 FastAPI 后继续通过桌面启动器自动启动和关闭本地服务。

#### Scenario: 双击启动脚本
- **WHEN** 用户双击 `start_offerscope.cmd`
- **THEN** 系统启动 FastAPI 后端并打开本地 React 应用页面

#### Scenario: 关闭桌面窗口
- **WHEN** 用户关闭桌面应用窗口
- **THEN** 系统清理本地 FastAPI 服务进程，避免后台残留

### Requirement: 启动失败提示可读
系统 SHALL 在 FastAPI 依赖缺失或端口占用时提供可读的错误提示。

#### Scenario: 依赖缺失
- **WHEN** 用户启动应用但 FastAPI 或 Uvicorn 未安装
- **THEN** 系统提示需要安装 Python 依赖，并给出 README 中的安装命令

#### Scenario: 端口占用
- **WHEN** 默认端口已被其他进程占用
- **THEN** 系统选择可用端口或提示用户当前端口冲突
