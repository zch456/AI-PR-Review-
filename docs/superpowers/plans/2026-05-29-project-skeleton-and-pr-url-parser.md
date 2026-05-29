# 项目骨架与 PR URL 解析 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可运行的 React + FastAPI 项目骨架，并实现 GitHub PR URL 解析的第一条端到端调用链。

**Architecture:** 第一阶段只实现最小可运行闭环：前端输入 PR 链接，调用后端 `/api/analyze-pr`，后端解析出 `owner`、`repo`、`pullNumber` 并返回预览结果。GitHub API、风险分析和 LLM Review 暂不进入本计划，后续通过独立小 PR 增量实现。

**Tech Stack:** React、Vite、TypeScript、Python、FastAPI、Pydantic、pytest。

---

## 计划范围

本计划只覆盖第一个可运行里程碑：

- 后端 FastAPI 最小服务。
- GitHub PR URL 解析器。
- `/api/health` 健康检查接口。
- `/api/analyze-pr` 解析预览接口。
- 前端最小输入页。
- 中文 README 快速开始草稿。

不在本计划中实现：

- GitHub API 数据拉取。
- PR diff 获取。
- 风险代码识别。
- LLM Review 生成。
- Markdown 导出。
- GitHub 自动评论。

这些功能会在后续计划中按小 PR 拆分。

## 文件结构

本计划将创建或修改以下文件：

- 创建: `.gitignore`
  - 负责忽略 Python、Node、本地环境变量和构建产物。
- 创建: `README.md`
  - 负责中文项目介绍、第一阶段启动方式和依赖说明。
- 创建: `api/requirements.txt`
  - 负责后端 Python 依赖声明。
- 创建: `api/pytest.ini`
  - 负责 pytest 搜索路径和测试目录配置。
- 创建: `api/app/__init__.py`
  - 标记 `app` 为 Python 包。
- 创建: `api/app/main.py`
  - FastAPI 应用入口，包含健康检查和 PR URL 解析预览接口。
- 创建: `api/app/pr_url_parser.py`
  - 纯函数模块，负责解析 GitHub PR 链接。
- 创建: `api/app/schemas.py`
  - 请求和响应数据结构。
- 创建: `api/tests/test_health.py`
  - 测试健康检查接口。
- 创建: `api/tests/test_pr_url_parser.py`
  - 测试 PR URL 解析规则。
- 创建: `api/tests/test_analyze_pr_endpoint.py`
  - 测试 `/api/analyze-pr` 的成功和失败响应。
- 创建: `web/package.json`
  - 前端依赖和脚本。
- 创建: `web/index.html`
  - Vite HTML 入口。
- 创建: `web/tsconfig.json`
  - 前端 TypeScript 配置。
- 创建: `web/tsconfig.node.json`
  - Vite 配置文件的 TypeScript 配置。
- 创建: `web/vite.config.ts`
  - Vite 配置和 `/api` 代理。
- 创建: `web/src/main.tsx`
  - React 入口。
- 创建: `web/src/App.tsx`
  - 第一阶段主界面。
- 创建: `web/src/styles.css`
  - 第一阶段界面样式。

---

### 任务 1: 后端健康检查骨架

**文件：**
- 创建: `api/requirements.txt`
- 创建: `api/pytest.ini`
- 创建: `api/app/__init__.py`
- 创建: `api/app/main.py`
- 创建: `api/tests/test_health.py`

- [ ] **步骤 1: 创建后端依赖声明**

创建 `api/requirements.txt`:

```txt
fastapi==0.115.6
uvicorn[standard]==0.32.1
pytest==8.3.4
httpx==0.28.1
```

- [ ] **步骤 2: 创建 pytest 配置**

创建 `api/pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **步骤 3: 创建包入口**

创建 `api/app/__init__.py`:

```python
"""AI PR Review Assistant API package."""
```

- [ ] **步骤 4: 编写失败测试**

创建 `api/tests/test_health.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_returns_ok_status() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **步骤 5: 安装依赖**

运行：

```bash
cd api
python3 -m venv .venv
./.venv/bin/python -m pip install -r requirements.txt
```

预期： pip 安装完成，最后输出不包含 `ERROR`。

- [ ] **步骤 6: 运行测试确认失败**

运行：

```bash
cd api
./.venv/bin/python -m pytest tests/test_health.py -q
```

