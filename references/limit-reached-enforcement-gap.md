# Limit reached but YouTube still playing — enforcement-gap triage

Use this when a user says a Fire TV is still playing Shorts after the daily limit should have blocked it.

## Observed pattern

A device can exceed the configured daily limit and still appear to keep playing because the daemon only force-stops inside the current Shorts-detected branch:

1. YouTube is foreground.
2. Current UI dump is classified as Shorts.
3. `daily_usage.seconds >= devices.limit_val`.
4. `_force_stop_youtube()` runs.

If the quota is already over limit but the current UI hierarchy reports a fullscreen/landscape focused element (for example `1920x1080`, aspect `1.78`), the detector classifies the current screen as regular video/fullscreen UI, so the daemon does not enter the force-stop path even though the stored daily counter is already above the limit.

## Fast checks

```bash
# Today's usage in minutes
python3 - <<'PY'
import sqlite3, datetime, os
path=os.path.expanduser('~/.clawshorts/clawshorts.db')
conn=sqlite3.connect(path)
conn.row_factory=sqlite3.Row
today=datetime.date.today().isoformat()
for r in conn.execute('''
    SELECT d.name, u.ip, u.seconds, d.limit_val
    FROM daily_usage u LEFT JOIN devices d ON d.ip=u.ip
    WHERE u.date=?
    ORDER BY u.ip
''', (today,)):
    print(f"{r['name'] or r['ip']} {r['ip']}: {r['seconds']/60:.2f} min / {r['limit_val']/60:.2f} min")
PY

# Evidence of enforcement attempt
shorts logs 160 | grep -E 'Shorts:|Daily limit reached|Force-stopped|focused|player|fallback'

# Live ADB state for the suspect device
IP=<PRIVATE_TV_IP>
adb devices
adb -s "$IP:5555" shell "dumpsys activity activities | grep -m1 'mResumedActivity'"
adb -s "$IP:5555" shell "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp' | head"
adb -s "$IP:5555" shell 'uiautomator dump /sdcard/ui.xml'
adb -s "$IP:5555" pull /sdcard/ui.xml /tmp/clawshorts-ui.xml
```

## How to interpret

- If logs show `Shorts: Ns / limit used`, then `Daily limit reached`, then `Force-stopped ...`, the daemon did block at least once.
- If later logs show only full-width landscape focused elements such as `1920x1080 (100%, ar=1.78)`, the current detector is treating the screen as non-Shorts. Report that counter/enforcement worked once, then gather fresh UI evidence before making a reliability claim.
- If the stored daily usage is above the limit and YouTube is foreground, consider whether policy should force-stop YouTube whenever quota is exhausted, not only when the current frame is classified as Shorts. That is a product decision: stricter and more reliable, but it may also block normal YouTube after the Shorts quota is spent.

## Reporting to the user

Give the concrete counted minutes and the evidence timestamp. Example:

> tv2 has 5 min 10 sec counted today. The daemon hit the 5-minute limit and force-stopped YouTube at 11:18:57, but the current live UI is reporting fullscreen landscape geometry, so the Shorts detector is no longer classifying it as Shorts.
