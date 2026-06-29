# ClawShorts Community Hub Submission Notes

Use this when preparing ClawShorts for HermesHub or OpenClaw/ClawHub publishing.

## HermesHub / Hermes Hub

Current submission target:

- Site: <https://hermeshub.xyz>
- Repository: `amanning3390/hermeshub`
- Submit by opening a PR that adds the skill directory under `skills/clawshorts/`.
- Hermes CLI publish path, when GitHub auth is configured:

```bash
hermes skills publish /path/to/clawshorts --to github --repo amanning3390/hermeshub
```

Authentication requires either `GITHUB_TOKEN` in the Hermes env or `gh auth login`.

HermesHub submission guide requirements observed during review:

- Skill directory contains `SKILL.md` plus optional `scripts/`, `references/`, and `assets/`.
- Keep `SKILL.md` under roughly 500 lines; move detail into references.
- Required structure in `SKILL.md`: clear frontmatter, When to Use, Procedure, Pitfalls, Verification.
- PR triggers automated security scanning; critical findings block merge.
- Document environment variables, network access, filesystem access, and destructive/persistent operations.

## OpenClaw / ClawHub

Current submission target:

- Site: <https://clawhub.ai>
- Docs: <https://docs.openclaw.ai/clawhub>
- CLI package: `clawhub`

Publish flow:

```bash
npm i -g clawhub
clawhub login
clawhub skill publish /path/to/clawshorts --slug clawshorts --name "ClawShorts" --version 1.3.2-hermes.2
```

Do not rely on Hermes' built-in `--to clawhub` path for upload yet. In the checked version, it performs the local skills guard scan, then reports that ClawHub publishing is not supported and points to manual submission.

## Safe package regeneration pattern

Before publishing, regenerate a clean staging directory and ZIP from the live skill directory while excluding local/cache artifacts:

- `__pycache__/`
- `.pytest_cache/`
- `*.pyc`
- `*.pyo`
- `.coverage`
- `_meta.json`
- `.DS_Store`

Example exclusions are important because an older prepared ZIP contained pytest/cache/coverage artifacts.

Expected top-level package contents include:

```text
SKILL.md
README.md
LICENSE
SECURITY_AUDIT.md
SPEC.md
TROUBLESHOOTING.md
pyproject.toml
skill-card.md
scripts/
references/
src/
tests/
```

## Required pre-submit verification

Run a Python compile check and the detector regression tests using the Hermes venv when available, because system Python may not have `pydantic`:

```bash
PY=~/.hermes/hermes-agent/venv/bin/python
[ -x "$PY" ] || PY=python3

"$PY" -m py_compile \
  src/clawshorts/detection.py \
  src/clawshorts/device_monitor.py \
  scripts/clawshorts-daemon.py \
  scripts/clawshorts_db.py

PYTHONPATH=src "$PY" -m pytest tests/test_detection_formula.py -q
```

If pytest is unavailable, import the test file and run each `test_*` function with a small Python harness.

Also run the Hermes publish pre-scan on the clean staging directory:

```bash
hermes skills publish /path/to/clean-staging --to clawhub
```

A SAFE verdict with medium findings for subprocess, launchd/systemd persistence, or daemon stop/restart behavior is expected for this skill class. Explain these in the submission/security notes rather than treating them as automatic blockers, because ClawShorts intentionally controls ADB, a local daemon, and YouTube force-stop behavior.
