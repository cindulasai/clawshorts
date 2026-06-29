# ClawShorts Troubleshooting

## ADB connection states

Check:

```bash
adb connect <PRIVATE_TV_IP>:5555
adb devices -l
```

Expected:

```text
<PRIVATE_TV_IP>:5555 device
```

Problem states:

- `unauthorized`: approve the ADB debugging prompt on the TV.
- `offline`: toggle Fire TV ADB Debugging off/on, then reconnect.
- no device: verify same private network, Fire TV IP, and ADB Debugging.

## Status says regular video while Shorts is open

Do not guess. Gather evidence:

```bash
shorts status <PRIVATE_TV_IP>
adb -s <PRIVATE_TV_IP>:5555 shell "dumpsys activity activities | grep -m3 -E 'mResumedActivity|ResumedActivity|topResumedActivity'"
adb -s <PRIVATE_TV_IP>:5555 shell "wm size; wm density"
adb -s <PRIVATE_TV_IP>:5555 shell "uiautomator dump /sdcard/ui.xml >/dev/null && cat /sdcard/ui.xml" > /tmp/clawshorts-ui.xml
```

The parser should select the focused portrait player, not the full-screen root node. A 9:16 full-height Shorts player on a 16:9 TV should be around 31.6% of screen width, independent of whether the TV is 720p, 1080p, or 4K.

## Status says YouTube while TV is in Settings/Home

Foreground app detection must use resumed activity only. Check:

```bash
adb -s <PRIVATE_TV_IP>:5555 shell "dumpsys activity activities | grep -m3 -E 'mResumedActivity|ResumedActivity|topResumedActivity'"
```

If the resumed activity is not a YouTube package, usage must not increase.

## Daemon active but usage does not increase

Check:

```bash
shorts logs 80
shorts status <PRIVATE_TV_IP>
```

Usage increases only after two successful polling intervals while Shorts remains foreground. If the TV disconnects or changes foreground app, counting pauses.

## macOS launchd cannot find adb

Launchd does not inherit the interactive shell PATH. The Hermes port falls back to `~/.local/bin/adb` when `adb` is not on PATH. If needed, install Android platform-tools there or put `adb` on a system-visible PATH.

## First run database errors

If you see `unable to open database file` or `no such table: devices`, run any CLI command through `clawshorts.sh`; the wrapper initializes `~/.clawshorts` and the SQLite schema before read-only commands.
