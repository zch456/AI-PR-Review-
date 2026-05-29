# AI PR Review Assistant Project Rules

## Project Direction

This project is an AI-assisted Pull Request review tool. It should help developers understand PR changes faster, identify risky code, and generate useful review suggestions while controlling false positives, false negatives, latency, and user experience.

Core capabilities should include:

- PR change summary.
- Risky code identification.
- Review suggestion generation.
- Context-aware analysis based on repository files and PR diffs.
- Clear explanation of model choice, context retrieval strategy, and future extension plan in the final README.

## Competition Deliverables

Required deliverables:

- Public GitHub or Gitee repository. The repository can remain private during development if the competition allows it, but it must be publicly accessible after the submission deadline for judging.
- Demo video showing the main workflow and review output.
- README documentation covering setup, usage, dependencies, architecture, originality statement, model design, context strategy, limitations, and future extensions.

## Validity Rules

- The work must match the selected topic direction and be independently completed.
- Maintain continuous delivery throughout the development cycle. Do not import all code in one final-day commit.
- All commit timestamps must fall within the selected competition batch start and deadline.
- The main branch must remain runnable after every merged PR.
- A work may be invalid if:
  - PR descriptions are blank or do not match the actual changes.
  - Third-party libraries or frameworks are used but not listed in README.
  - Original project work is not distinguished from dependencies or reused code.
  - Reused personal code is not disclosed in the relevant PR description.

## PR Discipline

Use PRs for all feature additions and meaningful changes.

Follow the minimum PR principle:

- Each PR should do one thing only.
- Keep PRs as small and focused as practical.
- Split large features into independent PRs that can be reviewed and merged step by step.
- Avoid mixing unrelated refactors, UI changes, dependency changes, and feature logic in the same PR.
- After each PR is merged, the main branch must remain installable, runnable, and demonstrable.

Each PR must include:

- Title: one sentence describing what the PR adds or changes.
- Feature description: what the feature does and how to use it.
- Implementation approach: key technology choices and core logic.
- Test method: how the feature was verified.

Suggested PR template:

```markdown
## 功能描述

说明本 PR 新增/修改了什么，以及用户如何使用。

## 实现思路

说明技术选型、关键模块、核心逻辑或重要取舍。

## 测试方式

说明执行了哪些命令、手动验证了哪些流程、结果如何。

## 依赖与来源说明

列出新增依赖；如复用个人历史代码，说明来源和改动范围。
```

## Development Cadence

Recommended delivery rhythm:

- Start with documentation, project skeleton, and a minimal runnable flow.
- Build features incrementally through small PRs.
- Keep commits meaningful and naturally distributed across the development period.
- Prefer working software over large unfinished branches.
- Record design decisions in README or docs as they stabilize.

## README Must Explain

The README should explicitly include:

- Problem background and target users.
- Main features and screenshots or demo references.
- Quick start and configuration.
- Supported PR input method.
- Architecture and data flow.
- AI model selection rationale.
- Context retrieval and prompt construction strategy.
- False-positive and false-negative control strategy.
- Response speed considerations.
- Dependency list and originality boundary.
- Known limitations.
- Future extension directions.
