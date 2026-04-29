## ADDED Requirements

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
