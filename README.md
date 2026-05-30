# AI PR Review 助手

AI PR Review 助手是一个网页端 Pull Request 代码评审辅助工具。用户输入 GitHub PR 链接后，系统会逐步完成 PR 信息获取、变更总结、风险代码识别和 Review 建议生成。

当前阶段实现了项目骨架、GitHub PR URL 解析、PR 元信息获取、变更文件获取、规则化风险预检查和 AI Review 报告生成：前端提交 PR 链接，后端解析仓库 owner、仓库名和 PR 编号，从 GitHub API 获取 PR 元信息和文件级 patch，生成规则风险提示，并可调用 DeepSeek 生成结构化 Review 总结和建议。

## 技术栈

- 前端：React、Vite、TypeScript
- 后端：Python、FastAPI、Pydantic、pytest
- GitHub 接入：GitHub REST API、httpx
- AI 接入：DeepSeek Chat Completions API

## 本阶段功能

- 输入 GitHub PR 链接。
- 调用后端 `/api/analyze-pr`。
- 校验并解析 `https://github.com/{owner}/{repo}/pull/{number}` 格式链接。
- 从 GitHub API 获取公开 PR 的基础元信息。
- 从 GitHub API 获取 changed files 和 patch。
- 基于规则识别依赖、配置、鉴权、测试删除、大文件变更和疑似敏感信息风险。
- 调用 AI 生成 PR 变更总结和 Review 发现项。
- 在页面展示 owner、repo、PR 编号、标题、作者、状态、分支、增删行、变更文件数量、整体风险、风险提示、文件列表和 AI Review 报告。
- 支持导出 Markdown 报告。

## 后端启动

```bash
cd api
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
./.venv/bin/python -m uvicorn app.main:app --reload
```

后端默认运行在 `http://127.0.0.1:8000`。

如需生成 AI Review，需要先配置 DeepSeek 环境变量：

```bash
export DEEPSEEK_API_KEY="你的 DeepSeek API Key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com"
export DEEPSEEK_MODEL="deepseek-chat"
```

`DEEPSEEK_API_KEY` 不应写入代码或提交到仓库。

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

本项目使用 React、Vite、TypeScript、FastAPI、Pydantic、pytest、httpx 等开源依赖。项目中的 PR URL 解析、GitHub 元信息映射、规则风险预检查、AI Review 适配、接口设计和页面交互为本项目原创实现。

## 后续计划

- 支持 GitHub token 以分析私有仓库和降低限流影响。
- 增加更细粒度的风险规则和可配置规则集。
- 支持将选中的 Review 建议发布回 GitHub PR。
