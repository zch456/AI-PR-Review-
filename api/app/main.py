from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .github_client import GitHubClient, GitHubClientError
from .pr_url_parser import InvalidPullRequestUrl, parse_github_pr_url
from .risk_engine import assess_pull_request_risks, calculate_overall_risk
from .schemas import AnalyzePrPreviewResponse, AnalyzePrRequest, PullRequestFileResponse, RiskSignalResponse


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
        files = github_client.fetch_pull_request_files(
            owner=parsed.owner,
            repo=parsed.repo,
            pull_number=parsed.pull_number,
        )
    except GitHubClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    risk_signals = assess_pull_request_risks(files)

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
        files=[
            PullRequestFileResponse(
                path=file.path,
                status=file.status,
                additions=file.additions,
                deletions=file.deletions,
                changes=file.changes,
                patch=file.patch,
            )
            for file in files
        ],
        overallRisk=calculate_overall_risk(risk_signals),
        riskSignals=[
            RiskSignalResponse(
                riskType=risk.risk_type,
                severity=risk.severity,
                confidence=risk.confidence,
                filePath=risk.file_path,
                title=risk.title,
                reason=risk.reason,
                suggestion=risk.suggestion,
            )
            for risk in risk_signals
        ],
    )
