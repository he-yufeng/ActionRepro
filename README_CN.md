# ActionRepro：把 CI 失败日志变成本地复现计划

CI 红了，最浪费时间的不是修 bug，而是在几千行 GitHub Actions 日志里找第一条真正有用的失败信号。

ActionRepro 做的事很窄：读取 CI 日志，判断失败类型，抽取本地复现命令，生成一份可以给 maintainer 看的证据包。

它不是 `act`。它不模拟 GitHub runner。

它也不是 `actionlint`。它不做 workflow 静态检查。

它处理的是已经发生的失败日志：这次失败到底像代码回归、权限 gate、网络 429、依赖安装问题、runner 磁盘不足，还是普通测试失败？

## 一分钟使用

```bash
pip install actionrepro
gh run view 123456789 --repo owner/repo --log > run.log
actionrepro plan run.log --out repro.md
```

生成的 `repro.md` 会列出：

- 失败分类
- 失败 job / step
- 关键日志片段
- 可能的本地复现命令
- 可以人工整理后发到 PR 里的回复草稿

## 适合什么场景

### 开源 PR 的 CI 善后

你提了 PR，CI 红了。ActionRepro 可以先判断是不是你改坏的，还是 GitHub token、CLA、Vercel、Hugging Face 429、runner disk 这类外部 gate。

这样回复 maintainer 时就不会只说“CI failed”，而是能说明失败归因和下一步。

### 多矩阵测试排查

Python 3.10 failed，但 3.11/3.12 全绿。Node lint failed，但 tests 全绿。ActionRepro 会把 job、step 和失败分类拆出来，避免你在完整日志里来回跳。

### 给 PR body 补证据

很多 PR 被 review 卡住，不是因为代码一定不对，而是 maintainer 没法快速判断：问题是否真实、修复是否验证过、失败是不是外部环境。ActionRepro 生成的 evidence pack 可以作为 PR body 或 follow-up comment 的素材。

## 核心命令

拉取 GitHub Actions 日志：

```bash
actionrepro fetch owner/repo 123456789 --out run.log
```

快速看失败表：

```bash
actionrepro inspect run.log
```

生成 Markdown 报告：

```bash
actionrepro plan run.log --out repro.md
```

生成 JSON：

```bash
actionrepro plan run.log --format json --out repro.json
```

直接生成可粘贴到 PR 里的回复草稿：

```bash
actionrepro plan run.log --format comment --out comment.md
```

只生成 PR 回复草稿，不自动发布：

```bash
actionrepro comment run.log --pr 42 --dry-run
```

v0.1 明确不自动发评论。原因很简单：工具不应该替你宣称“我验证过”，也不应该在你没确认的情况下往上游 PR 里写东西。

## 它能识别哪些失败

- `permission_gate`：GitHub token、CLA、Vercel、secret、workflow 权限问题
- `network_external_service`：429、下载失败、外部服务不可达
- `runner_disk`：runner 磁盘不足
- `runner_memory`：OOM、exit 137、JavaScript heap out of memory
- `flaky_timeout`：超时或疑似 flaky
- `dependency_install`：pip/npm/pnpm/yarn 依赖安装失败
- `lint_or_typecheck`：ruff、flake8、pylint、mypy、pyright、eslint 等
- `test_failure`：pytest / test / assertion 失败
- `unknown_failure`：有失败信号，但需要人工继续读

## 和已有工具的区别

`act` 负责本地跑 GitHub Actions。ActionRepro 不重复造 runner，只告诉你当前日志里最值得本地复现的是哪一步。

`actionlint` 检查 workflow YAML。ActionRepro 不检查 YAML，它处理实际跑出来的日志。

`reviewdog` 把检查结果贴到 PR。ActionRepro 是提交者手里的本地证据包工具，不自动代表你发言。

## 设计边界

ActionRepro 的第一版只做确定性日志分析，不调用 LLM，不自动修代码，不自动发评论。

如果一个工具一上来就试图“自动修所有 CI”，很容易变成黑盒。ActionRepro 的定位更克制：先帮你把失败读清楚，再由你决定下一步。

## 开发

```bash
python -m pip install -e ".[dev]"
pytest -q
ruff check .
python -m build
twine check dist/*
```
