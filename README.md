# ClawShorts

> A Fire TV YouTube Shorts limiter. Watches your TV over ADB, detects when Shorts is the foreground video surface, counts daily watch time, and force-stops YouTube when the daily limit is reached.

[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](pyproject.toml)
[![Platform: Fire TV / ADB](https://img.shields.io/badge/platform-Fire%20TV%20%2F%20ADB-orange.svg)](#requirements)

ClawShorts is the Shorts-only counterpart to the [TubeGuard](../tubeguard) family — Shorts are the most addictive surface on YouTube, so this is a focused, lighter tool that does one thing well.

The Hermes version is designed for community use: generic example IPs, no fixed TV pixel widths, and a user-local launcher by default.

## Requirements

- macOS or Linux computer running Hermes Agent
- Python 3 with `pydantic` available; the Hermes install prefers `~/.hermes/hermes-agent/venv/bin/python` when present
- Android platform-tools / `adb`
  - macOS Homebrew: `brew install android-platform-tools`
  - Linux: install `adb` / `android-tools-adb` from your package manager
  - Local user install is also fine if `adb` is available at `~/.local/bin/adb`
- Fire TV on the same trusted private network
- Fire TV ADB Debugging enabled and this computer authorized on the TV prompt

Security note: only enable ADB on a trusted private network. ADB is powerful device control; do not expose it on public WiFi.

## Install / setup

From this skill directory:

```bash
./scripts/clawshorts.sh setup 192.168.1.100 living-room
./scripts/clawshorts.sh connect 192.168.1.100
./scripts/clawshorts.sh status 192.168.1.100
./scripts/clawshorts.sh install
```

`install` creates a user-local convenience launcher at `~/.local/bin/shorts` when possible. Add `~/.local/bin` to your PATH if your shell does not already include it.

After that, use:

```bash
shorts status
shorts reset 192.168.1.100
shorts logs 50
shorts stop
shorts start
```

## Detection model

ClawShorts does not hard-code a pixel width like “608px means Shorts”. It uses a resolution-independent formula:

```text
expected_width_ratio = vertical_video_aspect / screen_aspect
```

For a 16:9 TV, a full-height 9:16 Shorts player is expected at:

```text
(9 / 16) / (16 / 9) = 0.3164 = 31.6% of screen width
```

Because this uses the TV's live `wm size`, the same detector works across 720p, 1080p, 1440p, 4K, and non-standard TV sizes. The candidate element must also be tall and portrait-ish, which rejects regular 16:9 videos, Fire TV settings rows, and menu panels.

## Commands

| Command | Purpose |
|---|---|
| `setup <IP> [NAME]` | Add first device and initialize config |
| `add <IP> [NAME]` | Add another Fire TV |
| `connect <IP>` | Connect ADB and auto-detect screen resolution |
| `status [IP]` | Show daemon health, foreground app, Shorts/regular classification, usage |
| `reset [IP]` | Reset today's usage counter |
| `history [days]` | Show recent daily usage |
| `logs [N]` | Show daemon logs |
| `list` | List configured devices |
| `config` | Show detection/runtime config |
| `detect <IP>` | Re-detect a device screen size |
| `install` | Install/start launchd or systemd user daemon |
| `stop` / `start` | Stop/start the daemon manually |
| `uninstall` | Remove launchd/systemd service |

## Quality gate before claiming success

A working install must pass all of these:

1. `adb devices -l` shows `<IP>:5555 device`, not `unauthorized` or `offline`.
2. `shorts status <IP>` reports the true foreground app from resumed activity.
3. While Shorts is foreground, status says `Shorts`, not `Regular video`.
4. Daemon logs show the focused portrait video element and `Shorts: Ns / limit used`.
5. Usage increases after at least two polling intervals while Shorts stays foreground.
6. When the TV is in Settings/Home or a regular landscape YouTube video, Shorts usage does not increase.

## Troubleshooting quick checks

```bash
adb connect <IP>:5555
adb devices -l
shorts status <IP>
shorts logs 80
```

If the device is `unauthorized`, accept the ADB debugging prompt on the TV. If it is `offline`, toggle Fire TV ADB Debugging off/on and reconnect.

## License

MIT-0 — see [LICENSE](LICENSE).
