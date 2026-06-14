from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from actionrepro.analyze import analyze_paths
from actionrepro.cli import main
from actionrepro.report import to_json, to_markdown, to_pr_comment

FIXTURES = Path(__file__).parent / "fixtures"


def test_classifies_pytest_failure() -> None:
    analysis = analyze_paths([FIXTURES / "pytest_failure.log"])

    assert analysis.failures
    assert analysis.failures[0].category == "test_failure"
    assert analysis.failures[0].commands == ["python -m pytest -q"]
    assert "AssertionError" in "\n".join(analysis.failures[0].evidence)


def test_classifies_permission_gate_before_generic_error() -> None:
    analysis = analyze_paths([FIXTURES / "permission_gate.log"])

    assert analysis.failures[0].category == "permission_gate"
    assert "permission" in analysis.failures[0].advice.lower()


def test_classifies_network_429() -> None:
    analysis = analyze_paths([FIXTURES / "network_429.log"])

    categories = [failure.category for failure in analysis.failures]
    assert "network_external_service" in categories


def test_classifies_runner_memory_failure(tmp_path: Path) -> None:
    log = tmp_path / "oom.log"
    log.write_text(
        "test\tRun tests\t2026-06-14T00:00:00Z\t##[group]Run npm test\n"
        "test\tRun tests\t2026-06-14T00:00:01Z\tnpm test\n"
        "test\tRun tests\t2026-06-14T00:00:02Z\t"
        "FATAL ERROR: Reached heap limit Allocation failed - JavaScript heap out of memory\n"
        "test\tRun tests\t2026-06-14T00:00:03Z\t##[error]Process completed with exit code 137.\n",
        encoding="utf-8",
    )

    analysis = analyze_paths([log])

    assert analysis.failures[0].category == "runner_memory"
    assert "memory" in analysis.failures[0].advice.lower()


def test_reports_markdown_and_json() -> None:
    analysis = analyze_paths([FIXTURES / "pytest_failure.log"])

    markdown = to_markdown(analysis)
    payload = json.loads(to_json(analysis))

    assert "ActionRepro report" in markdown
    assert payload["failures"][0]["category"] == "test_failure"


def test_pr_comment_dry_run_text() -> None:
    analysis = analyze_paths([FIXTURES / "permission_gate.log"])

    comment = to_pr_comment(analysis)

    assert "permission_gate" in comment
    assert "maintainer" in comment.lower() or "external" in comment.lower()


def test_cli_plan_writes_markdown(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "report.md"

    result = runner.invoke(
        main,
        ["plan", str(FIXTURES / "pytest_failure.log"), "--out", str(out)],
    )

    assert result.exit_code == 0, result.output
    assert "ActionRepro report" in out.read_text(encoding="utf-8")


def test_cli_plan_writes_pr_comment(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "comment.md"

    result = runner.invoke(
        main,
        ["plan", str(FIXTURES / "permission_gate.log"), "--format", "comment", "--out", str(out)],
    )

    assert result.exit_code == 0, result.output
    text = out.read_text(encoding="utf-8")
    assert "first actionable signal" in text
    assert "permission_gate" in text


def test_cli_inspect() -> None:
    runner = CliRunner()

    result = runner.invoke(main, ["inspect", str(FIXTURES / "network_429.log")])

    assert result.exit_code == 0, result.output
    assert "ActionRepro findings" in result.output
