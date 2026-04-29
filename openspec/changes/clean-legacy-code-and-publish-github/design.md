## Context

当前项目已经完成 React + Vite 重构，生产运行入口变为 `dist/` 构建产物加 `local_app_server.py` 本地服务。根目录仍保留旧版全局脚本、历史测试脚本、日志和早期中文文档，其中一部分已不再被 React 入口引用。

这次变更同时涉及文件清理和 GitHub 发布，属于跨切面的仓库治理工作。删除文件前必须先证明它们不再被当前构建、后端服务和文档引用；发布前必须排除本地数据库、Cookie、API Key、依赖目录和构建缓存。

## Goals / Non-Goals

**Goals:**

- 建立发布前清理清单，区分“可删除”“需保留”“需确认”的文件。
- 删除旧版非 React 前端入口和临时日志，避免公开仓库出现多套前端入口。
- 增加或更新 `.gitignore`，确保敏感数据和本地生成物不会进入 GitHub。
- 验证清理后的 React 构建、后端测试和本地服务启动链路。
- 初始化或整理 Git 仓库，并发布到用户 GitHub 主页下的目标仓库。

**Non-Goals:**

- 不重构业务功能和 UI。
- 不修改现有 `/api/*` 接口、SQLite schema 或小红书脚本调用方式。
- 不提交 `data/offerscope.db` 中的真实本地数据。
- 不自动公开用户未确认的 GitHub 仓库名、远程地址或账号配置。

## Decisions

1. 以引用检查决定删除范围。

   删除前使用 `rg` 检查旧文件名、全局对象名和脚本引用，只有当前 React 构建、Python 服务、README 和 OpenSpec 都不依赖的文件才删除。这样比按文件名猜测更安全。

2. 旧前端文件一次性移除，文档中保留历史说明。

   旧 `app.js`、`router.js`、`store.js` 等文件不再作为运行入口保留；如果需要解释迁移背景，放到 `docs/project-refactor-guide.md`，而不是保留可执行旧代码。

3. `dist/` 默认不提交。

   GitHub 仓库应以源码为准，通过 `npm install && npm run build` 复现构建。`local_app_server.py` 支持托管 `dist/`，但 `dist/` 属于生成物，默认进入 `.gitignore`。

4. 本地数据和敏感配置不得提交。

   `data/*.db`、日志、环境文件、Cookie、API Key、`node_modules/` 必须被 `.gitignore` 排除。README 只描述配置方式，不包含真实凭据。

5. GitHub 发布使用最小可审计流程。

   先确认 Git 状态和远程目标，再提交、推送并创建或更新 GitHub 仓库。若当前目录不是 Git 仓库，需要初始化 Git；若用户未提供仓库名，则执行阶段暂停确认。

## Risks / Trade-offs

- [Risk] 误删仍被隐式使用的旧文件 → Mitigation：删除前做 `rg` 引用检查，删除后跑 `npm run build`、后端 unittest 和本地服务 smoke test。
- [Risk] 将本地数据库或密钥上传到 GitHub → Mitigation：先更新 `.gitignore`，再用 `git status --short` 核对待提交文件。
- [Risk] 用户希望保留某些历史文档但被清理 → Mitigation：实现时仅删除明确的旧代码和日志；中文需求/技术文档默认保留，除非用户明确要求删除。
- [Risk] GitHub 目标仓库不明确 → Mitigation：执行阶段在推送前确认仓库名、可见性和远程地址。
- [Risk] 清理后无法回滚 → Mitigation：删除前如已有 Git 仓库，先查看状态；若未初始化 Git，先创建初始提交或至少保留 OpenSpec 清单，避免无记录删除。
