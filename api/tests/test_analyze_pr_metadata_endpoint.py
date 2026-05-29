from fastapi.testclient import TestClient

from app.github_client import GitHubClientError, GitHubPullRequestMetadata
from app.main import app


client = TestClient(app)


class StubGitHubClient:
    def fetch_pull_request_metadata(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> GitHubPullRequestMetadata:
        assert owner == "zch456"
        assert repo == "AI-PR-Review-"
        assert pull_number == 2
        return GitHubPullRequestMetadata(
            title="接入 GitHub 元信息",
            author="zch456",
            state="open",
            is_draft=False,
            base_branch="main",
            head_branch="feature/github-metadata",
            additions=88,
            deletions=6,
            changed_files=3,
            html_url="https://github.com/zch456/AI-PR-Review-/pull/2",
        )


class FailingGitHubClient:
    def fetch_pull_request_metadata(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> GitHubPullRequestMetadata:
        raise GitHubClientError("无法获取 GitHub PR 元信息：GitHub API 返回 404。")


def test_analyze_pr_returns_github_pull_request_metadata(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", StubGitHubClient())

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/2"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "fetched",
        "owner": "zch456",
        "repo": "AI-PR-Review-",
        "pullNumber": 2,
        "title": "接入 GitHub 元信息",
        "author": "zch456",
        "state": "open",
        "isDraft": False,
        "baseBranch": "main",
        "headBranch": "feature/github-metadata",
        "additions": 88,
        "deletions": 6,
        "changedFiles": 3,
        "htmlUrl": "https://github.com/zch456/AI-PR-Review-/pull/2",
    }


def test_analyze_pr_returns_bad_gateway_when_github_lookup_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", FailingGitHubClient())

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/404"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "无法获取 GitHub PR 元信息：GitHub API 返回 404。"}
