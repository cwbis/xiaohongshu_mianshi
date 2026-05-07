## Why

React 版本已经发布到 GitHub，但还需要做一次完整功能巡检，确认采集、帖子库、分析、大模型、本地启动和数据持久化都能正常工作。用户反馈帖子图片有时加载不出来，可能影响帖子库浏览体验，需要集中排查图片 URL、跨域、防盗链、降级占位和详情页展示逻辑。

## What Changes

- 建立一套可重复的本地功能巡检流程，覆盖构建、后端测试、启动、页面访问、API 健康检查和核心用户路径。
- 排查帖子图片加载失败原因，包括 `coverUrl` 数据是否为空、URL 是否过期、图片站点是否限制外链、React 图片组件是否缺少错误降级。
- 修复帖子卡片和详情页图片展示策略：图片加载失败时不破坏布局，并显示可读的占位卡片。
- 如有必要，在本地 Python 服务中新增轻量图片代理或图片可用性检测，减少外链防盗链导致的加载失败。
- 补充测试或 smoke check，确保清理后的仓库和 React 版本仍可稳定启动。

## Capabilities

### New Capabilities

- `runtime-health-verification`: 定义项目功能巡检、启动验证、核心页面 smoke check 和回归验证要求。

### Modified Capabilities

- `react-frontend-shell`: 补充帖子图片加载失败时的前端降级显示和详情页体验要求。

## Impact

- 影响 React 帖子卡片、帖子详情弹层、采集候选卡片和图片加载相关样式。
- 可能影响 `local_app_server.py`，如果需要通过本地服务代理图片或检查图片可用性。
- 影响 README 或 docs 中的巡检说明。
- 不修改 SQLite schema，不改变 `/api/storage/*` 和 `/api/xhs/*` 的既有契约，除非确认需要新增可选图片代理接口。
