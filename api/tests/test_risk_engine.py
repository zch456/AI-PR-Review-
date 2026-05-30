from app.github_client import GitHubPullRequestFile
from app.risk_engine import assess_pull_request_risks, calculate_overall_risk
from typing import Optional


def make_file(
    path: str,
    *,
    status: str = "modified",
    additions: int = 1,
    deletions: int = 0,
    changes: int = 1,
    patch: Optional[str] = "@@ -1 +1 @@\n-old\n+new",
) -> GitHubPullRequestFile:
    return GitHubPullRequestFile(
        path=path,
        status=status,
        additions=additions,
        deletions=deletions,
        changes=changes,
        patch=patch,
    )


def risk_types(files: list[GitHubPullRequestFile]) -> set[str]:
    return {risk.risk_type for risk in assess_pull_request_risks(files)}


def test_flags_dependency_and_configuration_changes() -> None:
    risks = assess_pull_request_risks(
        [
            make_file("web/package.json", additions=8, deletions=2, changes=10),
            make_file(".github/workflows/ci.yml", additions=4, deletions=1, changes=5),
        ]
    )

    assert [risk.risk_type for risk in risks] == ["dependency_change", "configuration_change"]
    assert risks[0].severity == "medium"
    assert risks[0].file_path == "web/package.json"
    assert "依赖" in risks[0].title


def test_flags_security_sensitive_files_as_high_risk() -> None:
    risks = assess_pull_request_risks([make_file("api/app/auth/middleware.py")])

    assert risks[0].risk_type == "security_sensitive_file"
    assert risks[0].severity == "high"
    assert risks[0].confidence == "medium"
    assert "鉴权" in risks[0].reason


def test_flags_test_deletions() -> None:
    risks = assess_pull_request_risks(
        [make_file("api/tests/test_login.py", additions=1, deletions=18, changes=19)]
    )

    assert risks[0].risk_type == "test_deletion"
    assert risks[0].severity == "medium"
    assert "测试" in risks[0].suggestion


def test_flags_large_changes() -> None:
    risks = assess_pull_request_risks([make_file("web/package-lock.json", additions=600, changes=600)])

    assert "large_change" in risk_types([make_file("web/package-lock.json", additions=600, changes=600)])
    assert any(risk.severity == "medium" for risk in risks)


def test_flags_possible_secret_in_added_patch_lines() -> None:
    risks = assess_pull_request_risks(
        [
            make_file(
                "api/app/settings.py",
                patch='@@ -1 +1,2 @@\n+API_KEY = "sk-demo"\n+DEBUG = True',
            )
        ]
    )

    assert risks[0].risk_type == "possible_secret"
    assert risks[0].severity == "high"
    assert risks[0].confidence == "medium"
    assert "敏感" in risks[0].title


def test_does_not_flag_dependency_names_that_only_contain_secret_keywords() -> None:
    risks = assess_pull_request_risks(
        [
            make_file(
                "web/package-lock.json",
                additions=20,
                changes=20,
                patch='@@ -1 +1,4 @@\n+    "css-tokenizer": {\n+      "version": "1.0.0"\n+    }',
            )
        ]
    )

    assert "possible_secret" not in {risk.risk_type for risk in risks}


def test_calculates_overall_risk_from_signals() -> None:
    assert calculate_overall_risk([]) == "low"

    medium_risks = assess_pull_request_risks([make_file("requirements.txt")])
    assert calculate_overall_risk(medium_risks) == "medium"

    high_risks = assess_pull_request_risks([make_file("api/app/auth/session.py")])
    assert calculate_overall_risk(high_risks) == "high"