预期： FAIL，失败原因包含 `ModuleNotFoundError` 或 `ImportError`，因为 `app/main.py` 尚未实现。

- [ ] **步骤 7: 实现最小 FastAPI 应用**

创建 `api/app/main.py`:

```python
from fastapi import FastAPI


app = FastAPI(title="AI PR Review Assistant API", version="0.1.0")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- [ ] **步骤 8: 运行测试确认通过**

运行：

```bash
cd api
./.venv/bin/python -m pytest tests/test_health.py -q
```

预期： `1 passed`。

- [ ] **步骤 9: 提交后端健康检查骨架**

运行：

```bash
git add api/requirements.txt api/pytest.ini api/app/__init__.py api/app/main.py api/tests/test_health.py
git commit -m "feat: add api health check skeleton"
```

预期： commit 成功，主分支仍可运行测试。

---

### 任务 2: GitHub PR URL 解析器

**文件：**
- 创建: `api/app/pr_url_parser.py`
- 创建: `api/tests/test_pr_url_parser.py`

- [ ] **步骤 1: 编写解析器失败测试**

创建 `api/tests/test_pr_url_parser.py`:

```python
import pytest

from app.pr_url_parser import InvalidPullRequestUrl, parse_github_pr_url


def test_parse_standard_github_pull_request_url() -> None:
    parsed = parse_github_pr_url("https://github.com/zch456/AI-PR-Review-/pull/12")

    assert parsed.owner == "zch456"
    assert parsed.repo == "AI-PR-Review-"
    assert parsed.pull_number == 12


def test_parse_url_with_trailing_slash_and_query_string() -> None:
    parsed = parse_github_pr_url("https://github.com/openai/openai-python/pull/99/?tab=files")

    assert parsed.owner == "openai"
    assert parsed.repo == "openai-python"
    assert parsed.pull_number == 99


@pytest.mark.parametrize(
    "pr_url",
    [
        "",
        "not-a-url",
        "https://example.com/owner/repo/pull/1",
        "https://github.com/owner/repo/issues/1",
        "https://github.com/owner/repo/pull/not-number",
        "https://github.com/owner/repo/pull/0",
    ],
)
def test_reject_invalid_pull_request_urls(pr_url: str) -> None:
    with pytest.raises(InvalidPullRequestUrl):
        parse_github_pr_url(pr_url)
```

- [ ] **步骤 2: 运行测试确认失败**

运行：

```bash
cd api
./.venv/bin/python -m pytest tests/test_pr_url_parser.py -q
```

预期： FAIL，失败原因包含 `ModuleNotFoundError: No module named 'app.pr_url_parser'`。

- [ ] **步骤 3: 实现解析器**

创建 `api/app/pr_url_parser.py`:

```python
from dataclasses import dataclass
from urllib.parse import urlparse


class InvalidPullRequestUrl(ValueError):
    """Raised when a URL is not a supported GitHub Pull Request URL."""


@dataclass(frozen=True)
class ParsedPullRequest:
    owner: str
    repo: str
    pull_number: int


def parse_github_pr_url(pr_url: str) -> ParsedPullRequest:
    parsed_url = urlparse(pr_url.strip())

    if parsed_url.scheme not in {"http", "https"}:
        raise InvalidPullRequestUrl("请输入完整的 GitHub PR 链接。")

    if parsed_url.netloc.lower() != "github.com":
        raise InvalidPullRequestUrl("当前仅支持 github.com 的 PR 链接。")

    path_parts = [part for part in parsed_url.path.split("/") if part]
    if len(path_parts) < 4:
        raise InvalidPullRequestUrl("PR 链接缺少 owner、repo 或 PR 编号。")

    owner, repo, pull_segment, pull_number_text = path_parts[:4]
    if pull_segment != "pull":
        raise InvalidPullRequestUrl("链接必须指向 GitHub Pull Request。")

    if not pull_number_text.isdigit():
        raise InvalidPullRequestUrl("PR 编号必须是正整数。")

    pull_number = int(pull_number_text)
    if pull_number <= 0:
        raise InvalidPullRequestUrl("PR 编号必须大于 0。")

    return ParsedPullRequest(owner=owner, repo=repo, pull_number=pull_number)
