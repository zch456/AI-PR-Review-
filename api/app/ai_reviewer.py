import json
from dataclasses import dataclass
from typing import Optional

import httpx

from .config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from .github_client import GitHubPullRequestFile

# 字符数上限，约为 37K token（中文场景）
MAX_INPUT_CHARS = 150_000

SYSTEM_PROMPT = """你是一个经验丰富的资深代码审查工程师。你的任务是分析下方的 Pull Request 变更，并输出结构化的审查结果。

输出格式要求：
- 必须输出纯 JSON 对象，不要包含 markdown 代码块标记或额外说明文字。
- JSON 必须包含以下字段：
  {
    "summary": "对本次 PR 变更的整体总结（2-5 句话，中文）。简要说明 PR 的目的、主要变更范围、以及值得注意的改动。",
    "findings": [
      {
        "filePath": "文件路径",
        "severity": "low|medium|high",
        "lineStart": 行号或 null,
        "lineEnd": 行号或 null,
        "description": "发现的问题描述（中文）",
        "suggestion": "改进建议（中文）"
      }
    ]
  }

审查重点：
1. 逻辑正确性：是否存在边界条件错误、空指针风险、并发问题等。
2. 安全性：是否存在注入、信息泄露、权限绕过等风险。
3. 代码质量：可读性、可维护性、是否符合单一职责原则。
4. 兼容性：是否有破坏向后兼容的变更。
5. 测试覆盖：重要逻辑是否缺少对应的测试。
6. 配置风险：硬编码、环境依赖等。

对于没有问题的文件，不必强求输出 findings；如果有多个问题，每个问题应单独作为一个 finding 输出。"""


class AiReviewerError(RuntimeError):
    """Raised when AI review generation fails."""


@dataclass(frozen=True)
class ReviewFindingData:
    file_path: str
    severity: str  # "low" | "medium" | "high"
    line_start: Optional[int]
    line_end: Optional[int]
    description: str
    suggestion: str


@dataclass(frozen=True)
class AiReviewResult:
    summary: str
    findings: list[ReviewFindingData]


def generate_code_review(
    pr_title: str,
    pr_author: str,
    base_branch: str,
    head_branch: str,
    files: list[GitHubPullRequestFile],
    http_client: Optional[httpx.Client] = None,
) -> AiReviewResult:
    """构建 prompt 并调用 DeepSeek API 生成代码审查结果。"""
    if not DEEPSEEK_API_KEY:
        raise AiReviewerError("未配置 DEEPSEEK_API_KEY 环境变量。请设置后重启服务。")

    user_message = _build_user_message(
        pr_title=pr_title,
        pr_author=pr_author,
        base_branch=base_branch,
        head_branch=head_branch,
        files=files,
    )

    client = http_client or httpx.Client(timeout=120.0)

    try:
        response = client.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3,
            },
        )
    except httpx.RequestError as exc:
        raise AiReviewerError("无法连接到 DeepSeek API，请检查网络或 API 地址配置。") from exc

    if response.status_code >= 400:
        _raise_http_error(response)

    payload = response.json()
    return _parse_ai_response(payload)


def _build_user_message(
    pr_title: str,
    pr_author: str,
    base_branch: str,
    head_branch: str,
    files: list[GitHubPullRequestFile],
) -> str:
    """构建发送给 DeepSeek 的用户消息，包含 PR 元信息和文件 diff。"""
    lines: list[str] = []
    lines.append("PR 元信息")
    lines.append(f"- 标题: {pr_title}")
    lines.append(f"- 作者: {pr_author}")
    lines.append(f"- 分支: {head_branch} → {base_branch}")
    lines.append(f"- 变更文件数量: {len(files)}")
    lines.append("")
    lines.append("变更文件列表:")
    lines.append("")

    # 按变更行数降序排列，优先发送最重要的文件
    sorted_files = sorted(files, key=lambda f: f.changes, reverse=True)

    char_count = len("\n".join(lines))
    omitted_count = 0

    for file in sorted_files:
        file_entry = _format_file_entry(file)

        if char_count + len(file_entry) <= MAX_INPUT_CHARS:
            lines.append(file_entry)
            char_count += len(file_entry)
        else:
            # 剩余空间不够，尝试截断 patch
            remaining = MAX_INPUT_CHARS - char_count
            truncated_entry = _format_file_entry(file, max_patch_chars=remaining - 200)
            if len(truncated_entry) > 100:  # 至少能放下文件名和状态
                lines.append(truncated_entry)
                char_count += len(truncated_entry)
            omitted_count += 1

    if omitted_count > 0:
        lines.append("")
        lines.append(
            f"注意：由于 token 限制，{omitted_count} 个文件的变更内容已被省略或截断。"
            "请基于已有信息进行分析，并在 summary 中说明分析范围的局限性。"
        )

    return "\n".join(lines)


