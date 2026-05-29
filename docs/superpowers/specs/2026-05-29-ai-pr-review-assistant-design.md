# AI PR Review 助手设计方案

日期：2026-05-29

## 1. 项目目标

构建一个网页端 AI Pull Request 代码评审助手。开发者输入 GitHub Pull Request 链接后，系统自动获取 PR 变更，结合仓库上下文分析 diff，并生成结构化 Review 报告。

该工具应通过以下方式提升 Review 效率和质量：

- 帮助 Reviewer 快速理解 PR 修改了什么。
- 识别高风险文件和高风险代码片段。
- 生成可执行的 Review 建议。
- 区分高置信度问题和需要人工判断的问题。
- 导出可复制到 PR 讨论区的 Markdown Review 报告。

项目还必须满足比赛对持续交付、小 PR、清晰 PR 描述、公开仓库、README 文档和 Demo 视频的要求。

## 2. 目标用户

主要用户：

- 正在 Review 队友 PR 的开发者。
- 在提交 Review 前自查自己 PR 的开发者。
- 暂时没有成熟自动化 Review 工具的小团队。

次要用户：

- 评委。评委需要确认项目可运行、设计可解释，并能展示真实代码评审价值。

## 3. MVP 范围

第一个可用版本应支持以下流程：

1. 用户打开网页。
2. 用户粘贴 GitHub PR 链接。
3. 系统解析仓库 owner、仓库名和 PR 编号。
4. 系统从 GitHub 获取 PR 元信息和变更文件。
5. 系统对变更文件和 patch 执行基于规则的风险预检查。
6. 系统将结构化 PR 上下文发送给 AI 模型。
7. 系统在浏览器中展示结构化 Review 报告。
8. 用户复制或导出 Markdown 格式报告。

MVP 功能：

- GitHub PR 链接输入。
- PR 元信息获取。
- 变更文件和 patch 获取。
- PR 变更总结生成。
- 风险文件识别。
- Review 建议生成。
- 严重程度和置信度标记。
- Markdown 导出。
- README 说明安装、依赖、模型选择、上下文策略、限制和未来扩展方向。

MVP 暂不包含：

- GitHub App 安装。
- 自动将评论发布回 GitHub。
- 多用户登录认证。
- 团队仪表盘。
- 持久化 Review 历史数据库。
- 深度仓库级调用链分析。

这些能力可在基础 Demo 稳定后作为后续扩展。

## 4. 推荐技术栈

前端：

- 使用 React 和 Vite 构建轻量网页 UI。
- 使用 TypeScript 提升报告数据结构的可靠性。
- 组件结构围绕 Review 工作流设计，而不是做成营销落地页。

后端：

- 使用 Python FastAPI 构建 API 服务。
- 使用 Pydantic 定义请求和响应数据结构。
- 使用 HTTP 客户端访问 GitHub API。
- 提供模型服务适配层，用于调用 OpenAI-compatible API。

AI 层：

- prompt 模板独立存放，不写死在路由处理器中。
- 模型输出采用结构化 JSON。
- 对严重程度、置信度和报告章节做统一归一化。

测试：

- 后端单元测试覆盖 URL 解析、GitHub 响应映射、规则风险检查和报告聚合。
- 前端在可行范围内覆盖主报告渲染路径的组件或集成测试。
- 使用示例 PR fixture 做测试，避免每次测试都依赖真实 GitHub 网络请求。

## 5. 系统架构

```text
Browser UI
  -> POST /api/analyze-pr
    -> PR URL parser
    -> GitHub client
    -> PR context collector
    -> Rule-based risk engine
    -> AI review service
    -> Report aggregator
  <- Structured review report JSON
```

### 前端组件

- `PrInputPanel`：接收 GitHub PR 链接并启动分析。
- `AnalysisProgress`：展示加载状态和当前分析阶段。
- `ReportOverview`：展示标题、仓库、作者、分支、变更文件和摘要。
- `RiskList`：展示需要优先关注的文件或代码片段。
- `SuggestionList`：按严重程度分组展示 Review 建议。
- `MarkdownExport`：渲染可复制的 Markdown 报告。
- `ErrorState`：解释 API、token、限流或无效链接等错误。

### 后端模块

- `pr_url_parser`：校验并解析 GitHub PR 链接。
- `github_client`：获取 PR 元信息、变更文件和 patch。
- `context_collector`：构建紧凑的分析上下文。
- `risk_engine`：在 AI 分析前执行确定性的风险启发式规则。
- `llm_provider`：封装所选 AI 模型提供方。
- `review_service`：准备 prompt、调用模型、校验输出并聚合发现。
- `schemas`：定义请求、响应、发现项、风险项和摘要类型。

