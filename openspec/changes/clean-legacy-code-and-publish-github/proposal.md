## Why

React 重构已经完成，但项目根目录仍保留旧版全局脚本、历史日志和过渡文件，容易让后续维护者误判当前运行入口。现在需要在发布到 GitHub 前完成一次仓库级清理，确保公开仓库只保留当前可运行项目和必要历史说明。

## What Changes

- 清点并删除不再参与 React 版本运行的旧前端代码文件，例如旧 `app.js`、`router.js`、`store.js`、`xhs-service.js`、`llm-service.js`、`analysis-core.js`、`analysis-ai-service.js`、`model-presets.js`。
- 删除临时运行日志、测试输出等不应提交到 GitHub 的文件，例如 `server-test.log`、`server-test.err`。
- 明确保留当前 React 源码、Vite 配置、本地 Python 服务、SQLite schema 初始化逻辑、测试、README、OpenSpec 主规格和必要文档。
- 增加或更新 `.gitignore`，避免提交 `node_modules/`、`dist/`、本地 SQLite 数据库、日志和本机敏感配置。
- 在删除前形成可核对清单，避免误删仍被 React 或 Python 服务引用的文件。
- 发布项目到用户 GitHub 主页下的新仓库或指定仓库。
- **BREAKING**：旧版非 React 前端入口将被移除，后续运行方式以 React + Vite 构建和 Python 本地服务为准。

## Capabilities

### New Capabilities

- `repository-publication-readiness`: 约束仓库发布前的文件清理、敏感数据排除、GitHub 发布和可复现运行说明。

### Modified Capabilities

- `react-frontend-shell`: 明确 React 版本成为唯一前端入口，旧全局脚本不得再作为运行入口保留。

## Impact

- 影响根目录旧前端脚本、临时日志、`.gitignore`、README 和重构说明文档。
- 影响 Git 初始化、远程仓库配置、提交历史和 GitHub 发布流程。
- 不修改现有 `/api/*` 路径、SQLite schema 和 Python 后端业务接口。
- 不提交本地真实数据、Cookie、API Key、`node_modules/` 或构建缓存。
