# OfferScope 小红书面经分析台

OfferScope 是一个面向求职场景的本地分析工作台，支持：

- 通过本地 Python/FastAPI 服务调用小红书搜索与详情能力
- 在前端候选池中筛选帖子，再手动入库
- 基于本地帖子库做规则分析、专题题库整理和大模型总结
- 使用“面试 Agent”进行问题分类、上下文检索、结构化回答和追问
- 将帖子、配置、知识索引和会话历史持久化到本地 SQLite

如果你在继续推进架构演进，建议先看：
- [docs/project-refactor-guide.md](docs/project-refactor-guide.md)

## 技术栈

- 前端：React 19 + Vite
- 本地后端：FastAPI + Uvicorn
- 存储：SQLite
- 小红书采集能力：`XhsSkills-master/skills/xhs-apis`

## 目录概览

```text
demo_xiaohongshu/
├─ backend/                 # FastAPI 应用、路由、服务、仓储
├─ src/                     # React 前端
├─ data/                    # 本地 SQLite 数据文件
├─ XhsSkills-master/        # 小红书技能运行时
├─ local_app_server.py      # 兼容启动入口
├─ desktop_launcher.py      # 桌面启动器
└─ start_offerscope.cmd     # Windows 双击启动脚本
```

## 安装依赖

先安装前端依赖并构建：

```powershell
cd d:\codex\demo_xiaohongshu
npm install
npm run build
```

再安装 Python 依赖：

```powershell
cd d:\codex\demo_xiaohongshu
python -m pip install -r requirements.txt
```

如果你需要桌面窗口模式，再安装：

```powershell
python -m pip install pywebview
```

如果你要直接调用小红书技能，还需要安装技能依赖：

```powershell
python -m pip install -r .\XhsSkills-master\skills\xhs-apis\scripts\requirements.txt
cd .\XhsSkills-master\skills\xhs-apis\scripts
npm install
```

## 启动方式

### 方式一：桌面启动器

直接双击：

- [start_offerscope.cmd](start_offerscope.cmd)

它会：

1. 启动本地 FastAPI 服务
2. 等待 `/api/health` 就绪
3. 打开桌面窗口
4. 在退出时关闭后端服务

### 方式二：仅启动本地服务

```powershell
cd d:\codex\demo_xiaohongshu
python local_app_server.py
```

默认地址：

- `http://127.0.0.1:8080`
- `http://127.0.0.1:8080/api/health`

### 方式三：前后端联调开发

启动后端：

```powershell
cd d:\codex\demo_xiaohongshu
python local_app_server.py
```

另开一个终端启动 Vite：

```powershell
cd d:\codex\demo_xiaohongshu
npm run dev
```

开发地址：

- 前端：`http://127.0.0.1:5173`
- 本地 API：`http://127.0.0.1:8080`

## 数据存储

默认数据库文件：

- `data/offerscope.db`

其中保存：

- 帖子库
- `xhsConfig`
- `llmConfig`
- 题目抽取结果
- 知识点索引
- Agent 会话与消息历史
- schema 版本和迁移元数据

`data/*.db` 已被 `.gitignore` 排除，不会默认提交到仓库。

## 主要接口

### 健康检查

- `GET /api/health`

### 本地存储

- `GET /api/storage/bootstrap`
- `GET /api/storage/posts`
- `PUT /api/storage/posts`
- `GET /api/storage/settings`
- `PUT /api/storage/settings/xhsConfig`
- `PUT /api/storage/settings/llmConfig`
- `POST /api/storage/import-local`

### 小红书采集

- `POST /api/xhs/search`
- `POST /api/xhs/note-detail`

### 面试 Agent

- `POST /api/agent/classify`
- `POST /api/agent/retrieve`
- `POST /api/agent/answer`
- `POST /api/agent/follow-up`
- `GET /api/agent/sessions`
- `GET /api/agent/sessions/{session_id}`

## 前端页面

- `采集`：关键词搜索、分页加载、候选池筛选、详情抽屉、手动入库
- `帖子库`：按公司/岗位浏览帖子，查看全文，删除或载入草稿
- `分析`：关键词统计、常见问题、专题题库、Markdown 报告
- `大模型`：预设模型配置、问答和总结
- `面试 Agent`：分类、检索、结构化回答、追问、历史会话

## 测试

后端测试：

```powershell
cd d:\codex\demo_xiaohongshu
python -m unittest test_local_app_server.py
```

这组测试覆盖：

- SQLite repository 初始化与去重
- bootstrap payload
- 旧数据导入
- 存储路由读写
- XHS 路由兼容
- Agent 基础分类接口

前端构建检查：

```powershell
cd d:\codex\demo_xiaohongshu
npm run build
```

本地 smoke test 建议：

```powershell
cd d:\codex\demo_xiaohongshu
python local_app_server.py
```

然后访问：

- `http://127.0.0.1:8080`
- `http://127.0.0.1:8080/api/health`

## 兼容说明

- `local_app_server.py` 仍然保留旧入口，历史命令可以继续使用
- 首次启动时，如果检测到旧版 `localStorage` 数据，会尝试迁移到 SQLite
- 前端默认通过 `/api` 与本地后端通信

## 注意事项

- 小红书搜索和详情接口依赖有效的 cookies
- 大模型回答依赖你在页面里配置的 API Key、Base URL 和模型名
- 本项目默认不做代理图片缓存，封面图加载失败时前端会回退到占位图
