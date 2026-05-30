from __future__ import annotations

import json

import httpx
import pytest

from app.ai_reviewer import (
    MAX_INPUT_CHARS,
    AiReviewResult,
    AiReviewerError,
    ReviewFindingData,
    _build_user_message,
    _extract_json,
    _parse_ai_response,
    generate_code_review,
)
from app.github_client import GitHubPullRequestFile


# ---------- helpers ----------

def _make_file(path: str, changes: int, patch: str | None = None, status: str = "modified") -> GitHubPullRequestFile:
    return GitHubPullRequestFile(
        path=path,
        status=status,
        additions=changes // 2,
        deletions=changes - changes // 2,
        changes=changes,
        patch=patch,
    )


def _deepseek_json_response(content: dict) -> httpx.Response:
    """构建模拟的 DeepSeek 成功响应。"""
    return httpx.Response(
        status_code=200,
        json={
            "choices": [
                {
                    "message": {
                        "content": json.dumps(content, ensure_ascii=False),
                    }
                }
            ]
        },
    )


def _mock_transport(response: httpx.Response):
    """创建一个返回固定响应的 MockTransport。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return response

    return httpx.MockTransport(handler)


# ---------- tests ----------


class TestGenerateCodeReviewSuccess:
    def test_returns_parsed_result(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "sk-test")

        expected = {"summary": "本次 PR 增加了新功能。", "findings": []}
        client = httpx.Client(transport=_mock_transport(_deepseek_json_response(expected)))

        result = generate_code_review(
            pr_title="测试 PR",
            pr_author="tester",
            base_branch="main",
            head_branch="feature/x",
            files=[],
            http_client=client,
        )

        assert isinstance(result, AiReviewResult)
        assert result.summary == "本次 PR 增加了新功能。"
        assert result.findings == []

    def test_parses_findings_with_all_fields(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "sk-test")

        content = {
            "summary": "包含多个问题的 PR。",
            "findings": [
                {
                    "filePath": "src/main.py",
                    "severity": "high",
                    "lineStart": 42,
                    "lineEnd": 58,
                    "description": "空指针风险",
                    "suggestion": "添加 null 检查",
                },
                {
                    "filePath": "src/utils.py",
                    "severity": "medium",
                    "lineStart": None,
                    "lineEnd": None,
                    "description": "代码重复",
                    "suggestion": "提取公共函数",
                },
            ],
        }
        client = httpx.Client(transport=_mock_transport(_deepseek_json_response(content)))

        result = generate_code_review(
            pr_title="PR",
            pr_author="a",
            base_branch="main",
            head_branch="dev",
            files=[],
            http_client=client,
        )

        assert len(result.findings) == 2
        f0 = result.findings[0]
        assert f0.file_path == "src/main.py"
        assert f0.severity == "high"
        assert f0.line_start == 42
        assert f0.line_end == 58
        assert f0.description == "空指针风险"
        assert f0.suggestion == "添加 null 检查"

        f1 = result.findings[1]
        assert f1.line_start is None
        assert f1.line_end is None


class TestMissingApiKey:
    def test_raises_when_api_key_is_empty(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "")

        with pytest.raises(AiReviewerError, match="DEEPSEEK_API_KEY"):
            generate_code_review(
                pr_title="t", pr_author="a", base_branch="m", head_branch="f", files=[],
            )


class TestHttpErrors:
    def test_401_raises_auth_error(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "sk-test")
        transport = _mock_transport(httpx.Response(status_code=401, json={"error": "unauthorized"}))
        client = httpx.Client(transport=transport)

        with pytest.raises(AiReviewerError, match="认证失败"):
            generate_code_review("t", "a", "m", "f", [], http_client=client)

    def test_429_raises_rate_limit_error(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "sk-test")
        transport = _mock_transport(httpx.Response(status_code=429, json={}))
        client = httpx.Client(transport=transport)

        with pytest.raises(AiReviewerError, match="频率过高"):
            generate_code_review("t", "a", "m", "f", [], http_client=client)

    def test_500_raises_service_error(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "sk-test")
        transport = _mock_transport(httpx.Response(status_code=500, text="Internal Server Error"))
        client = httpx.Client(transport=transport)

        with pytest.raises(AiReviewerError, match="暂时不可用"):
            generate_code_review("t", "a", "m", "f", [], http_client=client)


class TestConnectionError:
    def test_network_error_raises(self, monkeypatch):
        monkeypatch.setattr("app.ai_reviewer.DEEPSEEK_API_KEY", "sk-test")

        def failing_handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

        client = httpx.Client(transport=httpx.MockTransport(failing_handler))

        with pytest.raises(AiReviewerError, match="无法连接"):
            generate_code_review("t", "a", "m", "f", [], http_client=client)


class TestParseAiResponse:
    def test_missing_choices_raises(self):
        with pytest.raises(AiReviewerError, match="响应结构异常"):
            _parse_ai_response({})

    def test_missing_summary_raises(self):
        payload = {"choices": [{"message": {"content": '{"findings": []}'}}]}
        with pytest.raises(AiReviewerError, match="缺少 summary"):
            _parse_ai_response(payload)

    def test_missing_findings_raises(self):
        payload = {"choices": [{"message": {"content": '{"summary": "ok"}'}}]}
        with pytest.raises(AiReviewerError, match="缺少 findings"):
            _parse_ai_response(payload)

    def test_findings_not_array_raises(self):
        payload = {"choices": [{"message": {"content": '{"summary": "ok", "findings": "bad"}'}}]}
        with pytest.raises(AiReviewerError, match="不是数组"):
            _parse_ai_response(payload)

    def test_malformed_finding_skipped(self):
        """个别 finding 格式错误时跳过该条，保留其余。"""
        content = {
            "summary": "ok",
            "findings": [
                {
                    "filePath": "good.py",
                    "severity": "low",
                    "description": "ok",
                    "suggestion": "ok",
                },
                "not_an_object",  # 格式错误，应跳过
                {
                    "filePath": "also_good.py",
                    "severity": "high",
                    "description": "ok too",
                    "suggestion": "fix it",
                },
            ],
        }
        payload = {"choices": [{"message": {"content": json.dumps(content)}}]}

        result = _parse_ai_response(payload)
        assert result.summary == "ok"
        assert len(result.findings) == 2
        assert result.findings[0].file_path == "good.py"
        assert result.findings[1].file_path == "also_good.py"

    def test_markdown_code_block_handled(self):
        """JSON 被 markdown 代码块包裹时也能正确解析。"""
        content = '```json\n{"summary": "ok", "findings": []}\n```'
        payload = {"choices": [{"message": {"content": content}}]}

        result = _parse_ai_response(payload)
        assert result.summary == "ok"


class TestExtractJson:
    def test_plain_json(self):
        assert _extract_json('{"a": 1}') == {"a": 1}

    def test_markdown_wrapped_json(self):
        assert _extract_json('```json\n{"a": 1}\n```') == {"a": 1}

    def test_markdown_no_lang(self):
        assert _extract_json('```\n{"a": 1}\n```') == {"a": 1}

    def test_json_surrounded_by_text(self):
        result = _extract_json('Here is the result: {"a": 1} done.')
        assert result == {"a": 1}

    def test_invalid_json_raises(self):
        with pytest.raises(AiReviewerError, match="不是有效的 JSON"):
            _extract_json("not json at all")


class TestBuildUserMessage:
    def test_includes_pr_metadata(self):
        message = _build_user_message(
            pr_title="测试 PR",
            pr_author="tester",
            base_branch="main",
            head_branch="feature/x",
            files=[],
        )
        assert "测试 PR" in message
        assert "tester" in message
        assert "feature/x → main" in message

    def test_includes_file_patches(self):
        files = [
            _make_file("src/main.py", changes=20, patch="@@ -1,3 +1,5 @@"),
        ]
        message = _build_user_message("t", "a", "m", "f", files)
        assert "src/main.py" in message
        assert "@@ -1,3 +1,5 @@" in message

    def test_truncates_when_exceeds_limit(self):
        """超长 patch 应被截断。"""
        huge_patch = "x" * (MAX_INPUT_CHARS + 1000)
        files = [_make_file("big.py", changes=1, patch=huge_patch)]

        message = _build_user_message("t", "a", "m", "f", files)
        assert len(message) <= MAX_INPUT_CHARS + 2000  # 允许截断笔记的额外字符
        # 应该包含截断标记
        assert ("截断" in message) or ("省略" in message) or ("限制" in message)

    def test_files_sorted_by_changes_desc(self):
        """文件应按变更行数降序排列。"""
        files = [
            _make_file("c.py", changes=10, patch="@@ c"),
            _make_file("a.py", changes=30, patch="@@ a"),
            _make_file("b.py", changes=20, patch="@@ b"),
        ]
        message = _build_user_message("t", "a", "m", "f", files)

        pos_a = message.index("a.py")
        pos_b = message.index("b.py")
        pos_c = message.index("c.py")
        assert pos_a < pos_b < pos_c  # 30 > 20 > 10


class TestOmittedFilesNote:
    def test_note_added_when_files_omitted(self, monkeypatch):
        """使用极小上限触发省略逻辑，验证省略提示出现。"""
        monkeypatch.setattr("app.ai_reviewer.MAX_INPUT_CHARS", 300)

        files = [
            _make_file(f"file_{i}.py", changes=10, patch="@@ -1,1 +1,1 @@\n+line\n") for i in range(20)
        ]
        message = _build_user_message("t", "a", "m", "f", files)

        assert "限制" in message or "省略" in message
