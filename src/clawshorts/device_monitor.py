"""Device monitoring helpers — extracted from cmd_status."""
from __future__ import annotations

import logging
import re
import shutil
import subprocess
import time
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .constants import DEFAULT_SCREEN_HEIGHT, DEFAULT_SCREEN_WIDTH
from .detection import is_shorts_element, parse_element_from_ui_dump

__all__ = ["DaemonHealth", "ScreenInfo", "check_daemon", "poll_screen"]

log = logging.getLogger(__name__)
ADB_BIN = shutil.which("adb") or str(Path.home() / ".local" / "bin" / "adb") or "adb"


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class DaemonHealth:
    healthy: bool
    status: str
    detail: str


@dataclass
class ScreenInfo:
    app: str
    detail: str


# ---------------------------------------------------------------------------
# Daemon health check
# ---------------------------------------------------------------------------

def check_daemon(ip: str) -> DaemonHealth:
    """Check if the daemon is running and doing UI polls.

    Returns (healthy, status, detail).
    """
    try:
        result = subprocess.run(
            ["pgrep", "-f", "clawshorts-daemon.py"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        pids = [p for p in result.stdout.strip().split("\n") if p]
        if not pids:
            return DaemonHealth(False, "🔴 Daemon not running", "Run 'shorts start' to start")
    except subprocess.TimeoutExpired:
        return DaemonHealth(False, "🔴 Process check timed out", "Check ADB connectivity")
    except FileNotFoundError:
        log.warning("pgrep not available")
        return DaemonHealth(False, "🔴 pgrep not found", "Install procps")
    except OSError as e:
        log.warning("Process check failed: %s", e)
        return DaemonHealth(False, "🔴 Process check failed", str(e)[:50])

    # Check log for recent activity
    log_file = Path.home() / ".clawshorts" / "daemon.log"
    if log_file.exists():
        try:
            content = log_file.read_text(errors="replace")
            today = time.strftime("%Y-%m-%d")
            lines = content.strip().split("\n")
            recent = [
                l for l in lines
                if l.startswith(f"[{today}]") or "HEARTBEAT" in l or "DEBUG" in l
            ]
            if recent:
                debug_lines = [l for l in recent if "DEBUG" in l or "Shorts:" in l]
                if debug_lines:
                    last_debug = debug_lines[-1]
                    ts_match = re.search(
                        r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", last_debug
                    )
                    detail = last_debug.split("INFO")[-1].split("DEBUG")[-1].strip()[:50]
                    return DaemonHealth(True, "🟢 Daemon active", f"Polling: {detail}")
                return DaemonHealth(True, "🟢 Daemon active", "UI polling confirmed")
        except OSError as e:
            log.warning("Log read failed: %s", e)

    return DaemonHealth(True, "🟡 Daemon running", "No recent UI polls (may be idle)")


# ---------------------------------------------------------------------------
# Screen resolution detection
# ---------------------------------------------------------------------------

def _get_screen_size(ip: str) -> tuple[int, int]:
    """Query actual screen size from device via adb, cached for one hour."""
    cache_file = Path.home() / ".clawshorts" / f"screen_{ip.replace('.', '_')}.txt"
    now = time.time()
    if cache_file.exists():
        try:
            content = cache_file.read_text().strip()
            age = now - cache_file.stat().st_mtime
            if age < 3600 and "x" in content:
                w, h = content.split("x", 1)
                return int(w), int(h)
        except (ValueError, OSError):
            pass
    device_id = f"{ip}:5555"
    try:
        out = subprocess.run(
            [ADB_BIN, "-s", device_id, "shell", "wm", "size"],
            capture_output=True, text=True, timeout=6,
        )
        matches = re.findall(r"(\d+)x(\d+)", out.stdout)
        if matches:
            width, height = map(int, matches[-1])
            cache_file.write_text(f"{width}x{height}")
            return width, height
    except (subprocess.TimeoutExpired, OSError):
        pass
    return DEFAULT_SCREEN_WIDTH, DEFAULT_SCREEN_HEIGHT


def _get_screen_width(ip: str) -> int:
    """Backward-compatible wrapper for older callers."""
    return _get_screen_size(ip)[0]


# ---------------------------------------------------------------------------
# Live screen poll
# ---------------------------------------------------------------------------

def poll_screen(ip: str) -> ScreenInfo:
    """Poll the device's current app and focused element.

    Returns (app_name, focused_info).
    """
    device_id = f"{ip}:5555"

    # Check foreground app
    try:
        result = subprocess.run(
            [ADB_BIN, "-s", device_id, "shell", "dumpsys", "activity", "activities"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        resumed_lines = "\n".join(
            line for line in result.stdout.splitlines()
            if "mResumedActivity" in line or "ResumedActivity" in line or "topResumedActivity" in line
        )
        youtube_active = any(
            pkg in resumed_lines
            for pkg in [
                "com.amazon.firetv.youtube",
                "com.google.android.youtube.tv",
                "com.amazon.youtube.tv",
                "com.google.android.youtube",
                "com.youtube.tv",
            ]
        )
        app = "YouTube" if youtube_active else "Other/Home"
    except subprocess.TimeoutExpired:
        return ScreenInfo("Error", "ADB command timed out")
    except FileNotFoundError:
        return ScreenInfo("Error", "ADB not installed")
    except OSError as e:
        return ScreenInfo("Error", f"ADB error: {e}"[:50])

    # Get focused element via UI dump
    try:
        subprocess.run(
            [ADB_BIN, "-s", device_id, "shell", "uiautomator", "dump", "/sdcard/ui.xml"],
            capture_output=True,
            timeout=15,
        )
        with tempfile.NamedTemporaryFile(prefix="clawshorts-ui-", suffix=".xml", delete=True) as tmp:
            pull_result = subprocess.run(
                [ADB_BIN, "-s", device_id, "pull", "/sdcard/ui.xml", tmp.name],
                capture_output=True,
                timeout=10,
            )
            if pull_result.returncode == 0:
                xml_content = Path(tmp.name).read_text(errors="replace")
                elem = parse_element_from_ui_dump(xml_content)
                if elem and elem.width:
                    screen_w, screen_h = _get_screen_size(ip)
                    w = elem.width
                    pct = w / screen_w * 100
                    is_shorts = is_shorts_element(w, elem.height, screen_w, screen_h)
                    status = "Shorts" if is_shorts else "Regular video"
                    return ScreenInfo(app, f"Focused: {w}px ({pct:.0f}%) - {status}")
                return ScreenInfo(app, "Focused: unknown")
        return ScreenInfo(app, "UI dump/pull failed")
    except subprocess.TimeoutExpired:
        return ScreenInfo(app, "UI dump timed out")
    except OSError as e:
        return ScreenInfo(app, f"UI dump error: {e}"[:50])
