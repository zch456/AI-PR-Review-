from fastapi.testclient import TestClient

from app.ai_reviewer import AiReviewResult, ReviewFindingData
from app.github_client import GitHubPullRequestFile, GitHubPullRequestMetadata
from app.main import app

client = TestClient(app)

VALID_PR_URL = "https://github.com/zch456/AI-PR-Review-/pull/7"


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


def stub_generate_code_review(
    pr_title: str,
    pr_author: str,
    base_branch: str,
    head_branch: str,
    files: list,
    http_client=None,
) -> AiReviewResult:
    return AiReviewResult(
        summary="这是一段由 AI 生成的变更总结。",
        findings=[
            ReviewFindingData(
                file_path="api/app/main.py",
                severity="medium",
                line_start=10,
                line_end=25,
                description="边界条件处理不完整。",
                suggestion="建议增加空值检查。",
            )
        ],
    )


def test_generate_review_returns_ai_result(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", StubGitHubClient())
    monkeypatch.setattr("app.main.generate_code_review", stub_generate_code_review)

    response = client.post(
        "/api/generate-review",
        json={"prUrl": VALID_PR_URL},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == "这是一段由 AI 生成的变更总结。"
    assert len(payload["findings"]) == 1
    finding = payload["findings"][0]
    assert finding["filePath"] == "api/app/main.py"
    assert finding["severity"] == "medium"
    assert finding["lineStart"] == 10
    assert finding["lineEnd"] == 25
    assert finding["description"] == "边界条件处理不完整。"
    assert finding["suggestion"] == "建议增加空值检查。"


def test_generate_review_rejects_invalid_url() -> None:
    response = client.post("/api/generate-review", json={"prUrl": "https://example.com/demo"})

    assert response.status_code == 400
    assert response.json()["detail"] == "当前仅支持 github.com 的 PR 链接。"


def test_generate_review_handles_ai_reviewer_error(monkeypatch) -> None:
    monkeypatch.setattr("app.main.github_client", StubGitHubClient())

    def failing_review(*args, **kwargs):
        from app.ai_reviewer import AiReviewerError
        raise AiReviewerError("模拟 AI Review 失败。")

    monkeypatch.setattr("app.main.generate_code_review", failing_review)

    response = client.post("/api/generate-review", json={"prUrl": VALID_PR_URL})

    assert response.status_code == 502
    assert response.json()["detail"] == "模拟 AI Review 失败。"
