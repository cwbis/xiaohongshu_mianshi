# fastapi-local-runtime Specification

## Purpose

定义 OfferScope 基于 FastAPI 的本地服务入口、静态托管方式以及后端模块边界。

## Requirements

### Requirement: FastAPI 本地服务入口
系统 SHALL 使用 FastAPI 提供本地 HTTP API，并保留单入口的本地启动体验。

#### Scenario: 启动 FastAPI 本地服务
- **WHEN** 用户通过项目启动脚本启动应用
- **THEN** 系统启动 FastAPI 本地服务，并在本机端口提供 `/api/health` 和 React 首页

#### Scenario: 兼容旧启动命令
- **WHEN** 用户执行 README 中保留的兼容启动命令
- **THEN** 系统仍能启动新的 FastAPI 服务，而不要求用户理解后端迁移细节

### Requirement: 现有 API 路径保持兼容
系统 SHALL 在迁移到 FastAPI 后保持现有核心 API 路径和响应语义兼容。

#### Scenario: 读取启动数据
- **WHEN** React 前端请求 `GET /api/storage/bootstrap`
- **THEN** 系统返回帖子、设置和存储元数据，字段语义与迁移前保持兼容

#### Scenario: 保存帖子和设置
- **WHEN** React 前端调用 `PUT /api/storage/posts` 或 `PUT /api/storage/settings/<scope>`
- **THEN** 系统将数据保存到本地 SQLite，并返回兼容的保存结果

#### Scenario: 调用小红书能力
- **WHEN** React 前端调用 `POST /api/xhs/search` 或 `POST /api/xhs/note-detail`
- **THEN** 系统通过封装后的 XHS 服务执行现有采集逻辑，并返回兼容结果

### Requirement: React 构建产物托管
系统 SHALL 由 FastAPI 本地服务托管 React 生产构建产物，并在非 API 路径返回前端入口。

#### Scenario: 访问首页
- **WHEN** 用户访问本地服务根路径 `/`
- **THEN** 系统返回 React 应用入口页面

#### Scenario: 访问前端资源
- **WHEN** 浏览器请求 React 构建后的静态资源
- **THEN** 系统返回对应资源并保留正确的内容类型

### Requirement: 后端模块边界清晰
系统 SHALL 将 API 路由、业务服务、数据库访问和请求响应模型拆分为独立模块。

#### Scenario: 新增 API 能力
- **WHEN** 开发者新增一个后端能力
- **THEN** 系统将路由放在 `backend/api/`，业务逻辑放在 `backend/services/`，持久化逻辑放在 `backend/repositories/`

#### Scenario: 校验请求和响应
- **WHEN** API 接收请求或返回结构化响应
- **THEN** 系统使用 schema 描述关键字段和默认值
