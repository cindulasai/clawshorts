# ClawShorts Over-Limit Enforcement Verification

Use this when validating the important distinction:

- Shorts over daily limit should be blocked immediately.
- Regular YouTube video should stay allowed.

## Required live evidence

A reliable claim requires all three of these, not just a running daemon:

1. Database shows the device is over its daily limit.
2. Daemon log shows a portrait/focused Shorts element was detected and YouTube was force-stopped.
3. A later regular/landscape YouTube state is classified as regular video and does **not** trigger a force-stop.

## Database check

```bash
python3 - <<'PY'
import sqlite3, datetime, os
p = os.path.expanduser('~/.clawshorts/clawshorts.db')
conn = sqlite3.connect(p)
conn.row_factory = sqlite3.Row
today = datetime.date.today().isoformat()
for r in conn.execute('''
    SELECT d.name, u.ip, u.seconds, d.limit_val
    FROM daily_usage u LEFT JOIN devices d ON d.ip = u.ip
    WHERE u.date = ?
    ORDER BY u.ip
''', (today,)):
    print(f"{r['name'] or r['ip']} {r['ip']}: {r['seconds']:.1f}s / {r['limit_val']:.0f}s")
PY
```

## Log evidence pattern

Good over-limit Shorts block:

```text
focused 608x1080px (32%, ar=0.56)
Shorts: 310s / 300s used  (0s remaining)
Daily limit reached (300s). Stopping YouTube.
Force-stopped com.amazon.firetv.youtube
```

Good regular-video allow state:

```text
focused 1920x1080px (100%, ar=1.78)
```

or another landscape element such as `720x405px (38%, ar=1.78)`. These are landscape/regular states and must not be counted as Shorts.

## User-facing wording

If the evidence matches:

> The rule is working: Shorts over the limit blocks YouTube, while regular YouTube video remains allowed.

If the device is over limit but status says `Regular video` while the user insists Shorts is visible:

- do not claim reliability;
- gather raw ADB foreground activity, `uiautomator` XML, focused bounds, and logs;
- update the detector or test fixtures before publishing.

## Regression expectation

`tests/test_detection_formula.py` should include:

- positive portrait Shorts cases across multiple 16:9 resolutions;
- regular full-screen 16:9 negative cases;
- landscape preview/card negative cases;
- non-standard resolution cases.

Run:

```bash
PYTHONPATH=src python -m pytest -q tests/test_detection_formula.py
```