import { FormEvent, useState } from "react";

type PullRequestFile = {
  path: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  patch: string | null;
};

type RiskSignal = {
  riskType: string;
  severity: "low" | "medium" | "high";
  confidence: "low" | "medium" | "high";
  filePath: string;
  title: string;
  reason: string;
  suggestion: string;
};

type ParsedPreview = {
  status: "fetched";
  owner: string;
  repo: string;
  pullNumber: number;
  title: string;
  author: string;
  state: string;
  isDraft: boolean;
  baseBranch: string;
  headBranch: string;
  additions: number;
  deletions: number;
  changedFiles: number;
  htmlUrl: string;
  files: PullRequestFile[];
  overallRisk: "low" | "medium" | "high";
  riskSignals: RiskSignal[];
};

type ApiError = {
  detail: string;
};

type ReviewFinding = {
  filePath: string;
  severity: "low" | "medium" | "high";
  lineStart: number | null;
  lineEnd: number | null;
  description: string;
  suggestion: string;
};

type AiReviewResult = {
  summary: string;
  findings: ReviewFinding[];
};

const exampleUrl = "https://github.com/zch456/AI-PR-Review-/pull/1";

const fileStatusLabels: Record<string, string> = {
  added: "新增",
  modified: "修改",
  removed: "删除",
  renamed: "重命名",
  copied: "复制",
  changed: "变更",
  unchanged: "未变更"
};

const riskLevelLabels: Record<ParsedPreview["overallRisk"], string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险"
};

const confidenceLabels: Record<RiskSignal["confidence"], string> = {
  low: "低置信度",
  medium: "中置信度",
  high: "高置信度"
};

