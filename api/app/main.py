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
        parsed = parse_github_pr_url(request.prUrl)
    except InvalidPullRequestUrl as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AnalyzePrPreviewResponse(
        status="parsed",
        owner=parsed.owner,
        repo=parsed.repo,
        pullNumber=parsed.pull_number,
    )
