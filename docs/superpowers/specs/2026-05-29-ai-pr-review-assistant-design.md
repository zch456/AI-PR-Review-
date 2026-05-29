# AI PR Review Assistant Design

Date: 2026-05-29

## 1. Project Goal

Build a web-based AI Pull Request review assistant. A developer enters a GitHub Pull Request URL, and the system fetches PR changes, analyzes the diff with repository context, and generates a structured review report.

The tool should improve review efficiency and quality by helping reviewers:

- Understand what changed in a PR.
- Identify risky files and risky code snippets.
- Get actionable review suggestions.
- Distinguish high-confidence issues from uncertain questions.
- Export a review report that can be copied into a PR discussion.

The project must also satisfy the competition requirements for continuous delivery, small PRs, clear PR descriptions, a public repository, README documentation, and a demo video.

## 2. Target Users

Primary users:

- Developers reviewing teammates' PRs.
- Developers self-checking their own PRs before requesting review.
- Small teams that do not have mature automated review tooling.

Secondary users:

- Competition judges evaluating whether the project can run, explain its design, and demonstrate realistic value.

## 3. MVP Scope

The first usable version should support this workflow:

1. User opens the web page.
2. User pastes a GitHub PR URL.
3. System parses the repository owner, repository name, and PR number.
4. System fetches PR metadata and changed files from GitHub.
5. System runs a rule-based risk precheck on changed files and patches.
6. System sends structured PR context to an AI model.
7. System displays a structured review report in the browser.
8. User copies or exports the report as Markdown.

MVP features:

- GitHub PR URL input.
- PR metadata retrieval.
- Changed files and patch retrieval.
- PR summary generation.
- Risk file identification.
- Review suggestion generation.
- Severity and confidence labels.
- Markdown export.
- README explaining setup, dependencies, model selection, context strategy, limitations, and future extensions.

Out of MVP scope:

- GitHub App installation.
- Automatically posting comments back to GitHub.
- Multi-user authentication.
- Team dashboard.
- Persistent review history database.
- Deep repository-wide call graph analysis.

These can be future extensions after the basic demo is stable.

## 4. Recommended Technology Stack

Frontend:

- React with Vite for a lightweight web UI.
- TypeScript for safer report data structures.
- A component structure focused on the review workflow rather than a marketing landing page.

Backend:

- Python FastAPI for the API service.
- Pydantic models for request and response schemas.
- HTTP client for GitHub API access.
- A model provider adapter that can call an OpenAI-compatible API.

AI layer:

- Prompt templates stored separately from route handlers.
- Structured JSON output from the model.
- Normalization logic for severity, confidence, and report sections.

Testing:

- Backend unit tests for URL parsing, GitHub response mapping, rule-based risk checks, and report aggregation.
- Frontend component or integration tests for the main report rendering path when practical.
- Fixture-based tests with sample PR data to avoid relying on live GitHub calls in every test.

## 5. System Architecture

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

### Frontend Components

- `PrInputPanel`: accepts a GitHub PR URL and starts analysis.
- `AnalysisProgress`: shows loading and current stage.
- `ReportOverview`: shows title, repository, author, branch, changed files, and summary.
- `RiskList`: shows files or snippets that need attention first.
- `SuggestionList`: shows review suggestions grouped by severity.
- `MarkdownExport`: renders a copyable Markdown version of the report.
- `ErrorState`: explains API, token, rate limit, or invalid URL errors.

### Backend Modules

- `pr_url_parser`: validates and parses GitHub PR URLs.
- `github_client`: fetches PR metadata, changed files, and patches.
- `context_collector`: builds compact context for analysis.
- `risk_engine`: applies deterministic risk heuristics before AI analysis.
- `llm_provider`: wraps the selected AI provider.
- `review_service`: prepares prompts, calls the model, validates output, and aggregates findings.
- `schemas`: defines request, response, finding, risk, and summary types.

## 6. Data Flow

1. Frontend sends:

```json
{
  "prUrl": "https://github.com/owner/repo/pull/123"
}
```

2. Backend parses:

```json
{
  "owner": "owner",
  "repo": "repo",
  "pullNumber": 123
}
```

3. Backend fetches:

- PR title and description.
- PR author.
- Base and head branch.
- Changed file list.
- Patch content for each file.
- Additions, deletions, and status for each file.

4. Backend builds analysis context:

- PR metadata.
- File-level change summary.
- Patch snippets.
- Rule-based risk signals.

5. AI model returns structured findings:

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

6. Frontend renders the final report.

## 7. Review Report Shape

The report should include:

- `summary`: plain-language PR summary.
- `riskLevel`: overall risk level.
- `keyChanges`: important changes grouped by topic or file.
- `riskFiles`: files that deserve early reviewer attention.
- `findings`: concrete suggestions with severity and confidence.
- `reviewQuestions`: uncertain points that should be checked by a human.
- `recommendedTests`: tests or manual checks suggested for the PR.
- `markdown`: exportable Markdown text.

Each finding should include:

- `filePath`.
- `line` when available.
- `severity`: `high`, `medium`, or `low`.
- `confidence`: `high`, `medium`, or `low`.
- `title`.
- `reason`.
- `impact`.
- `suggestion`.

## 8. Model Selection Strategy

The MVP should use an OpenAI-compatible model interface instead of hard-coding one vendor into business logic.

Selection principles:

- Use a stronger reasoning-capable model for final report generation when quality matters.
- Allow a cheaper and faster model for quick summaries in future versions.
- Keep model name, base URL, and API key in environment variables.
- Keep prompt templates versioned in the repository so behavior is auditable.

