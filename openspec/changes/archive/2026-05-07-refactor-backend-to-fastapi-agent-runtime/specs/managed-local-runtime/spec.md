## ADDED Requirements

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
