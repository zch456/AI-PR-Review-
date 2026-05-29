from typing import Literal

from pydantic import BaseModel, Field


class AnalyzePrRequest(BaseModel):
    prUrl: str = Field(min_length=1)


class AnalyzePrPreviewResponse(BaseModel):
    status: Literal["parsed"]
    owner: str
    repo: str
    pullNumber: int
