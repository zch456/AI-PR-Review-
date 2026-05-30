from fastapi.testclient import TestClient

from app.github_client import GitHubClientError, GitHubPullRequestFile, GitHubPullRequestMetadata
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

    def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[GitHubPullRequestFile]:
        assert owner == "zch456"
        assert repo == "AI-PR-Review-"
        assert pull_number == 2
        return [
            GitHubPullRequestFile(
                path="api/app/github_client.py",
                status="added",
                additions=53,
                deletions=0,
                changes=53,
                patch="@@ -0,0 +1,53 @@",
            ),
            GitHubPullRequestFile(
                path="web/src/App.tsx",
                status="modified",
                additions=20,
                deletions=6,
                changes=26,
                patch=None,
            ),
        ]


class FailingGitHubClient:
    def fetch_pull_request_metadata(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> GitHubPullRequestMetadata:
        raise GitHubClientError("无法获取 GitHub PR 元信息：GitHub API 返回 404。")


class FailingFilesGitHubClient(StubGitHubClient):
    def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[GitHubPullRequestFile]:
        raise GitHubClientError("无法获取 GitHub PR 变更文件：GitHub API 返回 500。")


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
        "files": [
            {
                "path": "api/app/github_client.py",
                "status": "added",
                "additions": 53,
                "deletions": 0,
                "changes": 53,
                "patch": "@@ -0,0 +1,53 @@",
            },
            {
                "path": "web/src/App.tsx",
                "status": "modified",
                "additions": 20,
                "deletions": 6,
                "changes": 26,
                "patch": None,
            },
        ],
        "overallRisk": "low",
        "riskSignals": [],
    }


def test_analyze_pr_returns_bad_gateway_when_github_lookup_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", FailingGitHubClient())

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/404"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "无法获取 GitHub PR 元信息：GitHub API 返回 404。"}


def test_analyze_pr_returns_bad_gateway_when_github_file_lookup_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", FailingFilesGitHubClient())

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/2"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "无法获取 GitHub PR 变更文件：GitHub API 返回 500。"}


class RiskyGitHubClient(StubGitHubClient):
    def fetch_pull_request_files(
        self,
        owner: str,
        repo: str,
        pull_number: int,
    ) -> list[GitHubPullRequestFile]:
        return [
            GitHubPullRequestFile(
                path="api/app/auth/session.py",
                status="modified",
                additions=14,
                deletions=3,
                changes=17,
                patch='@@ -1 +1,2 @@\n+API_TOKEN = "demo-token"',
            ),
            GitHubPullRequestFile(
                path="package.json",
                status="modified",
                additions=5,
                deletions=1,
                changes=6,
                patch="@@ -1 +1 @@",
            ),
        ]


def test_analyze_pr_returns_rule_based_risk_signals(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", RiskyGitHubClient())

    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/2"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["overallRisk"] == "high"
    assert [risk["riskType"] for risk in payload["riskSignals"]] == [
        "security_sensitive_file",
        "possible_secret",
        "dependency_change",
    ]
    assert payload["riskSignals"][0]["filePath"] == "api/app/auth/session.py"
    assert payload["riskSignals"][0]["severity"] == "high"
