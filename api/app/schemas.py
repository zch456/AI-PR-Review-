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