Initial design:

- `LLM_PROVIDER=openai_compatible`
- `LLM_MODEL=<configured by user>`
- `LLM_BASE_URL=<configured by user>`
- `LLM_API_KEY=<configured by user>`

README should explain that the project supports OpenAI-compatible APIs and that users must configure their own model provider.

## 9. Context Acquisition Strategy

The tool should use layered context:

### MVP Context

- PR title and description.
- Changed file list.
- Patch diff for each changed file.
- Additions, deletions, and file status.
- Rule-based risk signals.

### Near-Term Context

- Full content of changed files when size permits.
- Neighboring function or class context around changed lines.
- Test files related to changed source files.
- Project manifest files such as `package.json`, `pyproject.toml`, or build config.

### Future Context

- Repository-wide symbol search.
- Call graph or import graph.
- Embedding-based retrieval for related files.
- Historical issues or review comments.
- Team-specific review rules.

The MVP should keep context compact to control latency and token cost. Large diffs should be chunked by file and summarized before final aggregation.

## 10. False Positive and False Negative Control

The system should avoid presenting every model observation as a confirmed defect.

Controls:

- Separate deterministic risk signals from AI-generated findings.
- Use severity and confidence fields.
- Put uncertain items into `reviewQuestions` instead of `findings`.
- Require each finding to include a concrete code location when possible.
- Ask the model to prefer actionable findings over generic style advice.
- Deduplicate similar findings during aggregation.
- Show recommended tests separately from defects.

Report language should be careful:

- High-confidence issues can use direct wording.
- Low-confidence items should be phrased as review questions.
- Suggestions should explain impact and verification method.

## 11. Response Speed Strategy

The MVP should feel responsive during demo usage.

Design choices:

- Fetch GitHub PR files once per analysis request.
- Limit file count and patch size in MVP with clear error messages.
- Analyze small PRs in one model call.
- For larger PRs, analyze file groups and aggregate results.
- Show frontend progress states instead of a blank loading screen.
- Cache fixture data for tests and demo fallback.

The demo should use a medium-sized PR so the analysis is realistic but not slow.

## 12. Error Handling

Expected error cases:

- Invalid PR URL.
- Private repository without token access.
- GitHub rate limit.
- PR has too many files or an oversized diff.
- AI provider key missing.
- AI provider timeout or invalid JSON response.

User-facing behavior:

- Explain the failed step.
- Suggest the next action.
- Keep the page usable after failure.

Backend behavior:

- Return structured error responses.
- Avoid exposing API keys or sensitive configuration.
- Log enough context for local debugging.

## 13. Security and Privacy

The tool handles repository code and PR content, so README must clearly explain:

- The backend sends selected PR context to the configured AI provider.
- Users should avoid analyzing private or sensitive repositories unless they trust their configured provider.
- API keys must be stored in environment variables and never committed.
- The MVP does not persist PR content by default.

Future production versions should add:

- User authentication.
- Per-user encrypted credentials.
- Audit logs.
- Data retention controls.

## 14. UI Direction

The UI should be a practical developer tool, not a landing page.

First screen:

- Header with product name.
- PR URL input.
- Analyze button.
- Small configuration status indicator.

Report screen:

- PR overview at the top.
- Overall risk level.
- Key changes.
- High-risk findings first.
- Review questions.
- Recommended tests.
- Markdown export.

Visual tone:

- Dense but readable.
- Clear severity colors.
- File paths and line numbers easy to scan.
- No decorative layout that distracts from the report.

## 15. Testing Plan

Backend tests:

- Parse valid GitHub PR URLs.
- Reject invalid URLs.
- Map GitHub API file responses into internal schemas.
- Detect rule-based risks such as deleted tests, config changes, auth-related files, migration files, and large patches.
- Validate model output normalization.
- Generate Markdown from a structured report.

Frontend checks:

- Input validation.
- Loading state.
- Error state.
- Report rendering with fixture data.
- Markdown copy/export behavior.

Manual demo checks:

- Analyze a public PR.
- Confirm summary, risks, suggestions, and export render correctly.
- Confirm missing API key error is understandable.
- Confirm README setup steps work from a clean clone.

## 16. Incremental PR Roadmap

Follow small PR discipline. Each PR should do one thing and keep the main branch runnable.

Suggested PR order:

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

Each PR description must include:

- Feature description.
- Implementation approach.
- Test method.
- Dependency and source disclosure when relevant.

## 17. Demo Plan

Demo video flow:

1. Show repository and README.
2. Start backend and frontend.
3. Paste a public GitHub PR URL.
4. Run analysis.
5. Explain generated PR summary.
6. Show risk files and review suggestions.
7. Copy/export Markdown report.
8. Briefly show model/context strategy in README.

The demo should use a PR with enough changes to show useful analysis but not so large that latency dominates the video.

## 18. Future Extensions

Possible extensions after MVP:

- GitHub App integration.
- Auto-comment selected findings on PRs.
- Repository rule configuration.
- Team-specific review style.
- AST-based code context extraction.
- Related-file retrieval with embeddings.
- Review history and trend dashboard.
- Multi-model pipeline with fast summary and stronger final review.
- Support for Gitee and GitLab.

## 19. Success Criteria

The project is successful if:

- A judge can clone the repository and run the demo.
- The web app accepts a real GitHub PR URL.
- The app produces a useful, structured review report.
- The README clearly explains dependencies, originality, model choice, context strategy, and future extensions.
- The commit and PR history show continuous, small, meaningful delivery.
- The main branch stays runnable after each merged PR.