def _format_file_entry(file: GitHubPullRequestFile, max_patch_chars: Optional[int] = None) -> str:
    """格式化单个文件变更为 prompt 条目。"""
    status_label = {"added": "新增", "modified": "修改", "removed": "删除",
                    "renamed": "重命名", "copied": "复制", "changed": "变更"}.get(file.status, file.status)

    parts: list[str] = []
    parts.append(f"### 文件: {file.path} ({status_label})  +{file.additions} -{file.deletions}")
    parts.append("")

    if file.patch:
        patch = file.patch
        if max_patch_chars is not None and len(patch) > max_patch_chars:
            patch = patch[:max_patch_chars] + "\n... (patch 已截断)"
        parts.append("```diff")
        parts.append(patch)
        parts.append("```")
    else:
        parts.append("（无 patch 信息）")

    parts.append("")
    return "\n".join(parts)


def _raise_http_error(response: httpx.Response) -> None:
    """解析 DeepSeek HTTP 错误并抛出 AiReviewerError。"""
    try:
        detail = response.json()
    except Exception:
        detail = response.text

    if response.status_code == 401:
        raise AiReviewerError("DeepSeek API 认证失败，请检查 DEEPSEEK_API_KEY 是否正确。")
    if response.status_code == 429:
        raise AiReviewerError("DeepSeek API 请求频率过高，请稍后重试。")
    if response.status_code >= 500:
        raise AiReviewerError(f"DeepSeek 服务暂时不可用（HTTP {response.status_code}），请稍后重试。")

    raise AiReviewerError(f"DeepSeek API 返回错误（HTTP {response.status_code}）：{detail}")


def _parse_ai_response(payload: dict) -> AiReviewResult:
    """从 DeepSeek API 响应中提取并验证审查结果。"""
    try:
        choices = payload["choices"]
        content = choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AiReviewerError("DeepSeek API 响应结构异常，缺少 choices 或 message 字段。") from exc

    # 尝试解析 JSON，处理可能的 markdown 代码块包裹
    parsed = _extract_json(content)

    # 验证必要字段
    if not isinstance(parsed, dict):
        raise AiReviewerError("AI 返回的响应不是有效的 JSON 对象。")

    summary = parsed.get("summary")
    if not summary or not isinstance(summary, str):
        raise AiReviewerError("AI 返回的响应缺少 summary 字段或格式不正确。")

    raw_findings = parsed.get("findings")
    if raw_findings is None:
        raise AiReviewerError("AI 返回的响应缺少 findings 字段。")
    if not isinstance(raw_findings, list):
        raise AiReviewerError("AI 返回的 findings 不是数组格式。")

    findings: list[ReviewFindingData] = []
    for idx, item in enumerate(raw_findings):
        try:
            if not isinstance(item, dict):
                continue
            finding = ReviewFindingData(
                file_path=str(item.get("filePath", "")),
                severity=_normalize_severity(item.get("severity", "low")),
                line_start=_optional_int(item.get("lineStart")),
                line_end=_optional_int(item.get("lineEnd")),
                description=str(item.get("description", "")),
                suggestion=str(item.get("suggestion", "")),
            )
            if finding.file_path and finding.description:
                findings.append(finding)
        except Exception:
            # 个别条目格式错误，跳过，继续处理其余条目
            continue

    return AiReviewResult(summary=summary, findings=findings)


def _extract_json(content: str) -> dict:
    """从 AI 输出中提取 JSON 对象，处理可能的 markdown 代码块包裹。"""
    text = content.strip()

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试去掉 ```json ... ``` 包裹
    if text.startswith("```"):
        lines = text.splitlines()
        # 去掉首行的 ```json 或 ```
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        # 去掉末行的 ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        # 最后尝试：查找第一个 { 和最后一个 }
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(content[start:end + 1])
            except json.JSONDecodeError:
                pass
        raise AiReviewerError("AI 返回的响应不是有效的 JSON 格式，无法解析。") from exc


def _normalize_severity(value: object) -> str:
    """将严重程度规范化为 low/medium/high。"""
    if isinstance(value, str) and value.lower() in {"low", "medium", "high"}:
        return value.lower()
    return "low"


def _optional_int(value: object) -> Optional[int]:
    """安全转换为 Optional[int]。"""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