## 6. 数据流

1. 前端发送：

```json
{
  "prUrl": "https://github.com/owner/repo/pull/123"
}
```

2. 后端解析：

```json
{
  "owner": "owner",
  "repo": "repo",
  "pullNumber": 123
}
```

3. 后端获取：

- PR 标题和描述。
- PR 作者。
- base 分支和 head 分支。
- 变更文件列表。
- 每个文件的 patch 内容。
- 每个文件的新增行数、删除行数和文件状态。

4. 后端构建分析上下文：

- PR 元信息。
- 文件级变更摘要。
- patch 片段。
- 基于规则识别出的风险信号。

5. AI 模型返回结构化结果：

```json
{
  "summary": "...",
  "riskLevel": "medium",
  "keyChanges": [],
  "findings": [],
  "reviewQuestions": [],
  "recommendedTests": []
}
```

6. 前端渲染最终报告。

## 7. Review 报告结构

报告应包含：

- `summary`：面向人的 PR 总结。
- `riskLevel`：整体风险等级。
- `keyChanges`：按主题或文件分组的重要变更。
- `riskFiles`：建议 Reviewer 优先关注的文件。
- `findings`：带严重程度和置信度的具体建议。
- `reviewQuestions`：需要人工确认的不确定问题。
- `recommendedTests`：建议补充或手动执行的测试。
- `markdown`：可导出的 Markdown 文本。

每条发现项应包含：

- `filePath`。
- `line`，有行号时提供。
- `severity`：`high`、`medium` 或 `low`。
- `confidence`：`high`、`medium` 或 `low`。
- `title`。
- `reason`。
- `impact`。
- `suggestion`。

## 8. 模型选择策略

MVP 应使用 OpenAI-compatible 模型接口，而不是将某个模型厂商写死在业务逻辑中。

选择原则：

- 当最终 Review 报告质量更重要时，使用推理能力更强的模型。
- 未来可为快速摘要接入成本更低、速度更快的模型。
- 模型名、base URL 和 API key 均通过环境变量配置。
- prompt 模板应纳入版本管理，保证模型行为可审计、可迭代。

初始设计：

- `LLM_PROVIDER=openai_compatible`
- `LLM_MODEL=<由用户配置>`
- `LLM_BASE_URL=<由用户配置>`
- `LLM_API_KEY=<由用户配置>`

README 应说明项目支持 OpenAI-compatible API，用户需要自行配置可用的模型提供方。

## 9. 上下文获取策略

工具应采用分层上下文：

### MVP 上下文

- PR 标题和描述。
- 变更文件列表。
- 每个变更文件的 patch diff。
- 新增行数、删除行数和文件状态。
- 基于规则识别出的风险信号。

### 近期增强上下文

- 在文件大小允许时获取变更文件完整内容。
- 获取变更行附近的函数或 class 上下文。
- 查找与变更源文件相关的测试文件。
- 获取项目清单和构建配置文件，例如 `package.json`、`pyproject.toml` 或其他 build config。

### 未来上下文

- 仓库级符号搜索。
- 调用图或 import 图。
- 基于 embedding 的相关文件检索。
- 历史 issue 或历史 Review 评论。
- 团队自定义 Review 规则。

MVP 应保持上下文紧凑，以控制响应速度和 token 成本。对于大 diff，应按文件分块分析，再做最终聚合。

## 10. 误报与漏报控制

系统不应把模型的每一个观察都当成确定缺陷展示。

控制策略：

- 区分确定性的规则风险信号和 AI 生成的发现项。
- 使用严重程度和置信度字段。
- 将不确定内容放入 `reviewQuestions`，而不是直接放入 `findings`。
- 尽可能要求每条发现项包含具体代码位置。
- 要求模型优先输出可执行建议，减少泛泛的风格建议。
- 在聚合阶段去重相似发现。
- 将推荐测试与缺陷问题分开展示。

报告措辞应谨慎：

- 高置信度问题可以直接表达。
- 低置信度内容应表述为 Review 问题。
- 建议应说明影响和验证方法。

## 11. 响应速度策略

MVP 在 Demo 中应有明确的响应反馈。

设计选择：

- 每次分析请求只获取一次 GitHub PR 文件数据。
- MVP 中限制文件数量和 patch 大小，并给出清晰错误提示。
- 小 PR 使用一次模型调用完成分析。
- 较大 PR 按文件组分析后聚合结果。
- 前端展示分析进度，避免长时间空白加载。
- 为测试和 Demo 兜底准备 fixture 数据。

Demo 应选择中等规模 PR，既能体现真实分析价值，又不会让视频被等待时间占据。

