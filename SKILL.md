---
name: clawshorts
description: Use when asked to check, manage, configure, start, stop, or reset YouTube Shorts limiting on Fire TV devices from Hermes Agent. Supports ADB setup, status checks, daily quota tracking, daemon management, and reliable resolution-independent Shorts detection.
version: 1.3.2-hermes.2
author: cindulasai + Hermes Agent
license: MIT-0
metadata:
  hermes:
    tags: [fire-tv, adb, youtube, parental-controls, smart-home]
    related_skills: [hermes-agent]
---

# ClawShorts

## Overview

ClawShorts limits YouTube Shorts watch time on Fire TV devices. It connects over ADB, detects when YouTube Shorts is the foreground video surface, tracks daily usage per device in SQLite, and force-stops YouTube when the daily limit is reached.

This Hermes port is community-oriented: use private IPs only, avoid machine-specific assumptions, and rely on a resolution-independent detector rather than fixed pixel widths.

## When to Use

Use this skill when the user asks to:

- check Shorts quota or usage;
- add/connect a Fire TV;
- start, stop, install, or uninstall the Shorts limiter daemon;
- reset today’s Shorts counter;
- inspect logs or troubleshoot ADB/Fire TV detection;
- prepare the ClawShorts skill for reliable community sharing.

Do not use this for non-Fire-TV YouTube control, browser YouTube, or public-network device targeting.

## Primary Entry Point

```bash
~/.hermes/skills/smart-home/clawshorts/scripts/clawshorts.sh <command>
```

If installed, users can run the shorter launcher:

```bash
shorts <command>
```

The install command can create a user-local `shorts` launcher when possible. It does not require a global bin directory.

## Setup Flow

```bash
shorts setup <PRIVATE_TV_IP> <NAME>
shorts connect <PRIVATE_TV_IP>
shorts status <PRIVATE_TV_IP>
shorts install
```

Rules:

1. Validate that the target IP is private before device-control commands.
2. ADB Debugging must be enabled on the Fire TV.
3. The user must approve the on-TV “Allow ADB debugging?” prompt.
4. Only install/start the daemon after `adb devices -l` shows `<IP>:5555 device`.

## Commands

| Command | Purpose |
|---|---|
| `status [IP]` | Check usage, daemon health, foreground app, and Shorts/regular classification |
| `reset [IP]` | Reset today’s counter for all devices or one IP |
| `start` | Start daemon in foreground/manual mode |
| `stop` | Stop daemon |
| `history [days]` | Show usage history |
| `logs [N]` | Show last N daemon log lines |
| `list` | List configured devices |
| `setup <IP> [NAME]` | First-time setup for a device |
| `add <IP> [NAME]` | Add another Fire TV |
| `connect <IP>` | Connect ADB and auto-detect screen resolution |
| `enable <IP>` / `disable <IP>` | Enable or disable a device |
| `config [show|get|set|reset]` | View or adjust config |
| `detect <IP>` | Re-detect screen resolution |
| `install` | Install/start launchd or systemd user daemon |
| `uninstall` | Remove launchd/systemd user daemon |

## Resolution-independent Shorts detection

Detailed multi-TV detection and daemon reload notes live in [multi-TV detection](references/multi-tv-detection.md). Use them before changing thresholds or adding new TV profiles.

Never hard-code a width such as “608px means Shorts”. The detector uses geometry:

```text
expected_width_ratio = vertical_video_aspect / screen_aspect
```

For a 16:9 TV, a full-height 9:16 Shorts player is expected at:

```text
(9 / 16) / (16 / 9) = 0.3164 = 31.6% of screen width
```

This scales across 720p, 1080p, 1440p, 4K, and non-standard TV sizes because it uses the device’s live `wm size` values. A candidate element must also be tall and portrait-ish, so regular 16:9 videos, Fire TV settings rows, and menu panels are rejected.

The status parser and daemon both use the same shared detector in `src/clawshorts/detection.py`. Keep them aligned.

## Limit/Blocking Triage

When the user asks “how many minutes were played today,” query the SQLite database directly and report minutes/seconds per configured device before diagnosing reliability:

```bash
python3 - <<'PY'
import sqlite3, datetime, os
path=os.path.expanduser('~/.clawshorts/clawshorts.db')
conn=sqlite3.connect(path)
conn.row_factory=sqlite3.Row
today=datetime.date.today().isoformat()
for r in conn.execute('''
    SELECT d.name, u.ip, u.seconds, d.limit_val
    FROM daily_usage u LEFT JOIN devices d ON d.ip=u.ip
    WHERE u.date=? ORDER BY u.ip
''', (today,)):
    print(f"{r['name'] or r['ip']} {r['ip']}: {r['seconds']/60:.2f} min / {r['limit_val']/60:.2f} min")
PY
```

