import pytest

from app.pr_url_parser import InvalidPullRequestUrl, parse_github_pr_url


def test_parse_standard_github_pull_request_url() -> None:
    parsed = parse_github_pr_url("https://github.com/zch456/AI-PR-Review-/pull/12")

    assert parsed.owner == "zch456"
    assert parsed.repo == "AI-PR-Review-"
    assert parsed.pull_number == 12


def test_parse_url_with_trailing_slash_and_query_string() -> None:
    parsed = parse_github_pr_url("https://github.com/openai/openai-python/pull/99/?tab=files")

    assert parsed.owner == "openai"
    assert parsed.repo == "openai-python"
    assert parsed.pull_number == 99


@pytest.mark.parametrize(
    "pr_url",
    [
        "",
        "not-a-url",
        "https://example.com/owner/repo/pull/1",
        "https://github.com/owner/repo/issues/1",
        "https://github.com/owner/repo/pull/not-number",
        "https://github.com/owner/repo/pull/0",
    ],
)
def test_reject_invalid_pull_request_urls(pr_url: str) -> None:
    with pytest.raises(InvalidPullRequestUrl):
        parse_github_pr_url(pr_url)
