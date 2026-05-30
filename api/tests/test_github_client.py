import httpx
import pytest

from app.github_client import GitHubClient, GitHubClientError


def test_fetch_pull_request_metadata_maps_github_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/repos/zch456/AI-PR-Review-/pulls/1"
        return httpx.Response(
            status_code=200,
            json={
                "title": "初始化项目骨架",
                "state": "open",
                "draft": False,
                "user": {"login": "zch456"},
                "base": {"ref": "main"},
                "head": {"ref": "feature/init"},
                "additions": 120,
                "deletions": 4,
                "changed_files": 6,
                "html_url": "https://github.com/zch456/AI-PR-Review-/pull/1",
            },
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = GitHubClient(http_client=http_client)

    metadata = client.fetch_pull_request_metadata("zch456", "AI-PR-Review-", 1)

    assert metadata.title == "初始化项目骨架"
    assert metadata.author == "zch456"
    assert metadata.state == "open"
    assert metadata.is_draft is False
    assert metadata.base_branch == "main"
    assert metadata.head_branch == "feature/init"
    assert metadata.additions == 120
    assert metadata.deletions == 4
    assert metadata.changed_files == 6
    assert metadata.html_url == "https://github.com/zch456/AI-PR-Review-/pull/1"


def test_fetch_pull_request_metadata_raises_chinese_error_for_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={"message": "Not Found"})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = GitHubClient(http_client=http_client)

    with pytest.raises(GitHubClientError, match="无法获取 GitHub PR 元信息"):
        client.fetch_pull_request_metadata("zch456", "missing-repo", 404)


def test_fetch_pull_request_files_maps_github_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/repos/zch456/AI-PR-Review-/pulls/2/files"
        assert request.url.params["per_page"] == "100"
        return httpx.Response(
            status_code=200,
            json=[
                {
                    "filename": "api/app/main.py",
                    "status": "modified",
                    "additions": 12,
                    "deletions": 3,
                    "changes": 15,
                    "patch": "@@ -1,3 +1,4 @@",
                },
                {
                    "filename": "web/public/favicon.svg",
                    "status": "added",
                    "additions": 4,
                    "deletions": 0,
                    "changes": 4,
                },
            ],
        )

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = GitHubClient(http_client=http_client)

    files = client.fetch_pull_request_files("zch456", "AI-PR-Review-", 2)

    assert len(files) == 2
    assert files[0].path == "api/app/main.py"
    assert files[0].status == "modified"
    assert files[0].additions == 12
    assert files[0].deletions == 3
    assert files[0].changes == 15
    assert files[0].patch == "@@ -1,3 +1,4 @@"
    assert files[1].path == "web/public/favicon.svg"
    assert files[1].patch is None


def test_fetch_pull_request_files_raises_chinese_error_for_github_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=500, json={"message": "Server Error"})

    http_client = httpx.Client(transport=httpx.MockTransport(handler))
    client = GitHubClient(http_client=http_client)

    with pytest.raises(GitHubClientError, match="无法获取 GitHub PR 变更文件"):
        client.fetch_pull_request_files("zch456", "AI-PR-Review-", 2)
