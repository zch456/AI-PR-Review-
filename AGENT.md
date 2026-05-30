# AI PR Review 助手协作约定

## 项目定位

本项目是一个网页端 AI PR Review 工具。用户输入 GitHub PR 链接后，系统获取 PR 元信息、变更文件和 patch，执行规则风险预检查，并可调用 DeepSeek 生成结构化 Review 报告。

当前项目已经完成初步闭环：

- GitHub PR URL 解析。
- 公开 GitHub PR 元信息获取。
- changed files 和 patch 获取。
- 规则化风险预检查。
- DeepSeek AI Review 生成。
- 前端报告展示。
- Markdown 报告导出。

后续重点不是继续堆功能，而是提升稳定性、准确性、可配置性和真实 Review 体验。

## 开发原则

- 每次只处理一个清晰主题，保持小步迭代。
- 新功能优先通过独立 PR 完成，合并后主分支必须可运行。
- 涉及业务逻辑的改动按 TDD 推进：先写或调整测试，再实现，再跑验证。
- 文档跟随代码更新，避免 README、开发计划和实际行为脱节。
- 不提交 API Key、token、本地路径隐私或临时调试产物。
- 用户本地已有未提交改动时，不擅自覆盖；只暂存和提交本次任务相关文件。

## 分支与 PR 流程

- 从 `main` 创建功能分支，分支名使用 `codex/<主题>`。
- PR 标题和描述使用中文，说明做了什么、实现思路和验证方式。
- 每个新功能完成后创建 PR，并合并回 `main`。
- 合并前后都要跑基础验证，确保远程主分支稳定。

## 常用验证命令

后端测试：

```bash
cd api
./.venv/bin/python -m pytest -q
```

前端构建：

```bash
cd web
npm run build
```

敏感信息扫描：

```bash
rg -n "sk-[A-Za-z0-9_-]{12,}|API_KEY.*sk-|secret.*sk-" README.md api web -g '!web/node_modules/**' -g '!api/.venv/**'
```

## 文档分工

- `README.md`：项目入口，说明功能、运行方式、配置方式、依赖和当前限制。
- `docs/开发历程.md`：回顾项目从骨架到 AI Review 闭环的演进过程。
- `docs/开发计划.md`：记录当前状态、后续迭代路线和验收标准。
- `docs/踩坑记录.md`：沉淀开发中遇到的真实问题、原因和约束。
- `docs/优化拓展.md`：面向下一阶段的产品、工程、算法和体验升级方案。