```

- [ ] **步骤 4: 运行解析器测试确认通过**

运行：

```bash
cd api
./.venv/bin/python -m pytest tests/test_pr_url_parser.py -q
```

预期： `3 passed`。

- [ ] **步骤 5: 运行后端全部测试**

运行：

```bash
cd api
./.venv/bin/python -m pytest -q
```

预期： 所有测试通过，当前应包含 `4 passed`。

- [ ] **步骤 6: 提交 URL 解析器**

运行：

```bash
git add api/app/pr_url_parser.py api/tests/test_pr_url_parser.py
git commit -m "feat: parse github pull request urls"
```

预期： commit 成功，后端测试仍通过。

---

### 任务 3: `/api/analyze-pr` 解析预览接口

**文件：**
- 创建: `api/app/schemas.py`
- 修改: `api/app/main.py`
- 创建: `api/tests/test_analyze_pr_endpoint.py`

- [ ] **步骤 1: 编写接口失败测试**

创建 `api/tests/test_analyze_pr_endpoint.py`:

```python
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analyze_pr_returns_parsed_preview() -> None:
    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/7"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "parsed",
        "owner": "zch456",
        "repo": "AI-PR-Review-",
        "pullNumber": 7,
    }


def test_analyze_pr_rejects_invalid_url() -> None:
    response = client.post("/api/analyze-pr", json={"prUrl": "https://example.com/demo/repo/pull/1"})

    assert response.status_code == 400
    assert response.json() == {"detail": "当前仅支持 github.com 的 PR 链接。"}
```

- [ ] **步骤 2: 运行测试确认失败**

运行：

```bash
cd api
./.venv/bin/python -m pytest tests/test_analyze_pr_endpoint.py -q
```

预期： FAIL，失败原因包含 `404 Not Found` 或 `ModuleNotFoundError`，因为接口和 schema 尚未实现。

- [ ] **步骤 3: 创建请求和响应 schema**

创建 `api/app/schemas.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field


class AnalyzePrRequest(BaseModel):
    pr_url: str = Field(alias="prUrl", min_length=1)


class AnalyzePrPreviewResponse(BaseModel):
    status: Literal["parsed"]
    owner: str
    repo: str
    pullNumber: int
```

- [ ] **步骤 4: 更新 FastAPI 应用**

替换 `api/app/main.py` with:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .pr_url_parser import InvalidPullRequestUrl, parse_github_pr_url
from .schemas import AnalyzePrPreviewResponse, AnalyzePrRequest


app = FastAPI(title="AI PR Review Assistant API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze-pr", response_model=AnalyzePrPreviewResponse)
def analyze_pr(request: AnalyzePrRequest) -> AnalyzePrPreviewResponse:
    try:
        parsed = parse_github_pr_url(request.pr_url)
    except InvalidPullRequestUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AnalyzePrPreviewResponse(
        status="parsed",
        owner=parsed.owner,
        repo=parsed.repo,
        pullNumber=parsed.pull_number,
    )
```

- [ ] **步骤 5: 运行接口测试确认通过**

运行：

```bash
cd api
./.venv/bin/python -m pytest tests/test_analyze_pr_endpoint.py -q
```

预期： `2 passed`。

- [ ] **步骤 6: 运行后端全部测试**

运行：

```bash
cd api
./.venv/bin/python -m pytest -q
```

预期： 所有测试通过，当前应包含 `6 passed`。

- [ ] **步骤 7: 提交解析预览接口**

运行：

```bash
git add api/app/main.py api/app/schemas.py api/tests/test_analyze_pr_endpoint.py
git commit -m "feat: expose pull request url parsing endpoint"
```

预期： commit 成功，后端测试仍通过。

---

### 任务 4: 前端最小输入页

**文件：**
- 创建: `web/package.json`
- 创建: `web/index.html`
- 创建: `web/tsconfig.json`
- 创建: `web/tsconfig.node.json`
- 创建: `web/vite.config.ts`
- 创建: `web/src/main.tsx`
- 创建: `web/src/App.tsx`
- 创建: `web/src/styles.css`

- [ ] **步骤 1: 创建前端 package 配置**

创建 `web/package.json`:

```json
{
  "name": "ai-pr-review-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite --host 0.0.0.0",
    "build": "tsc -b && vite build",
    "preview": "vite preview --host 0.0.0.0"
  },
  "dependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "typescript": "^5.7.2",
    "vite": "^6.0.7"
  }
}
```

