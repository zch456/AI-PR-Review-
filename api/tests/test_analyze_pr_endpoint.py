from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analyze_pr_returns_parsed_preview() -> None:
    response = client.post(
        "/api/analyze-pr",
        json={"prUrl": "https://github.com/zch456/AI-PR-Review-/pull/7"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "parsed",
        "owner": "zch456",
        "repo": "AI-PR-Review-",
        "pullNumber": 7,
    }


def test_analyze_pr_rejects_invalid_url() -> None:
    response = client.post("/api/analyze-pr", json={"prUrl": "https://example.com/demo/repo/pull/1"})

    assert response.status_code == 400
    assert response.json() == {"detail": "当前仅支持 github.com 的 PR 链接。"}
