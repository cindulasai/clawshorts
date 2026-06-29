"""Shared Shorts detection logic.

Both device_monitor.py (for `shorts status`) and clawshorts-daemon.py
use this module for identical Shorts detection.
"""
from __future__ import annotations

import re
from typing import NamedTuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Shorts are portrait video surfaces. On a 16:9 TV, a full-height 9:16
# portrait player occupies (9/16) / (16/9) = 31.64% of screen width.
# The detector uses that geometry as the center of a tolerance band, so it
# scales across 720p/1080p/4K and unusual TV sizes without pixel constants.
SHORTS_VIDEO_ASPECT = 9 / 16          # width / height for vertical video
SHORTS_MIN_HEIGHT_RATIO = 0.55        # must fill most of the TV height
SHORTS_EXPECTED_WIDTH_TOLERANCE = 0.45  # +/-45% around geometric expectation
SHORTS_ABSOLUTE_MIN_WIDTH_RATIO = 0.18
SHORTS_ABSOLUTE_MAX_WIDTH_RATIO = 0.55

# Max width/height ratio for Shorts (allows 9:16 and near-square overlays,
# excludes landscape 16:9 previews/settings rows). Kept loose for vendor UI.
SHORTS_MAX_ASPECT_RATIO = 1.0


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class ElementInfo(NamedTuple):
    """Parsed UI element information."""
    app: str
    width: int | None
    height: int | None
    detail: str


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def is_shorts_element(
    width: int | None,
    height: int | None,
    screen_width: int,
    screen_height: int | None = None,
    *,
    max_aspect_ratio: float = SHORTS_MAX_ASPECT_RATIO,
    min_height_ratio: float = SHORTS_MIN_HEIGHT_RATIO,
    tolerance: float = SHORTS_EXPECTED_WIDTH_TOLERANCE,
) -> bool:
    """Return True when element geometry matches a YouTube Shorts player.

    Resolution-independent formula:

        expected_width_ratio = vertical_video_aspect / screen_aspect

    For any 16:9 TV size (1280x720, 1920x1080, 3840x2160), a full-height
    9:16 vertical video is expected at ~31.6% screen width. The same formula
    also adapts to different screen aspect ratios because it uses the live
    `wm size` dimensions rather than hard-coded pixels.

    A candidate must:
    - be tall enough to represent the player, not a menu row;
    - be portrait-ish by width/height aspect ratio;
    - have width near the geometric expected ratio, with a tolerance band for
      YouTube/Fire TV UI padding and vendor differences.
    """
    if width is None or height is None or width <= 0 or height <= 0:
        return False
    if not screen_width or screen_width <= 0:
        return False

    width_ratio = width / screen_width
    aspect = width / height

    if aspect > max_aspect_ratio:
        return False

    if screen_height and screen_height > 0:
        height_ratio = height / screen_height
        if height_ratio < min_height_ratio:
            return False
        screen_aspect = screen_width / screen_height
        expected_width_ratio = SHORTS_VIDEO_ASPECT / screen_aspect
        lower = max(SHORTS_ABSOLUTE_MIN_WIDTH_RATIO, expected_width_ratio * (1 - tolerance))
        upper = min(SHORTS_ABSOLUTE_MAX_WIDTH_RATIO, expected_width_ratio * (1 + tolerance))
        return lower <= width_ratio <= upper

    # Legacy fallback for callers that only know screen width. This still uses
    # ratios, not pixels, but is intentionally conservative.
    return SHORTS_ABSOLUTE_MIN_WIDTH_RATIO <= width_ratio <= SHORTS_ABSOLUTE_MAX_WIDTH_RATIO


def parse_element_from_ui_dump(ui_text: str) -> ElementInfo | None:
    """Parse the video-like element from a Fire TV UI dump.

    Fire TV YouTube / Cobalt often emits the XML hierarchy as a single line.
    The old parser returned the first node with bounds, which is usually the
    root full-screen FrameLayout (1920x1080). That made Shorts look like a
    regular full-width video in `shorts status` even when the daemon's focused
    element logic would detect Shorts correctly.

    Selection order mirrors the daemon:
    1. Focused element (primary Fire TV YouTube signal)
    2. Named player/surface/video element
    3. Largest centered tall element fallback
    """
    if not ui_text or "node" not in ui_text.lower():
        return None

    def _element_from_node(node_text: str) -> ElementInfo | None:
        bounds_m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node_text)
        if not bounds_m:
            return None
        left, top, right, bottom = (int(bounds_m.group(i)) for i in range(1, 5))
        width = right - left
        height = bottom - top
        package_m = re.search(r'package="([^"]+)"', node_text)
        text_m = re.search(r'text="([^"]*)"', node_text)
        content_m = re.search(r'content-desc="([^"]*)"', node_text)
        app = package_m.group(1) if package_m else "unknown"
        detail = (text_m.group(1) if text_m else "") or (content_m.group(1) if content_m else "")
        return ElementInfo(app=app, width=width, height=height, detail=detail)

    # XML is usually one line; extract each <node ...> tag explicitly.
    nodes = re.findall(r'<node\b[^>]*>', ui_text)

    # Primary: focused node. Ignore tiny focus sentinels.
    for node in nodes:
        if 'focused="true"' not in node:
            continue
        elem = _element_from_node(node)
        if elem and elem.width and elem.width >= 100:
            return elem

    # Secondary: named player / surface / video nodes.
    for node in nodes:
        if not re.search(r'resource-id="[^"]*(?:player|surface|video)[^"]*"', node, re.I):
            continue
        elem = _element_from_node(node)
        if elem and elem.width and elem.width >= 100:
            return elem

    # Fallback: largest centered element that fills substantial screen height.
    # Infer screen size from root max bounds in the dump.
    all_bounds = []
    for node in nodes:
        m = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
        if m:
            x1, y1, x2, y2 = (int(m.group(i)) for i in range(1, 5))
            all_bounds.append((node, x1, y1, x2, y2))
    if all_bounds:
        screen_w = max(x2 for _, _, _, x2, _ in all_bounds)
        screen_h = max(y2 for _, _, _, _, y2 in all_bounds)
        best = None
        best_w = 0
        for node, x1, y1, x2, y2 in all_bounds:
            w, h = x2 - x1, y2 - y1
            if h > screen_h * 0.4 and x1 > 0 and x2 < screen_w and w > best_w:
                best = node
                best_w = w
        if best:
            return _element_from_node(best)

    return None