- [ ] **步骤 2: 创建 HTML 入口**

创建 `web/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>AI PR Review 助手</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **步骤 3: 创建 TypeScript 配置**

创建 `web/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

创建 `web/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **步骤 4: 创建 Vite 配置**

创建 `web/vite.config.ts`:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://127.0.0.1:8000"
    }
  }
});
```

- [ ] **步骤 5: 创建 React 入口**

创建 `web/src/main.tsx`:

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **步骤 6: 创建最小 App 界面**

创建 `web/src/App.tsx`:

```tsx
import { FormEvent, useState } from "react";

type ParsedPreview = {
  status: "parsed";
  owner: string;
  repo: string;
  pullNumber: number;
};

type ApiError = {
  detail: string;
};

const exampleUrl = "https://github.com/zch456/AI-PR-Review-/pull/1";

export default function App() {
  const [prUrl, setPrUrl] = useState(exampleUrl);
  const [result, setResult] = useState<ParsedPreview | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("/api/analyze-pr", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prUrl })
      });

      if (!response.ok) {
        const payload = (await response.json()) as ApiError;
        throw new Error(payload.detail || "分析请求失败。");
      }

      const payload = (await response.json()) as ParsedPreview;
      setResult(payload);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "分析请求失败。");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="shell">
        <header className="header">
          <p className="eyebrow">AI Pull Request Review</p>
          <h1>AI PR Review 助手</h1>
          <p className="subtitle">粘贴 GitHub PR 链接，先完成链接解析；后续 PR 将逐步接入 diff 获取、风险识别和 AI Review。</p>
        </header>

        <form className="inputPanel" onSubmit={handleSubmit}>
          <label htmlFor="pr-url">GitHub PR 链接</label>
          <div className="inputRow">
            <input
              id="pr-url"
              type="url"
              value={prUrl}
              onChange={(event) => setPrUrl(event.target.value)}
              placeholder={exampleUrl}
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? "解析中" : "开始分析"}
            </button>
          </div>
        </form>

        {error && <div className="errorBox">{error}</div>}

        {result && (
          <section className="resultPanel" aria-label="PR 解析结果">
            <h2>解析结果</h2>
            <dl>
              <div>
                <dt>Owner</dt>
                <dd>{result.owner}</dd>
              </div>
              <div>
                <dt>Repository</dt>
                <dd>{result.repo}</dd>
              </div>
              <div>
                <dt>Pull Request</dt>
                <dd>#{result.pullNumber}</dd>
              </div>
            </dl>
          </section>
        )}
      </section>
    </main>
  );
}
```

- [ ] **步骤 7: 创建样式**

创建 `web/src/styles.css`:

```css
:root {
  font-family:
    Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #172033;
  background: #f4f7fb;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

button,
input {
  font: inherit;
}

.page {
  min-height: 100vh;
  padding: 48px 20px;
}

.shell {
  width: min(960px, 100%);
  margin: 0 auto;
}

.header {
  margin-bottom: 28px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #2563eb;
  font-size: 14px;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 40px;
  line-height: 1.15;
}

.subtitle {
  max-width: 720px;
  margin: 14px 0 0;
  color: #526071;
  line-height: 1.7;
}

.inputPanel,
.resultPanel,
.errorBox {
  border: 1px solid #dbe3ef;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 28px rgb(15 23 42 / 8%);
}

.inputPanel {
  padding: 20px;
}

.inputPanel label {
  display: block;
  margin-bottom: 10px;
  color: #334155;
  font-weight: 700;
}

.inputRow {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
}

.inputRow input {
  width: 100%;
  min-height: 44px;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  padding: 0 12px;
}

.inputRow button {
  min-height: 44px;
  border: 0;
  border-radius: 6px;
  padding: 0 18px;
  color: #ffffff;
  background: #2563eb;
  font-weight: 700;
  cursor: pointer;
}

.inputRow button:disabled {
  cursor: wait;
  opacity: 0.7;
}

.errorBox {
  margin-top: 16px;
  padding: 14px 16px;
  color: #991b1b;
  background: #fef2f2;
  border-color: #fecaca;
}

.resultPanel {
  margin-top: 20px;
  padding: 20px;
}

.resultPanel h2 {
  margin: 0 0 16px;
  font-size: 22px;
}

.resultPanel dl {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
}

.resultPanel div {
  min-width: 0;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 14px;
  background: #f8fafc;
}

.resultPanel dt {
  margin-bottom: 6px;
  color: #64748b;
  font-size: 13px;
  font-weight: 700;
}

.resultPanel dd {
  margin: 0;
  overflow-wrap: anywhere;
  font-weight: 700;
}

@media (max-width: 720px) {
  .page {
    padding: 28px 14px;
  }

  h1 {
    font-size: 32px;
  }

  .inputRow,
  .resultPanel dl {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **步骤 8: 安装前端依赖**

运行：

```bash
cd web
npm install
```

预期： 生成 `web/package-lock.json`，安装过程最后不包含 `npm ERR!`。

- [ ] **步骤 9: 构建前端**

运行：

```bash
cd web
npm run build
```

预期： 构建成功，输出包含 `built in`，并生成 `web/dist`。

- [ ] **步骤 10: 提交前端最小输入页**

运行：

```bash
git add web/package.json web/package-lock.json web/index.html web/tsconfig.json web/tsconfig.node.json web/vite.config.ts web/src/main.tsx web/src/App.tsx web/src/styles.css
git commit -m "feat: add pull request input web page"
```

预期： commit 成功，前端可构建。

---

### 任务 5: 项目说明与忽略规则

**文件：**
- 创建: `.gitignore`
- 创建: `README.md`

- [ ] **步骤 1: 创建 `.gitignore`**

创建 `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
.pytest_cache/
api/.venv/

