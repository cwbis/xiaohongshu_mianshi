# react-frontend-shell Specification

## Purpose

定义 OfferScope React 前端工作台的核心能力、运行边界和与本地 Python API 的兼容要求。

## Requirements

### Requirement: React 前端工作台保持现有页面能力
系统 SHALL 使用 React 实现 OfferScope 前端工作台，并保持采集、帖子库、分析和大模型四个页面的主要用户能力。

#### Scenario: 用户访问采集页
- **WHEN** 用户进入 React 版采集页
- **THEN** 系统展示公司、岗位、搜索关键词、Cookies、页码、每页条数和排序控件，并支持搜索、刷新、加载更多、分页、候选详情和入库操作

#### Scenario: 用户访问帖子库页
- **WHEN** 用户进入 React 版帖子库页
- **THEN** 系统展示已入库帖子，并支持按公司选择、按岗位筛选、查看详情、导入、导出、删除和载入草稿

#### Scenario: 用户访问分析和大模型页面
- **WHEN** 用户进入 React 版分析页或大模型页
- **THEN** 系统继续支持规则分析、专题题库、大模型配置、问题回答和总结展示

### Requirement: React 前端兼容现有本地 API
系统 SHALL 继续通过现有本地 API 与 Python 服务通信，不要求修改 SQLite schema 或现有 API 路径。

#### Scenario: React 前端加载本地数据
- **WHEN** React 应用启动
- **THEN** 系统调用 `/api/storage/bootstrap` 获取帖子、设置和存储元数据

#### Scenario: React 前端保存数据
- **WHEN** 用户修改帖子库、`xhsConfig` 或 `llmConfig`
- **THEN** 系统继续调用 `/api/storage/posts` 或 `/api/storage/settings/<scope>` 保存数据

#### Scenario: React 前端调用小红书能力
- **WHEN** 用户搜索帖子或加载帖子详情
- **THEN** 系统继续调用 `/api/xhs/search` 或 `/api/xhs/note-detail`

### Requirement: React 前端状态按业务域拆分
系统 SHALL 将旧前端全局状态拆分为面向业务域的 React 状态，避免将旧 `app.js` 的单一全局状态原样迁移。

#### Scenario: 开发者维护搜索功能
- **WHEN** 开发者修改搜索候选池逻辑
- **THEN** 相关状态位于采集业务域内，而不是散落在无边界的全局对象中

#### Scenario: 开发者维护帖子库功能
- **WHEN** 开发者修改帖子库公司筛选、岗位筛选或详情弹层
- **THEN** 相关状态位于帖子库业务域内，并通过清晰 action 或 hook 更新

### Requirement: React 构建产物可由本地 Python 服务托管
系统 SHALL 提供构建后的静态前端产物，并让现有本地服务或桌面启动器可以打开 React 应用。

#### Scenario: 用户使用默认启动方式
- **WHEN** 用户通过 `start_offerscope.cmd` 或 `desktop_launcher.py` 启动应用
- **THEN** 系统打开 React 版前端，并保持本地 API 可用

#### Scenario: 开发者执行生产构建
- **WHEN** 开发者运行前端构建命令
- **THEN** 系统生成可被 Python 静态服务托管的前端产物

### Requirement: React 重构保留数据迁移和持久化行为
系统 SHALL 保留当前 SQLite bootstrap、旧 `localStorage` 数据迁移和本地配置持久化行为。

#### Scenario: 数据库为空且存在旧浏览器数据
- **WHEN** React 应用启动且后端返回尚未完成旧数据迁移
- **THEN** 系统读取旧 `localStorage` 快照并调用 `/api/storage/import-local` 导入

#### Scenario: 用户配置大模型或小红书搜索参数
- **WHEN** 用户修改 `llmConfig` 或 `xhsConfig`
- **THEN** 系统将配置持久化到 SQLite，并在下次启动时恢复

### Requirement: React 重构提供回归验证入口
系统 SHALL 提供覆盖 React 前端核心行为的轻量验证入口，并保留后端现有测试。

#### Scenario: 开发者验证前端构建
- **WHEN** 开发者运行前端检查或构建命令
- **THEN** 系统能够发现 React 源码语法、类型或构建错误

#### Scenario: 开发者验证本地服务
- **WHEN** 开发者运行 `python -m unittest test_local_app_server.py`
- **THEN** 后端存储、健康检查和 bootstrap 行为继续通过测试

