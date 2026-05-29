from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .github_client import GitHubClient, GitHubClientError
from .pr_url_parser import InvalidPullRequestUrl, parse_github_pr_url
from .schemas import AnalyzePrPreviewResponse, AnalyzePrRequest


app = FastAPI(title="AI PR Review Assistant API", version="0.1.0")
github_client = GitHubClient()

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
        parsed = parse_github_pr_url(request.prUrl)
    except InvalidPullRequestUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        metadata = github_client.fetch_pull_request_metadata(
            owner=parsed.owner,
            repo=parsed.repo,
            pull_number=parsed.pull_number,
        )
    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return AnalyzePrPreviewResponse(
        status="fetched",
        owner=parsed.owner,
        repo=parsed.repo,
        pullNumber=parsed.pull_number,
        title=metadata.title,
        author=metadata.author,
        state=metadata.state,
        isDraft=metadata.is_draft,
        baseBranch=metadata.base_branch,
        headBranch=metadata.head_branch,
        additions=metadata.additions,
        deletions=metadata.deletions,
        changedFiles=metadata.changed_files,
        htmlUrl=metadata.html_url,
    )
