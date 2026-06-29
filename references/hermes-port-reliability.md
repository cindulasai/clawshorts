# ClawShorts Reliability Notes

## Root causes fixed during Hermes port

1. UI XML parsing selected the first root node instead of the focused video node.
   - Fire TV YouTube/Cobalt often dumps XML as one long line.
   - The parser now extracts every `<node ...>` tag and prioritizes `focused="true"` video-like nodes.

2. Fixed pixel or fixed threshold assumptions are not reliable for community users.
   - Detection now uses `expected_width_ratio = vertical_video_aspect / screen_aspect`.
   - This scales across TV resolutions and aspect ratios.

3. Foreground app detection must use resumed activity only.
   - Checking the full activity dump can find stale YouTube activities in history and misreport Settings/Home as YouTube.

4. Services need stable executable paths.
   - macOS launchd and Linux systemd may not inherit the interactive shell PATH.
   - The port falls back to `~/.local/bin/adb` and uses a stable Python path.

## Quality gate

Before telling a user the limiter is working, verify:

- ADB state is `device`, not `unauthorized` or `offline`.
- The foreground activity is YouTube when counting.
- Status reports `Shorts` while Shorts is visibly foreground.
- Usage increases after multiple polling intervals.
- Usage stops increasing when the TV leaves Shorts.
- Regression tests pass for multiple screen sizes.
