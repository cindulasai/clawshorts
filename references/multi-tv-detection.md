# Multi-TV formula and daemon reload notes

Use when extending or troubleshooting ClawShorts across more than one Fire TV or different screen sizes.

## Screen-size invariant

Do not key Shorts detection on a fixed pixel width such as `606px` or `608px`.

Use geometry:

```text
expected_width_ratio = vertical_video_aspect / screen_aspect
```

For full-height 9:16 Shorts on a 16:9 TV:

```text
(9 / 16) / (16 / 9) = 0.3164
```

So the expected player width is about 31.6% of the current logical screen width, whether the display reports 720p, 1080p, 1440p, or 4K.

## Practical detector gates

A candidate should pass all of these:

- focused video element preferred over root UI node;
- portrait-ish aspect ratio;
- enough height coverage to be a player, not a menu row;
- width ratio near formula-derived expected ratio;
- regular landscape video rejected.

## Multi-device daemon pitfall

If a new TV is added while the daemon is already running, `shorts status <ip>` may detect Shorts correctly while the daemon still counts only the devices loaded at startup.

Fix pattern:

```bash
shorts add <name> <ip>
shorts detect <ip>
shorts restart
shorts status <ip>
shorts logs 20
```

Quality gate: after restart logs should show the daemon started with the expected device count and usage should increment for the newly added TV while Shorts is foreground.

## Regression tests worth keeping

- 1280x720, 1920x1080, 2560x1440, 3840x2160;
- non-standard 16:9-ish sizes like 1366x768 and 1024x576;
- regular YouTube landscape video;
- Fire TV Home/Settings rows;
- focused single-line YouTube XML where root node is full screen but focused child is the actual Shorts player.
