from dataclasses import dataclass
from typing import Optional

import httpx

GITHUB_API_BASE_URL = "https://api.github.com"


class GitHubClientError(RuntimeError):
    """Raised when GitHub PR metadata cannot be fetched."""


@dataclass(frozen=True)
class GitHubPullRequestMetadata:
    title: str
    author: str
    state: str
    is_draft: bool
    base_branch: str
    head_branch: str
    additions: int
    deletions: int
    changed_files: int
    html_url: str


@dataclass(frozen=True)
class GitHubPullRequestFile:
    path: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: Optional[str]


class GitHubClient:
    def __init__(self, http_client: Optional[httpx.Client] = None) -> None:
        self._http_client = http_client or httpx.Client(timeout=10.0)

    def fetch_pull_request_metadata(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> GitHubPullRequestMetadata:
        response = self._http_client.get(f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}")
        if response.status_code >= 400:
            raise GitHubClientError(f"无法获取 GitHub PR 元信息：GitHub API 返回 {response.status_code}。")

        payload = response.json()
        return GitHubPullRequestMetadata(
            title=payload["title"],
            author=payload["user"]["login"],
            state=payload["state"],
            is_draft=payload["draft"],
            base_branch=payload["base"]["ref"],
            head_branch=payload["head"]["ref"],
            additions=payload["additions"],
            deletions=payload["deletions"],
            changed_files=payload["changed_files"],
            html_url=payload["html_url"],
        )

    def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[GitHubPullRequestFile]:
        response = self._http_client.get(
            f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls/{pull_number}/files",
            params={"per_page": 100},
        )
        if response.status_code >= 400:
            raise GitHubClientError(f"无法获取 GitHub PR 变更文件：GitHub API 返回 {response.status_code}。")

        payload = response.json()
        return [
            GitHubPullRequestFile(
                path=item["filename"],
                status=item["status"],
                additions=item["additions"],
                deletions=item["deletions"],
                changes=item["changes"],
                patch=item.get("patch"),
            )
            for item in payload
        ]
