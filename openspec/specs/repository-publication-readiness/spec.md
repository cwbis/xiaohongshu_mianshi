# repository-publication-readiness Specification

## Purpose

定义 OfferScope 发布到 GitHub 前的仓库清理、敏感数据排除、验证和发布要求。

## Requirements

### Requirement: 仓库发布前清理旧代码
系统 SHALL 在发布到 GitHub 前清理不再参与当前 React 版本运行的旧代码和临时文件，并保留当前可运行源码、测试、文档和 OpenSpec 主规格。

#### Scenario: 删除旧版全局前端入口
- **WHEN** 当前 React 构建、Python 服务和文档均不再引用旧版全局前端文件
- **THEN** 系统移除旧 `app.js`、`router.js`、`store.js`、`xhs-service.js`、`llm-service.js`、`analysis-core.js`、`analysis-ai-service.js` 和 `model-presets.js`

#### Scenario: 保留当前运行所需文件
- **WHEN** 执行清理
- **THEN** 系统保留 `src/`、`index.html`、`package.json`、`vite.config.js`、`local_app_server.py`、`desktop_launcher.py`、`start_offerscope.cmd`、测试文件、README、docs 和 openspec 主规格

#### Scenario: 删除临时输出文件
- **WHEN** 发现运行日志、错误日志或测试输出文件
- **THEN** 系统删除这些临时文件，并确保后续通过 `.gitignore` 排除同类文件

### Requirement: 仓库不得提交本地敏感数据和生成物
系统 SHALL 在 GitHub 发布前排除本地数据、密钥、依赖目录、构建产物和运行缓存。

#### Scenario: 更新 Git 忽略规则
- **WHEN** 准备提交到 GitHub
- **THEN** `.gitignore` 包含 `node_modules/`、`dist/`、`data/*.db`、日志文件、环境变量文件和本地缓存目录

#### Scenario: 检查待提交文件
- **WHEN** 执行 Git 提交前检查
- **THEN** 系统展示待提交文件清单，并确认其中不包含 Cookie、API Key、SQLite 数据库、`node_modules/` 或构建产物

### Requirement: 清理后必须保持项目可运行
系统 SHALL 在删除旧代码后验证 React 构建、本地服务测试和服务首页托管行为。

#### Scenario: 验证 React 构建
- **WHEN** 旧前端代码被删除后
- **THEN** `npm run build` 继续成功生成 React 构建产物

#### Scenario: 验证本地 Python 服务
- **WHEN** 旧前端代码被删除后
- **THEN** `python -m unittest test_local_app_server.py` 继续通过

#### Scenario: 验证本地首页可访问
- **WHEN** Python 本地服务启动
- **THEN** 首页返回 React 应用页面，且 `/api/health` 返回成功响应

### Requirement: 项目可发布到用户 GitHub 主页仓库
系统 SHALL 支持将清理后的当前项目发布到用户 GitHub 账号下的目标仓库。

#### Scenario: 当前目录不是 Git 仓库
- **WHEN** 执行发布流程且当前目录尚未初始化 Git
- **THEN** 系统初始化 Git 仓库，创建首个提交，并配置用户确认的 GitHub 远程仓库

#### Scenario: 当前目录已有 Git 仓库
- **WHEN** 执行发布流程且当前目录已有 Git 仓库
- **THEN** 系统保留现有历史，基于当前分支创建清理提交，并推送到用户确认的 GitHub 远程仓库

#### Scenario: GitHub 目标信息不明确
- **WHEN** 用户未提供仓库名、可见性或远程地址
- **THEN** 系统在推送前暂停并要求用户确认，不得猜测发布目标
