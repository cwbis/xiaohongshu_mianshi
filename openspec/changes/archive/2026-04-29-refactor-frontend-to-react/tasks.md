## 1. React 工程搭建

- [x] 1.1 新增 Vite + React 工程配置，包括 `package.json`、构建脚本、开发脚本和 React 入口文件。
- [x] 1.2 建立 `src/` 目录结构，至少包含 `app/`、`pages/`、`components/`、`api/`、`domain/`、`styles/`。
- [x] 1.3 调整 `index.html` 或新增 React 入口 HTML，确保开发和生产构建都能加载 React 应用。
- [x] 1.4 配置开发环境 API proxy，使 React dev server 能访问本地 Python API。

## 2. 服务层与领域逻辑迁移

- [x] 2.1 将 `store.js` 能力迁移为 React 工程内的 storage API client，保持 `/api/storage/*` 契约不变。
- [x] 2.2 将 `xhs-service.js` 能力迁移为 React 工程内的 XHS API client，保持 `/api/xhs/*` 契约不变。
- [x] 2.3 将 `llm-service.js` 和 `model-presets.js` 迁移为 React 工程内模块，保持现有模型配置能力。
- [x] 2.4 将帖子记录归一化、帖子分组、搜索结果合并、日期处理等纯逻辑抽到 `src/domain/`。
- [x] 2.5 将规则分析和 AI payload 相关逻辑迁移或封装，避免 React 组件直接承载分析算法。

## 3. 应用状态与路由

- [x] 3.1 建立 React 应用根组件，完成 bootstrap、错误状态和基础布局。
- [x] 3.2 建立路由结构，保留采集、帖子库、分析、大模型四个页面入口。
- [x] 3.3 将旧全局 `state` 拆为业务域状态，覆盖 runtime、collect、library、analysis、llm。
- [x] 3.4 保留旧 `localStorage` 自动迁移流程，并确保启动时仍从 SQLite 恢复帖子和配置。

## 4. 页面迁移

- [x] 4.1 迁移采集页，支持搜索、刷新、加载更多、上一页、下一页、候选详情、勾选和入库。
- [x] 4.2 迁移帖子库页，支持公司导航、岗位筛选、卡片网格、详情弹层、导入、导出、删除和载入草稿。
- [x] 4.3 迁移分析页，支持关键词、常见问题、流程观察、专题题库和 Markdown 报告。
- [x] 4.4 迁移大模型页，支持供应商选择、模型选择、配置持久化、问题回答和总结展示。
- [x] 4.5 迁移现有核心样式到 React 工程，并清理旧全局样式中不再使用的部分。

## 5. 本地服务与运行入口

- [x] 5.1 调整 `local_app_server.py` 静态文件托管策略，使其能服务 React 构建产物。
- [x] 5.2 确认 `desktop_launcher.py` 和 `start_offerscope.cmd` 仍能打开 React 版应用。
- [x] 5.3 保留或明确停用旧全局脚本入口，避免新旧前端同时接管页面。
- [x] 5.4 更新 README 和 `docs/project-refactor-guide.md`，说明 React 开发、构建和运行方式。

## 6. 验证与回归

- [x] 6.1 增加或更新前端构建检查命令，确保 React 源码可构建。
- [x] 6.2 运行后端现有测试 `python -m unittest test_local_app_server.py`。
- [x] 6.3 验证搜索入库、帖子库浏览、分析、大模型配置和桌面启动主链路。
- [x] 6.4 清点可删除的旧前端文件和扩展桥接代码，记录后续清理项。