If a device is over limit but still playing, do not assume the daemon is dead. Check logs and live ADB UI state. A known gap is documented in [limit reached enforcement gap](references/limit-reached-enforcement-gap.md): the daemon may have force-stopped once, then later fail to stop again if current UI geometry is classified as fullscreen/regular video rather than Shorts.

For the strict over-limit behavior gate, see [over-limit enforcement verification](references/over-limit-enforcement-verification.md). The expected rule is: once today's Shorts counter is over the limit, newly detected Shorts should force-stop YouTube immediately, but regular landscape YouTube video should remain allowed.

## Reliability Gate Before Declaring Success

Do not claim a setup or port is done until all checks pass:

1. `adb devices -l` shows `<IP>:5555 device`, not `unauthorized` or `offline`.
2. `shorts status <IP>` reports the true foreground app from resumed activity only.
3. While the user is actively watching Shorts, status reports `Shorts`, not `Regular video`.
4. Daemon logs show the focused portrait video element and `Shorts: Ns / limit used`.
5. Usage increases after at least two polling intervals while Shorts remains foreground.
6. When the TV is in Settings/Home or regular YouTube landscape playback, usage does not increase.
7. Regression tests pass for multiple screen resolutions.

If the user says they are watching Shorts but status disagrees, gather raw ADB UI/window signals and debug the parser before making claims.

## Data Locations

- Database: `~/.clawshorts/clawshorts.db`
  - `config` — global defaults and legacy/tuning values
  - `devices` — device IP/name/limit/screen data
  - `daily_usage` — daily watch time by IP/date
- Daemon log: `~/.clawshorts/daemon.log`
- macOS LaunchAgent: `~/Library/LaunchAgents/com.fink.clawshorts.plist`
- Linux systemd user unit: `~/.config/systemd/user/clawshorts.service`

## Requirements

- `adb` / Android platform-tools
  - `adb` on PATH, or local fallback at `~/.local/bin/adb`
- Python 3
  - Hermes port prefers `~/.hermes/hermes-agent/venv/bin/python` when present because it includes dependencies such as `pydantic`.
- Fire TV on a trusted private network with ADB Debugging enabled.

## Security Notes

ADB gives strong device-control access. Only enable Fire TV ADB Debugging on trusted private networks. Do not target public IPs. If the TV shows `unauthorized`, have the user approve the ADB prompt on the TV; do not bypass it.

## Verification Commands

```bash
adb devices -l
shorts status <PRIVATE_TV_IP>
shorts logs 80
python -m py_compile src/clawshorts/detection.py src/clawshorts/device_monitor.py scripts/clawshorts-daemon.py
```

If `pytest` is available:

```bash
python -m pytest tests/test_detection_formula.py -q
```

Without `pytest`, run the test file’s functions via a small Python harness as part of packaging verification.

## Community Packaging Notes

Before publishing to Hermes Hub/community distribution:

- keep examples generic (`192.168.1.100`, `<PRIVATE_TV_IP>`), never a real user IP;
- keep the formula-based detector as the default;
- avoid global bin-directory assumptions;
- document ADB security clearly;
- include tests for common 16:9 sizes and non-standard resolutions;
- verify install/status/logs with real tool output;
- use the current hub submission targets and clean-package workflow in [community hub submission notes](references/community-hub-submission.md) before uploading or opening PRs.

Known submission targets:

- HermesHub: PR to `amanning3390/hermeshub`, adding `skills/clawshorts/`; `hermes skills publish <path> --to github --repo amanning3390/hermeshub` can automate this when GitHub auth is configured.
- OpenClaw/ClawHub: use the `clawhub` CLI (`clawhub skill publish <path> --slug clawshorts ...`). Hermes' `--to clawhub` path may only pre-scan and then defer to manual/ClawHub submission.


## Fire TV Guard Security Watchdog

A Hermes cron watchdog monitors guard logs and ADB state every 5 minutes and notifies the user only when suspicious activity appears. It watches for block events, daemon errors, repeated TV connection failures, ADB `offline`/`unauthorized` states, and accidental activation of broad generic blockers that should remain inactive.

Watchdog script:

```text
~/.hermes/scripts/fire_tv_guard_watchdog.py
```

Cron job:

```text
fire-tv-guard-security-watchdog
```