### Requirement: React 版本成为唯一前端运行入口
系统 SHALL 在仓库发布前移除旧版非 React 前端运行入口，避免新旧前端同时存在造成维护混淆。

#### Scenario: 用户从本地服务访问首页
- **WHEN** 用户访问 Python 本地服务首页
- **THEN** 系统只加载 React 入口和 React 构建产物，不再加载旧版全局脚本入口

#### Scenario: 开发者查看根目录
- **WHEN** 开发者查看项目根目录的前端入口文件
- **THEN** 系统保留 `index.html`、`src/main.jsx` 和 React 源码结构作为当前前端入口

#### Scenario: 发布仓库后复现运行
- **WHEN** 新环境克隆 GitHub 仓库并按 README 运行
- **THEN** 系统通过 `npm install`、`npm run build` 和 `python local_app_server.py` 启动 React 版本应用

### Requirement: 帖子图片加载失败时保持可浏览
系统 SHALL 在帖子图片缺失、过期或加载失败时显示稳定的占位封面，且不破坏采集候选卡片、帖子库卡片或详情页布局。

#### Scenario: 采集候选图片加载失败
- **WHEN** 采集候选结果包含不可访问的 `coverUrl`
- **THEN** 系统在候选卡片中显示占位封面，并保留标题、作者、发布时间和入库操作

#### Scenario: 帖子库卡片图片加载失败
- **WHEN** 已入库帖子图片加载失败
- **THEN** 系统在帖子库卡片中显示占位封面，并保留公司、岗位、标题和交互信息

#### Scenario: 详情页图片加载失败
- **WHEN** 用户打开帖子详情且图片不可访问
- **THEN** 系统显示占位视觉区域和完整正文内容，详情页仍可滚动和关闭

### Requirement: 图片加载问题可诊断
系统 SHALL 提供足够的运行时信号，帮助判断图片失败来自空 URL、远端拒绝、网络错误还是前端展示逻辑。

#### Scenario: 图片 URL 为空
- **WHEN** 帖子没有 `coverUrl`
- **THEN** 系统直接显示占位封面，不发起无效图片请求

#### Scenario: 图片请求失败
- **WHEN** 浏览器触发图片加载错误
- **THEN** 系统将该图片标记为失败状态，并在当前卡片或详情页展示降级视觉

### Requirement: 图片代理保持可选
系统 SHALL 仅在确认外链限制影响主要浏览体验时新增本地图像代理能力，且代理能力必须限制协议、超时和响应类型。

#### Scenario: 不需要图片代理
- **WHEN** 前端降级已能满足浏览体验
- **THEN** 系统不新增后端图片代理接口

#### Scenario: 需要图片代理
- **WHEN** 多数有效图片因外链限制无法在浏览器直接显示
- **THEN** 系统可以新增受限的 `/api/image-proxy` 能力，并确保非图片内容或非法 URL 被拒绝

### Requirement: React 前端提供面试 Agent 页面
系统 SHALL 在现有 React 前端中新增“面试 Agent”页面，用于提问、查看分类、查看检索来源、阅读结构化回答和继续追问。

#### Scenario: 进入面试 Agent 页面
- **WHEN** 用户从应用导航进入“面试 Agent”
- **THEN** 系统展示问题输入区、回答区、上下文来源区和追问入口

#### Scenario: 发送首次问题
- **WHEN** 用户输入面试问题并点击生成
- **THEN** 前端调用 `/api/agent/answer`，并展示知识领域、标签、回答结构和来源列表

#### Scenario: 继续追问
- **WHEN** 用户在已有回答后输入追问
- **THEN** 前端调用追问接口并将回复追加到当前会话中

### Requirement: 面试 Agent 复用现有帖子库和模型配置
系统 SHALL 让面试 Agent 使用当前本地帖子库、公司/岗位上下文和大模型配置。

#### Scenario: 使用现有大模型配置
- **WHEN** 用户已经在大模型页面配置供应商、模型、Base URL 和 API Key
- **THEN** 面试 Agent 使用同一份本地配置发起回答请求

#### Scenario: 使用公司和岗位过滤
- **WHEN** 用户在帖子库中选择了公司或岗位范围
- **THEN** 面试 Agent 可以将该范围作为检索上下文过滤条件

### Requirement: 回答展示适合复习
系统 SHALL 以适合面试复习的方式展示 Agent 回答。

#### Scenario: 展示结构化回答
- **WHEN** Agent 返回回答结果
- **THEN** 前端展示一句话总结、分点回答、项目落地、易错点、可能追问和来源列表
