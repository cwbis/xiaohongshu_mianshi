# OfferScope 小红书面经分析台

OfferScope 是一个面向求职场景的本地分析工作台，支持“一键拉取小红书面经 + 本地帖子库 + 规则分析 + 大模型总结”。

如果后续要整体重构项目，先看这份梳理文档：
- [docs/project-refactor-guide.md](docs/project-refactor-guide.md)

当前版本已经支持：
- React + Vite 前端工作台，生产构建后由本地 Python 服务直接托管
- 通过本地 Python 服务调用小红书搜索与详情能力
- 直接搜索小红书帖子、刷新当前结果、继续加载更多候选内容
- 将帖子库、`xhsConfig`、`llmConfig` 持久化到本地 SQLite 数据库
- 在帖子库中按公司、岗位分组浏览帖子，并在分组内继续管理帖子
- 首次启动时把旧版浏览器 `localStorage` 数据自动迁移到 SQLite
- 生成关键词统计、常见问题、流程观察和 Markdown 报告

## 默认启动方式

如果是第一次拉起 React 版本，先安装并构建前端：

```powershell
cd d:\codex\demo_xiaohongshu
npm install
npm run build
```

### 方式一：桌面启动器

推荐直接双击：
- [start_offerscope.cmd](start_offerscope.cmd)

它会：
1. 启动本地后端服务
2. 等待 `/api/health` 就绪
3. 打开桌面运行入口
4. 在退出时关闭后端服务

对应 Python 启动器：
- [desktop_launcher.py](desktop_launcher.py)

说明：
- 桌面运行入口依赖 `pywebview`
- 如果缺少依赖，可执行：`python -m pip install pywebview`

## 开发兜底启动方式

如果你只是运行构建后的本地应用，可以继续使用 Python 服务：

```powershell
cd d:\codex\demo_xiaohongshu
python local_app_server.py
```

然后访问：
- `http://127.0.0.1:8080`

如果你要开发 React 页面，建议同时启动后端和 Vite：

```powershell
cd d:\codex\demo_xiaohongshu
python local_app_server.py
```

另开一个终端：

```powershell
cd d:\codex\demo_xiaohongshu
npm run dev
```

然后访问 Vite 地址：
- `http://127.0.0.1:5173`

Vite 已配置 `/api` 代理到 `http://127.0.0.1:8080`。

## 数据存储说明

当前版本不再依赖浏览器 `localStorage` 作为主存储。

默认数据文件位置：
- `data/offerscope.db`

存储内容包括：
- 帖子库
- `xhsConfig`
- `llmConfig`
- schema 版本与迁移元数据

注意：`data/*.db` 已被 `.gitignore` 排除，不会提交到 GitHub。

## 帖子库浏览方式

帖子库页面现在按公司优先浏览：
- 顶部公司导航：例如“美团”“腾讯”各自是一组
- 公司内岗位标签：例如“本地商业平台”“后端开发实习”是公司下面的子方向
- 内容区使用小红书式卡片网格，先横向填满，再向下延展

帖子库中可以继续执行这些操作：
- 查看详情
- 载入草稿
- 删除帖子

## 旧数据迁移

如果你的浏览器里还有旧版 `localStorage` 数据：
- 系统会在数据库为空且尚未完成迁移时自动尝试导入
- 迁移成功后会清理旧版浏览器存储键
- 后续读写统一走本地存储 API

## 关键本地接口

本地服务新增了这些持久化接口：
- `GET /api/storage/bootstrap`
- `GET /api/storage/posts`
- `PUT /api/storage/posts`
- `GET /api/storage/settings`
- `PUT /api/storage/settings/xhsConfig`
- `PUT /api/storage/settings/llmConfig`
- `POST /api/storage/import-local`

## 测试

已增加基础 Python 测试，覆盖：
- SQLite repository 初始化与去重逻辑
- bootstrap payload
- 旧数据导入
- 本地服务健康检查与 bootstrap 接口

运行方式：

```powershell
cd d:\codex\demo_xiaohongshu
python -m unittest test_local_app_server.py
```

前端构建检查：

```powershell
cd d:\codex\demo_xiaohongshu
npm run build
```

## 功能巡检

日常改动后建议依次检查：

```powershell
cd d:\codex\demo_xiaohongshu
npm run build
python -m unittest test_local_app_server.py
python local_app_server.py
```

然后访问：
- `http://127.0.0.1:8080`
- `http://127.0.0.1:8080/api/health`

需要人工确认的页面路径：
- 采集页：搜索表单、刷新、翻页、候选详情、勾选入库
- 帖子库：公司导航、岗位筛选、卡片网格、详情弹层、删除、载入草稿
- 分析页：规则分析报告、典型问题、专题题库入口
- 大模型页：供应商、模型、Base URL、API Key 和生成答案入口

## 图片加载说明

小红书图片可能因为 `coverUrl` 缺失、链接过期或外链限制加载失败。当前前端已经做了降级处理：
- 无图片或图片失败时，采集候选卡片显示占位封面
- 帖子库卡片显示小红书风格占位封面
- 详情页图片失败时仍保留视觉区域和正文滚动阅读

本项目暂不默认启用后端图片代理，避免引入开放代理和第三方图片缓存风险。
