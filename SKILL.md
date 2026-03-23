---
name: clawshorts
description: Block YouTube Shorts on Fire TV. Set your daily limit, get blocked when exceeded. Built for OpenClaw.
metadata:
  {
    "openclaw": { 
      "emoji": "📺", 
      "requires": { 
        "anyBins": ["adb"],
        "python3": true 
      } 
    },
  }
---

# 📺 ClawShorts — Block YouTube Shorts on Fire TV

Set a daily limit for YouTube Shorts on your Fire TV. When you hit it, YouTube closes automatically. Resets at midnight.

---

## Setup (5 minutes)

### 1. Find Your Fire TV IP
**Settings → My Fire TV → About → Network** → note the IP (e.g. `192.168.1.100`)

### 2. Enable ADB Debugging
**Settings → My Fire TV → Developer Options** → turn ON **ADB Debugging**

> ⚠️ **Security:** ADB gives full control over your Fire TV. Only use on a **trusted home network**.

### 3. Install
```bash
shorts setup 192.168.1.100
shorts install
```

That's it — the daemon auto-starts and begins enforcing your limit.

---

## Set Your Daily Limit

Default is **300 seconds (5 minutes)** per day.

```bash
shorts install 600   # 10 minutes/day
shorts install 1800  # 30 minutes/day
```

---

## Commands

| Command | What it does |
|---------|-------------|
| `shorts status` | Check today's usage right now |
| `shorts reset` | Reset today's counter to 0 |
| `shorts stop` | Pause the limiter |
| `shorts start` | Resume the limiter |
| `shorts uninstall` | Remove completely |
| `shorts history` | Show watch history (last 30 days) |
| `shorts logs` | Show debug logs (last 50 lines) |
| `shorts setup <IP> [NAME]` | First-time setup |
| `shorts add <IP> [NAME]` | Add another device |
| `shorts list` | List all devices |
| `shorts connect <IP>` | Connect via ADB |
| `shorts enable <IP>` | Enable a device |
| `shorts disable <IP>` | Disable a device |

---

## How Detection Works

ClawShorts watches what you're watching via ADB — every 3 seconds:

- **Shorts playing** → ~45% screen width, portrait → **counts**
- **Regular video** → ~100% screen width → **doesn't count**
- **YouTube home / browse** → no video active → **doesn't count**
- **Other apps / Fire TV home** → **doesn't count**

Only actual Shorts playback counts toward your daily limit.

---

## Troubleshooting

**Daemon not running:**
```bash
shorts start
```

**Check live status:**
```bash
shorts status
```

**View debug log:**
```bash
tail ~/.clawshorts/daemon.log
```

**ADB not found — install it:**
```bash
brew install android-platform-tools  # Mac
sudo apt install adb                # Linux
```

---

## Multiple Fire TVs?

Add more IPs separated by commas:
```bash
shorts setup 192.168.1.100,192.168.1.101
shorts install
```

---

## What Gets Installed

**Runtime files** (in your home folder):
- `~/.clawshorts/clawshorts.db` — watch history
- `~/.clawshorts/daemon.log` — debug log
- `~/Library/LaunchAgents/com.fink.clawshorts.plist` — auto-start (Mac)
