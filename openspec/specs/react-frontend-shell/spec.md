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
- **THEN** 系统能发现 React 源码语法、类型或构建错误

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
- **THEN** 系统保留 `index.html`、`src/main.jsx` 和 React 源码结构作为当前前端入口，不再保留旧 `app.js` 作为备用入口

#### Scenario: 发布仓库后复现运行
- **WHEN** 新环境克隆 GitHub 仓库并按 README 运行
- **THEN** 系统通过 `npm install`、`npm run build` 和 `python local_app_server.py` 启动 React 版本应用
