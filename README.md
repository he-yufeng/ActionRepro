# ActionRepro

[中文 README](README_CN.md)

ActionRepro turns GitHub Actions failures into local repro plans and PR evidence packs.

It is not a local runner like `act`, and it is not a workflow linter like `actionlint`. It reads the
logs you already have, finds the first actionable failure, classifies it, extracts likely local
commands, and writes a short report you can use before replying to a maintainer.

```bash
pip install actionrepro
gh run view 123456789 --repo owner/repo --log > run.log
actionrepro plan run.log --out repro.md
```

## Why

When a PR check fails, the GitHub UI makes you scroll through a lot of setup noise before the useful
line appears. In open-source work, that wastes time and leads to weak replies like "CI failed for me
too". A better reply says whether the failure is a real regression, a permission gate, a network
limit, a dependency install issue, or a local test failure.

ActionRepro gives you that first pass quickly:

- failure category
- failed job and step
- evidence snippets
- likely local repro command
- PR comment draft

## Commands

Fetch a run log through `gh`:

```bash
actionrepro fetch owner/repo 123456789 --out run.log
```

Inspect failures:

```bash
actionrepro inspect run.log
```

Generate Markdown:

```bash
actionrepro plan run.log --out repro.md
```

Generate JSON:

```bash
actionrepro plan run.log --format json --out repro.json
```

Generate the same first-actionable finding as a paste-ready PR comment:

```bash
actionrepro plan run.log --format comment --out comment.md
```

Draft a PR comment without posting anything:

```bash
actionrepro comment run.log --pr 42 --dry-run
```

Posting is intentionally disabled in v0.1. The tool should not speak for you or claim a command was
run when it was not.

## What It Detects

ActionRepro has deterministic rules for common CI failure shapes:

- `permission_gate`: GitHub token, CLA, Vercel, secret, or integration permission failures
- `network_external_service`: 429s, failed downloads, or external API/network failures
- `runner_disk`: ENOSPC and disk pressure
- `runner_memory`: OOM, exit 137, or JS heap exhaustion
- `flaky_timeout`: timeout-shaped failures
- `dependency_install`: package resolution or install failures
- `lint_or_typecheck`: ruff, flake8, pylint, mypy, pyright, eslint, etc.
- `test_failure`: pytest/test/assertion failures
- `unknown_failure`: a real failure marker that needs manual reading

## Example Output

```md
# ActionRepro report

- Log files: 1
- Lines scanned: 37
- Commands detected: 2
- Failures detected: 1

## 1. test_failure

- Job: `test (ubuntu-latest)`
- Step: `Tests`
- Source: `run.log:27`
- Headline: `FAILED tests/test_parser.py::test_parse_windows_log`
- Advice: A test failed and should be reproduced locally.

### Local repro commands

- `python -m pytest -q`
```

## Boundaries

ActionRepro does not simulate GitHub runners. Use `act` when you need a local runner.

ActionRepro does not lint workflow YAML. Use `actionlint` for static workflow checks.

ActionRepro does not call an LLM, auto-fix code, or post PR comments. It creates a precise evidence
pack so you can make the right call.

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
ruff check .
python -m build
twine check dist/*
```
