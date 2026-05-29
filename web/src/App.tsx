import { FormEvent, useState } from "react";

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
          <p className="subtitle">
            粘贴 GitHub PR 链接，获取 PR 基础元信息；后续 PR 将逐步接入 diff 获取、风险识别和 AI Review。
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
            </dl>
          </section>
        )}
      </section>
    </main>
  );
}
