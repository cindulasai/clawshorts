# Hermes Port Notes

These notes capture Hermes-specific changes for the community ClawShorts port.

## Paths

- Skill path: `~/.hermes/skills/smart-home/clawshorts/`
- Primary wrapper: `~/.hermes/skills/smart-home/clawshorts/scripts/clawshorts.sh`
- Convenience launcher link: `~/.local/bin/shorts`
- State/database/logs: `~/.clawshorts/`

## Runtime choices

- Prefer `~/.hermes/hermes-agent/venv/bin/python` when present so the CLI/daemon can use existing dependencies such as `pydantic`.
- Initialize the SQLite schema before read-only commands (`list`, `status`) to avoid first-run database errors.
- Use a user-local launcher instead of global paths.
- Launchd/systemd services must use stable Python/ADB paths because service managers do not inherit interactive shell PATH.

## Setup sequence

```bash
shorts setup <PRIVATE_TV_IP> <NAME>
shorts connect <PRIVATE_TV_IP>
shorts status <PRIVATE_TV_IP>
shorts install
```

Install/start the daemon only after ADB is authorized and status can inspect the TV.
