from typing import Literal

from pydantic import BaseModel, Field


class AnalyzePrRequest(BaseModel):
    prUrl: str = Field(min_length=1)


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