# Node
web/node_modules/
web/dist/

# Local environment
.env
.env.*
!.env.example

# OS and editors
.DS_Store
.idea/
.vscode/
```

- [ ] **步骤 2: 创建中文 README 草稿**

创建 `README.md`:

```markdown
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
```

- [ ] **步骤 3: 运行后端测试**

运行：

```bash
cd api
./.venv/bin/python -m pytest -q
```

预期： 所有测试通过，当前应包含 `6 passed`。

- [ ] **步骤 4: 运行前端构建**

运行：

```bash
cd web
npm run build
```

预期： 构建成功，输出包含 `built in`。

- [ ] **步骤 5: 检查 Git 状态**

运行：

```bash
git status --short
```

预期： 只看到 `.gitignore` 和 `README.md` 未提交，`web/dist`、`web/node_modules`、`api/.venv` 不应出现在状态中。

- [ ] **步骤 6: 提交说明文档和忽略规则**

运行：

```bash
git add .gitignore README.md
git commit -m "docs: add project quick start guide"
```

预期： commit 成功。

---

### 任务 6: 第一阶段整体验证

**文件：**
- 不修改文件。

- [ ] **步骤 1: 启动后端服务**

运行：

```bash
cd api
./.venv/bin/python -m uvicorn app.main:app --reload
```

预期： 输出包含 `Uvicorn running on http://127.0.0.1:8000`。

- [ ] **步骤 2: 在另一个终端启动前端服务**

运行：

```bash
cd web
npm run dev
```

预期： 输出包含 `Local: http://localhost:5173/`。

- [ ] **步骤 3: 手动验证网页调用链**

在浏览器打开 `http://localhost:5173`，输入：

```text
https://github.com/zch456/AI-PR-Review-/pull/1
```

预期： 页面展示：

```text
Owner: zch456
Repository: AI-PR-Review-
Pull Request: #1
```

- [ ] **步骤 4: 验证后端测试**

运行：

```bash
cd api
./.venv/bin/python -m pytest -q
```

预期： 所有测试通过，当前应包含 `6 passed`。

- [ ] **步骤 5: 验证前端构建**

运行：

```bash
cd web
npm run build
```

预期： 构建成功，输出包含 `built in`。

- [ ] **步骤 6: 检查最终状态**

运行：

```bash
git status --short
```

预期： 工作区干净。

---

## 计划自查结果

- 设计方案中的第一阶段需求已覆盖：网页输入、后端解析、最小接口、测试和 README 草稿。
- GitHub API、风险分析、LLM Review、Markdown 导出被明确排除在本计划外，并留给后续小 PR。
- 所有任务均给出具体文件、具体代码、具体命令和预期输出。
- 变量名保持一致：前端请求字段为 `prUrl`，后端 schema alias 为 `prUrl`，响应字段为 `pullNumber`。
