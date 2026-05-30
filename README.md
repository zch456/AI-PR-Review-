# AI PR Review 助手

AI PR Review 助手是一个网页端 Pull Request 代码评审辅助工具。用户输入 GitHub PR 链接后，系统会逐步完成 PR 信息获取、变更总结、风险代码识别和 Review 建议生成。

当前阶段实现了项目骨架、GitHub PR URL 解析、PR 元信息获取、变更文件获取和规则化风险预检查闭环：前端提交 PR 链接，后端解析出仓库 owner、仓库名和 PR 编号，并从 GitHub API 获取 PR 标题、作者、状态、分支、增删行、变更文件数量和文件级 patch，再基于变更文件生成风险提示。

## 技术栈

- 前端：React、Vite、TypeScript
- 后端：Python、FastAPI、Pydantic、pytest
- GitHub 接入：GitHub REST API、httpx
- 后续 AI 接入：OpenAI-compatible API

## 本阶段功能

- 输入 GitHub PR 链接。
- 调用后端 `/api/analyze-pr`。
- 校验并解析 `https://github.com/{owner}/{repo}/pull/{number}` 格式链接。
- 从 GitHub API 获取公开 PR 的基础元信息。
- 从 GitHub API 获取 changed files 和 patch。
- 基于规则识别依赖、配置、鉴权、测试删除、大文件变更和疑似敏感信息风险。
- 在页面展示 owner、repo、PR 编号、标题、作者、状态、分支、增删行、变更文件数量、整体风险、风险提示和文件列表。

## 后端启动

```bash
cd api
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --reload
```

后端默认运行在 `http://127.0.0.1:8000`。

## 前端启动

```bash
cd web
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，并通过 Vite proxy 转发 `/api` 请求到后端。

## GitHub API 说明

当前版本使用 GitHub 公开 REST API 获取 PR 元信息和变更文件。分析公开仓库 PR 时不需要额外配置 token。后续如果要支持私有仓库或更高频率请求，需要增加 GitHub token 配置。

## 测试

后端测试：

```bash
cd api
./.venv/bin/python -m pytest -q
```

前端构建检查：

```bash
cd web
npm run build
```

## 依赖与原创说明

本项目使用 React、Vite、TypeScript、FastAPI、Pydantic、pytest、httpx 等开源依赖。项目中的 PR URL 解析、GitHub 元信息映射、接口设计、页面交互和后续 AI Review 流程为本项目原创实现。

## 后续计划

- 接入 OpenAI-compatible 模型生成 Review 建议。
- 展示结构化 Review 报告。
- 支持 Markdown 导出。
