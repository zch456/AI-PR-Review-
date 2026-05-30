from typing import Literal, Optional

from pydantic import BaseModel, Field


class AnalyzePrRequest(BaseModel):
    prUrl: str = Field(min_length=1)


class PullRequestFileResponse(BaseModel):
    path: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str]


class RiskSignalResponse(BaseModel):
    riskType: str
    severity: Literal["low", "medium", "high"]
    confidence: Literal["low", "medium", "high"]
    filePath: str
    title: str
    reason: str
    suggestion: str


class AnalyzePrPreviewResponse(BaseModel):
    status: Literal["fetched"]
    owner: str
    repo: str
    pullNumber: int
    title: str
    author: str
    state: str
    isDraft: bool
    baseBranch: str
    headBranch: str
    additions: int
    deletions: int
    changedFiles: int
    htmlUrl: str
    files: list[PullRequestFileResponse]
    overallRisk: Literal["low", "medium", "high"]
    riskSignals: list[RiskSignalResponse]


class ReviewFinding(BaseModel):
    filePath: str
    severity: Literal["low", "medium", "high"]
    lineStart: Optional[int] = None
    lineEnd: Optional[int] = None
    description: str
    suggestion: str


class AiReviewResponse(BaseModel):
    summary: str
    findings: list[ReviewFinding]
