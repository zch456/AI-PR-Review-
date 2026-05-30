from dataclasses import dataclass
from typing import Literal, Optional

from .github_client import GitHubPullRequestFile


RiskLevel = Literal["low", "medium", "high"]
Confidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class RiskSignal:
    risk_type: str
    severity: RiskLevel
    confidence: Confidence
    file_path: str
    title: str
    reason: str
    suggestion: str


DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
}

CONFIG_FILE_SUFFIXES = (
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".env",
)

SECURITY_PATH_KEYWORDS = (
    "auth",
    "authentication",
    "authorize",
    "permission",
    "security",
    "jwt",
    "token",
    "login",
    "session",
    "middleware",
)

SECRET_KEYWORDS = (
    "api_key",
    "apikey",
    "secret",
    "token",
    "password",
    "private_key",
)


def assess_pull_request_risks(files: list[GitHubPullRequestFile]) -> list[RiskSignal]:
    risks: list[RiskSignal] = []

    for file in files:
        normalized_path = file.path.lower()
        file_name = normalized_path.rsplit("/", 1)[-1]

        if file_name in DEPENDENCY_FILES:
            risks.append(
                RiskSignal(
                    risk_type="dependency_change",
                    severity="medium",
                    confidence="high",
                    file_path=file.path,
                    title="依赖变更",
                    reason="依赖文件变更可能影响安装、构建或运行时行为。",
                    suggestion="重点确认新增依赖的用途、版本范围和兼容性，并补充安装或构建验证。",
                )
            )

        if _is_configuration_file(normalized_path, file_name):
            risks.append(
                RiskSignal(
                    risk_type="configuration_change",
                    severity="medium",
                    confidence="medium",
                    file_path=file.path,
                    title="配置变更",
                    reason="配置或工作流变更可能影响部署、CI、运行参数或环境行为。",
                    suggestion="检查配置是否覆盖本地、测试和生产场景，并确认失败回滚方式。",
                )
            )

        is_test_file = _is_test_file(normalized_path)

        if not is_test_file and any(keyword in normalized_path for keyword in SECURITY_PATH_KEYWORDS):
            risks.append(
                RiskSignal(
                    risk_type="security_sensitive_file",
                    severity="high",
                    confidence="medium",
                    file_path=file.path,
                    title="鉴权或安全相关文件变更",
                    reason="该文件路径命中鉴权、安全、会话或中间件相关关键词，可能影响访问控制边界。",
                    suggestion="重点 Review 鉴权条件、默认分支、失败处理和越权场景，并补充安全相关测试。",
                )
            )

        if is_test_file and (file.status == "removed" or file.deletions > file.additions):
            risks.append(
                RiskSignal(
                    risk_type="test_deletion",
                    severity="medium",
                    confidence="high",
                    file_path=file.path,
                    title="测试覆盖减少",
                    reason="测试文件删除行数多于新增行数，可能降低回归保护。",
                    suggestion="确认被删除的测试是否已有替代覆盖，必要时补充新的测试用例。",
                )
            )

        if file.changes >= 300:
            risks.append(
                RiskSignal(
                    risk_type="large_change",
                    severity="medium",
                    confidence="high",
                    file_path=file.path,
                    title="单文件变更较大",
                    reason="单个文件变更超过 300 行，Review 成本和漏看风险较高。",
                    suggestion="优先拆分逻辑主题，或在 PR 描述中解释大变更来源和验证方式。",
                )
            )

        if _patch_adds_possible_secret(file.patch):
            risks.append(
                RiskSignal(
                    risk_type="possible_secret",
                    severity="high",
                    confidence="medium",
                    file_path=file.path,
                    title="疑似敏感信息写入",
                    reason="新增代码中出现 key、secret、token、password 等敏感配置关键词。",
                    suggestion="确认没有提交真实密钥；如只是配置字段名，应确保值来自环境变量或安全配置中心。",
                )
            )

    return risks


def calculate_overall_risk(risks: list[RiskSignal]) -> RiskLevel:
    if any(risk.severity == "high" for risk in risks):
        return "high"
    if any(risk.severity == "medium" for risk in risks):
        return "medium"
    return "low"


def _is_configuration_file(path: str, file_name: str) -> bool:
    if path.startswith(".github/workflows/"):
        return True
    if file_name in {"dockerfile", ".env", ".env.example"}:
        return True
    return file_name.endswith(CONFIG_FILE_SUFFIXES)


def _is_test_file(path: str) -> bool:
    return "/tests/" in path or "/test/" in path or path.startswith("tests/") or path.startswith("test_")


def _patch_adds_possible_secret(patch: Optional[str]) -> bool:
    if not patch:
        return False

    for line in patch.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        if _added_line_assigns_sensitive_key(line[1:]):
            return True
    return False


def _added_line_assigns_sensitive_key(line: str) -> bool:
    separator_positions = [position for position in (line.find("="), line.find(":")) if position >= 0]
    if not separator_positions:
        return False

    key_text = line[: min(separator_positions)].strip().strip("\"'`")
    normalized_key = key_text.lower()
    if not normalized_key:
        return False

    if normalized_key in SECRET_KEYWORDS:
        return True
    if "api_key" in normalized_key or "private_key" in normalized_key:
        return True

    segments = [segment for segment in normalized_key.replace("-", "_").split("_") if segment]
    return any(segment in {"secret", "token", "password"} for segment in segments)