## 12. 错误处理

预期错误场景：

- PR 链接无效。
- 私有仓库缺少 token 权限。
- GitHub API 触发限流。
- PR 文件过多或 diff 过大。
- 缺少 AI provider API key。
- AI provider 超时或返回无效 JSON。

用户侧行为：

- 说明失败发生在哪一步。
- 给出下一步处理建议。
- 失败后页面仍可继续使用。

后端行为：

- 返回结构化错误响应。
- 不暴露 API key 或敏感配置。
- 记录足够的本地调试信息。

## 13. 安全与隐私

工具会处理仓库代码和 PR 内容，因此 README 必须明确说明：

- 后端会将选定的 PR 上下文发送给用户配置的 AI provider。
- 除非信任所配置的 provider，否则不要分析私有或敏感仓库。
- API key 必须存放在环境变量中，严禁提交到仓库。
- MVP 默认不持久化 PR 内容。

未来生产版本应增加：

- 用户认证。
- 按用户隔离并加密存储凭据。
- 审计日志。
- 数据保留策略。

## 14. UI 方向

UI 应是实用的开发者工具，而不是营销落地页。

首屏：

- 产品名称。
- PR 链接输入框。
- 分析按钮。
- 简洁的配置状态提示。

报告页：

- 顶部展示 PR 概览。
- 展示整体风险等级。
- 展示关键变更。
- 高风险发现优先展示。
- 展示 Review 问题。
- 展示推荐测试。
- 提供 Markdown 导出。

视觉风格：

- 信息密度高但易读。
- 严重程度颜色清晰。
- 文件路径和行号便于扫描。
- 避免干扰报告阅读的装饰性布局。

## 15. 测试计划

后端测试：

- 解析合法 GitHub PR 链接。
- 拒绝非法链接。
- 将 GitHub API 文件响应映射为内部数据结构。
- 识别规则风险，例如删除测试、配置变更、鉴权相关文件、迁移文件和大 patch。
- 校验模型输出归一化逻辑。
- 根据结构化报告生成 Markdown。

前端检查：

- 输入校验。
- 加载状态。
- 错误状态。
- 使用 fixture 数据渲染报告。
- Markdown 复制或导出行为。

手动 Demo 检查：

- 分析一个公开 PR。
- 确认摘要、风险、建议和导出内容正确渲染。
- 确认缺少 API key 时错误提示可理解。
- 确认 README 中的启动步骤可从干净 clone 复现。

## 16. 增量 PR 路线

遵循小 PR 纪律。每个 PR 只做一件事，并保持主分支可运行。

建议 PR 顺序：

1. `docs: add project rules and design baseline`
2. `feat: initialize web and api project skeleton`
3. `feat: parse github pull request url`
4. `feat: fetch github pull request metadata`
5. `feat: fetch changed files and diff patches`
6. `feat: render pull request summary page`
7. `feat: add rule-based risk precheck`
8. `feat: integrate llm review generation`
9. `feat: display structured review report`
10. `feat: export review report as markdown`
11. `test: add sample pr fixtures and backend tests`
12. `docs: complete readme and demo guide`

每个 PR 描述必须包含：

- 功能描述。
- 实现思路。
- 测试方式。
- 如有新增依赖或复用来源，说明依赖与来源。

## 17. Demo 计划

Demo 视频流程：

1. 展示仓库和 README。
2. 启动后端和前端。
3. 粘贴公开 GitHub PR 链接。
4. 执行分析。
5. 讲解生成的 PR 摘要。
6. 展示风险文件和 Review 建议。
7. 复制或导出 Markdown 报告。
8. 简要展示 README 中的模型和上下文策略说明。

Demo 应选用一个变更量适中的 PR，既能展示有价值的分析，又不会让等待时间过长。

## 18. 未来扩展

MVP 之后可扩展：

- GitHub App 集成。
- 将选中的发现项自动评论到 PR。
- 仓库级规则配置。
- 团队自定义 Review 风格。
- 基于 AST 的代码上下文抽取。
- 基于 embedding 的相关文件检索。
- Review 历史和趋势仪表盘。
- 多模型流水线：快速摘要模型 + 强推理最终 Review 模型。
- 支持 Gitee 和 GitLab。

## 19. 成功标准

项目成功的标准：

- 评委可以 clone 仓库并运行 Demo。
- 网页应用可以接收真实 GitHub PR 链接。
- 应用可以生成有用的结构化 Review 报告。
- README 清楚说明依赖、原创性、模型选择、上下文策略和未来扩展。
- commit 和 PR 历史体现持续、小步、有意义的交付过程。
- 每次 PR 合并后，主分支都保持可运行。
