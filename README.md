# AI PR Review 助手

AI PR Review 助手是一个网页端 Pull Request 代码评审辅助工具。用户输入 GitHub PR 链接后，系统会逐步完成 PR 信息获取、变更总结、风险代码识别和 Review 建议生成。

当前阶段实现了项目骨架和 GitHub PR URL 解析闭环：前端提交 PR 链接，后端解析出仓库 owner、仓库名和 PR 编号。

## 技术栈

- 前端：React、Vite、TypeScript
- 后端：Python、FastAPI、Pydantic、pytest
- 后续 AI 接入：OpenAI-compatible API

## 本阶段功能

- 输入 GitHub PR 链接。
- 调用后端 `/api/analyze-pr`。
- 校验并解析 `https://github.com/{owner}/{repo}/pull/{number}` 格式链接。
- 在页面展示 owner、repo 和 PR 编号。

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

本项目使用 React、Vite、TypeScript、FastAPI、Pydantic、pytest 等开源依赖。项目中的 PR URL 解析、接口设计、页面交互和后续 AI Review 流程为本项目原创实现。

## 后续计划

- 接入 GitHub API 获取 PR 元信息。
- 获取 changed files 和 patch diff。
- 增加规则化风险预检查。
- 接入 OpenAI-compatible 模型生成 Review 建议。
- 展示结构化 Review 报告。
- 支持 Markdown 导出。
