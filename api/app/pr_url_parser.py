from dataclasses import dataclass
from urllib.parse import urlparse


class InvalidPullRequestUrl(ValueError):
    """Raised when a URL is not a supported GitHub Pull Request URL."""


@dataclass(frozen=True)
class ParsedPullRequest:
    owner: str
    repo: str
    pull_number: int


def parse_github_pr_url(pr_url: str) -> ParsedPullRequest:
    parsed_url = urlparse(pr_url.strip())

    if parsed_url.scheme not in {"http", "https"}:
        raise InvalidPullRequestUrl("请输入完整的 GitHub PR 链接。")

    if parsed_url.netloc.lower() != "github.com":
        raise InvalidPullRequestUrl("当前仅支持 github.com 的 PR 链接。")

    path_parts = [part for part in parsed_url.path.split("/") if part]
    if len(path_parts) < 4:
        raise InvalidPullRequestUrl("PR 链接缺少 owner、repo 或 PR 编号。")

    owner, repo, pull_segment, pull_number_text = path_parts[:4]
    if pull_segment != "pull":
        raise InvalidPullRequestUrl("链接必须指向 GitHub Pull Request。")

    if not pull_number_text.isdigit():
        raise InvalidPullRequestUrl("PR 编号必须是正整数。")

    pull_number = int(pull_number_text)
    if pull_number <= 0:
        raise InvalidPullRequestUrl("PR 编号必须大于 0。")

    return ParsedPullRequest(owner=owner, repo=repo, pull_number=pull_number)
