from fastapi.testclient import TestClient

from app.github_client import GitHubPullRequestFile, GitHubPullRequestMetadata
from app.main import app


client = TestClient(app)


class StubGitHubClient:
    def fetch_pull_request_metadata(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> GitHubPullRequestMetadata:
        return GitHubPullRequestMetadata(
            title="测试 PR",
            author=owner,
            state="open",
            is_draft=False,
            base_branch="main",
            head_branch="feature/test",
            additions=10,
            deletions=2,
            changed_files=1,
            html_url=f"https://github.com/{owner}/{repo}/pull/{pull_number}",
        )

    def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[GitHubPullRequestFile]:
        return [
            GitHubPullRequestFile(
                path="api/app/main.py",
                status="modified",
                additions=10,
                deletions=2,
                changes=12,
                patch="@@ -1,2 +1,3 @@",
            )
        ]


def test_analyze_pr_returns_metadata_preview(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", StubGitHubClient())

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/7"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "fetched"
    assert payload["owner"] == "zch456"
    assert payload["repo"] == "AI-PR-Review-"
    assert payload["pullNumber"] == 7
    assert payload["title"] == "测试 PR"
    assert payload["files"] == [
        {
            "path": "api/app/main.py",
            "status": "modified",
            "additions": 10,
            "deletions": 2,
            "changes": 12,
            "patch": "@@ -1,2 +1,3 @@",
        }
    ]
    assert payload["overallRisk"] == "low"
    assert payload["riskSignals"] == []


def test_analyze_pr_rejects_invalid_url() -> None:
    response = client.post("/api/analyze-pr", json={"prUrl": "https://example.com/demo/repo/pull/1"})

    assert response.status_code == 400
    assert response.json() == {"detail": "当前仅支持 github.com 的 PR 链接。"}