export default function App() {
  const [prUrl, setPrUrl] = useState(exampleUrl);
  const [result, setResult] = useState<ParsedPreview | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isReviewLoading, setIsReviewLoading] = useState(false);
  const [aiReview, setAiReview] = useState<AiReviewResult | null>(null);
  const [reviewError, setReviewError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError("");
    setResult(null);
    setAiReview(null);
    setReviewError("");

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

  async function handleGenerateReview() {
    if (!result) return;
    setIsReviewLoading(true);
    setReviewError("");
    setAiReview(null);

    try {
      const response = await fetch("/api/generate-review", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ prUrl })
      });

      if (!response.ok) {
        const payload = (await response.json()) as ApiError;
        throw new Error(payload.detail || "AI Review 生成失败。");
      }

      const payload = (await response.json()) as AiReviewResult;
      setAiReview(payload);
    } catch (caughtError) {
      setReviewError(caughtError instanceof Error ? caughtError.message : "AI Review 生成失败。");
    } finally {
      setIsReviewLoading(false);
    }
  }

  function handleExportMarkdown() {
    if (!result || !aiReview) return;

    const lines: string[] = [];
    lines.push("# AI PR Review 报告");
    lines.push("");
    lines.push("## PR 元信息");
    lines.push("");
    lines.push(`- **仓库**: ${result.owner}/${result.repo}`);
    lines.push(`- **PR 编号**: #${result.pullNumber}`);
    lines.push(`- **标题**: ${result.title}`);
    lines.push(`- **作者**: ${result.author}`);
    lines.push(`- **分支**: ${result.headBranch} → ${result.baseBranch}`);
    lines.push(`- **状态**: ${result.isDraft ? "草稿" : result.state}`);
    lines.push(`- **新增**: +${result.additions}`);
    lines.push(`- **删除**: -${result.deletions}`);
    lines.push(`- **变更文件**: ${result.changedFiles}`);
    lines.push(`- **PR 链接**: ${result.htmlUrl}`);
    lines.push(`- **整体风险**: ${riskLevelLabels[result.overallRisk]}`);
    lines.push("");

    if (result.riskSignals.length > 0) {
      lines.push("## 规则风险提示");
      lines.push("");
      for (const risk of result.riskSignals) {
        lines.push(`### [${riskLevelLabels[risk.severity]}] ${risk.title}`);
        lines.push(`- **文件**: \`${risk.filePath}\``);
        lines.push(`- **原因**: ${risk.reason}`);
        lines.push(`- **建议**: ${risk.suggestion}`);
        lines.push("");
      }
    }

    lines.push("## AI Review");
    lines.push("");
    lines.push("### 变更总结");
    lines.push("");
    lines.push(aiReview.summary);
    lines.push("");

    if (aiReview.findings.length > 0) {
      for (const finding of aiReview.findings) {
        const sevLabel = riskLevelLabels[finding.severity];
        const lineInfo = finding.lineStart != null && finding.lineEnd != null
          ? ` (L${finding.lineStart}-L${finding.lineEnd})`
          : "";
        lines.push(`### [${sevLabel}] ${finding.filePath}${lineInfo}`);
        lines.push("");
        lines.push(finding.description);
        lines.push("");
        lines.push(`> **建议**: ${finding.suggestion}`);
        lines.push("");
      }
    }

    lines.push("---");
    lines.push("*本报告由 AI PR Review 助手自动生成*");

    const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `PR-Review-${result.owner}-${result.repo}-${result.pullNumber}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="page">
      <section className="shell">
        <header className="header">
          <p className="eyebrow">AI Pull Request Review</p>
          <h1>AI PR Review 助手</h1>
          <p className="subtitle">
            粘贴 GitHub PR 链接，获取 PR 基础元信息、规则化风险提示，并生成可导出的 AI Review 报告。
          </p>
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
            <div className="resultHeader">
              <div>
                <p className="panelLabel">PR 元信息</p>
                <h2>{result.title}</h2>
              </div>
              <a href={result.htmlUrl} target="_blank" rel="noreferrer">
                打开 GitHub
              </a>
            </div>
            <dl className="summaryGrid">
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
              <div>
                <dt>作者</dt>
                <dd>{result.author}</dd>
              </div>
              <div>
                <dt>状态</dt>
                <dd>{result.isDraft ? "草稿" : result.state}</dd>
              </div>
              <div>
                <dt>分支</dt>
                <dd>
                  {result.headBranch} → {result.baseBranch}
                </dd>
              </div>
              <div>
                <dt>新增</dt>
                <dd>+{result.additions}</dd>
              </div>
              <div>
                <dt>删除</dt>
                <dd>-{result.deletions}</dd>
              </div>
              <div>
                <dt>变更文件</dt>
                <dd>{result.changedFiles}</dd>
              </div>
              <div>
                <dt>整体风险</dt>
                <dd>
                  <span className={`riskPill ${result.overallRisk}`}>{riskLevelLabels[result.overallRisk]}</span>
                </dd>
              </div>
            </dl>

            <div className="riskSection">
              <div className="sectionHeader">
                <p className="panelLabel">风险提示</p>
                <span>{result.riskSignals.length} 条</span>
              </div>
              {result.riskSignals.length > 0 ? (
                <ul className="riskList">
                  {result.riskSignals.map((risk) => (
                    <li className="riskRow" key={`${risk.riskType}-${risk.filePath}`}>
                      <div className="riskTitleRow">
                        <span className={`riskPill ${risk.severity}`}>{riskLevelLabels[risk.severity]}</span>
                        <strong>{risk.title}</strong>
                        <span>{confidenceLabels[risk.confidence]}</span>
                      </div>
                      <code>{risk.filePath}</code>
                      <p>{risk.reason}</p>
                      <p>{risk.suggestion}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="emptyState">未命中当前规则集中的高优先级风险。</p>
              )}
            </div>

            <div className="filesSection">
              <div className="sectionHeader">
                <p className="panelLabel">变更文件</p>
                <span>{result.files.length} 个文件</span>
              </div>
              <ul className="fileList">
                {result.files.map((file) => (
                  <li className="fileRow" key={file.path}>
                    <div className="fileMain">
                      <span className="statusBadge">{fileStatusLabels[file.status] ?? file.status}</span>
                      <code>{file.path}</code>
                    </div>
                    <div className="fileStats" aria-label={`${file.path} 的变更统计`}>
                      <span className="additions">+{file.additions}</span>
                      <span className="deletions">-{file.deletions}</span>
                      <span>{file.changes} 行</span>
                      <span>{file.patch ? "含 patch" : "无 patch"}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="aiReviewSection">
              <div className="sectionHeader">
                <p className="panelLabel">AI Review</p>
                <div className="aiReviewActions">
                  <button type="button" onClick={handleGenerateReview} disabled={isReviewLoading}>
                    {isReviewLoading ? "生成中..." : "生成 AI Review"}
                  </button>
                  {aiReview && (
                    <button type="button" onClick={handleExportMarkdown}>
                      导出 Markdown
                    </button>
                  )}
                </div>
              </div>

              {reviewError && <div className="errorBox">{reviewError}</div>}

              {aiReview && (
                <>
                  <div className="reviewSummary">
                    <h3>变更总结</h3>
                    <p>{aiReview.summary}</p>
                  </div>
                  {aiReview.findings.length > 0 ? (
                    <ul className="reviewFindings">
                      {aiReview.findings.map((finding, index) => (
                        <li className="reviewFinding" key={index}>
                          <div className="findingHeader">
                            <span className={`riskPill ${finding.severity}`}>
                              {riskLevelLabels[finding.severity]}
                            </span>
                            <code>{finding.filePath}</code>
                            {finding.lineStart != null && finding.lineEnd != null && (
                              <span className="findingLines">
                                L{finding.lineStart}-L{finding.lineEnd}
                              </span>
                            )}
                          </div>
                          <p className="findingDesc">{finding.description}</p>
                          <p className="findingSuggestion">{finding.suggestion}</p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="emptyState">AI 未发现需要关注的问题。</p>
                  )}
                </>
              )}
            </div>
          </section>
        )}
      </section>
    </main>
  );
}
