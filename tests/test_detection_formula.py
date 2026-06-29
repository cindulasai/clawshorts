from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clawshorts.detection import is_shorts_element, parse_element_from_ui_dump


def test_vertical_shorts_scales_across_common_16x9_resolutions() -> None:
    # A full-height 9:16 video occupies 31.64% of any 16:9 screen width.
    for screen_w, screen_h in [(1280, 720), (1920, 1080), (2560, 1440), (3840, 2160)]:
        player_h = screen_h
        player_w = round(player_h * 9 / 16)
        assert is_shorts_element(player_w, player_h, screen_w, screen_h), (screen_w, screen_h, player_w)


def test_vertical_shorts_scales_across_nonstandard_tv_resolutions() -> None:
    for screen_w, screen_h in [(1366, 768), (1024, 576), (1600, 900), (3440, 1440)]:
        player_h = screen_h
        player_w = round(player_h * 9 / 16)
        assert is_shorts_element(player_w, player_h, screen_w, screen_h), (screen_w, screen_h, player_w)


def test_regular_landscape_video_is_not_shorts() -> None:
    for screen_w, screen_h in [(1280, 720), (1920, 1080), (3840, 2160)]:
        assert not is_shorts_element(screen_w, screen_h, screen_w, screen_h)
        landscape_w = round(screen_w * 0.8)
        landscape_h = round(landscape_w / (16 / 9))
        assert not is_shorts_element(landscape_w, landscape_h, screen_w, screen_h)


def test_menu_rows_and_settings_panels_are_not_shorts() -> None:
    assert not is_shorts_element(600, 128, 1920, 1080)  # Fire TV settings row shape
    assert not is_shorts_element(600, 300, 1920, 1080)
    assert not is_shorts_element(440, 100, 1920, 1080)


def test_single_line_fire_tv_xml_selects_focused_player_not_root() -> None:
    # Fire TV YouTube/Cobalt often dumps XML as one long line. The parser must
    # select the focused portrait player, not the first full-screen root node.
    xml = (
        "<?xml version='1.0' encoding='UTF-8' standalone='yes' ?>"
        '<hierarchy rotation="0">'
        '<node class="android.widget.FrameLayout" package="com.amazon.firetv.youtube" '
        'focused="false" bounds="[0,0][1920,1080]">'
        '<node class="android.view.View" package="com.amazon.firetv.youtube" '
        'focused="true" bounds="[656,0][1264,1080]" />'
        "</node></hierarchy>"
    )
    elem = parse_element_from_ui_dump(xml)
    assert elem is not None
    assert elem.width == 608
    assert elem.height == 1080
    assert is_shorts_element(elem.width, elem.height, 1920, 1080)
