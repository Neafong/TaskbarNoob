"""ปักหมุด launcher ของกลุ่มลง Cinnamon panel (best-effort).

รองรับ 2 ทาง:
1. Grouped Window List applet (Mint รุ่นใหม่) — แก้ไฟล์ config JSON ของ applet
   (คีย์ `pinned-apps`) ที่ `~/.config/cinnamon/spices/grouped-window-list@cinnamon.org/<instance>.json`
   (Cinnamon เก่าใช้ `~/.cinnamon/configs/...`) แล้วสั่ง `org.Cinnamon.ReloadXlet` ผ่าน DBus
   ให้ applet โหลดใหม่ทันที
2. `org.cinnamon panel-launchers` ผ่าน gsettings (Cinnamon รุ่นเก่า — deprecated)

ทำแบบ "พยายาม" — ถ้าทำไม่ได้ให้โยน `PinError` แล้ว GUI ค่อยบอกให้ลากเอง
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable, Sequence

from .hotkeys import is_cinnamon

CINNAMON_SCHEMA = "org.cinnamon"
LAUNCHERS_KEY = "panel-launchers"
GROUPED_WINDOW_APPLET = "grouped-window-list@cinnamon.org"

CINNAMON_BUS = "org.Cinnamon"
CINNAMON_PATH = "/org/Cinnamon"
CINNAMON_INTERFACE = "org.Cinnamon"

Runner = Callable[[Sequence[str]], str]


class PinError(Exception):
    """โยนเมื่อปักหมุดลง panel ไม่สำเร็จ."""


def _run(command: Sequence[str]) -> str:
    result = subprocess.run(list(command), capture_output=True, text=True)
    if result.returncode != 0:
        raise PinError(result.stderr.strip() or f"คำสั่งล้มเหลว: {' '.join(command)}")
    return result.stdout


def _parse_string_array(raw: str) -> list[str]:
    text = raw.strip()
    if text.startswith("@as"):
        text = text[3:].strip()
    if not text or text == "[]":
        return []
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError) as exc:
        raise PinError(f"อ่าน {LAUNCHERS_KEY} ไม่ได้: {raw!r}") from exc
    if not isinstance(value, (list, tuple)):
        raise PinError(f"{LAUNCHERS_KEY} ไม่ใช่ list: {raw!r}")
    return [str(item) for item in value]


def _format_string_array(values: Sequence[str]) -> str:
    return "[" + ", ".join(f"'{value}'" for value in values) + "]"


def read_panel_launchers(runner: Runner = _run) -> list[str]:
    return _parse_string_array(runner(["gsettings", "get", CINNAMON_SCHEMA, LAUNCHERS_KEY]))


def add_panel_launcher(desktop_id: str, runner: Runner = _run) -> None:
    current = read_panel_launchers(runner)
    current = [value for value in current if value.upper() != "DEPRECATED"]
    if desktop_id in current:
        return
    runner(
        ["gsettings", "set", CINNAMON_SCHEMA, LAUNCHERS_KEY, _format_string_array([*current, desktop_id])]
    )


def grouped_window_config_dirs() -> list[Path]:
    """โฟลเดอร์ config ของ Grouped Window List (ใหม่ก่อน แล้วค่อย path เก่า)."""
    home = Path.home()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or (home / ".config"))
    return [
        config_home / "cinnamon" / "spices" / GROUPED_WINDOW_APPLET,
        home / ".cinnamon" / "configs" / GROUPED_WINDOW_APPLET,
    ]


def grouped_window_config_dir() -> Path:
    for directory in grouped_window_config_dirs():
        if directory.is_dir():
            return directory
    return grouped_window_config_dirs()[0]


def _grouped_window_config_files(config_dir: Path | None = None) -> Iterable[Path]:
    directories = [Path(config_dir)] if config_dir is not None else grouped_window_config_dirs()
    for directory in directories:
        if not directory.is_dir():
            continue
        yield from sorted(directory.glob("*.json"))


def add_grouped_window_pin(desktop_id: str, config_dir: Path | None = None) -> bool:
    """เพิ่ม desktop id เข้า `pinned-apps` ของ applet. คืน True ถ้าเจอ config ให้แก้."""
    found = False
    for path in _grouped_window_config_files(config_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "pinned-apps" not in data:
            continue
        entry = data["pinned-apps"]
        values = entry.get("value") if isinstance(entry, dict) else entry
        if not isinstance(values, list):
            continue
        found = True
        if desktop_id in values:
            continue
        values.append(desktop_id)
        try:
            path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        except OSError:
            continue
    return found


def grouped_window_pinned_ids(config_dir: Path | None = None) -> set[str]:
    """คืน desktop id ทั้งหมดที่ปักหมุดไว้ใน Grouped Window List."""
    ids: set[str] = set()
    for path in _grouped_window_config_files(config_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict):
            continue
        entry = data.get("pinned-apps")
        values = entry.get("value") if isinstance(entry, dict) else entry
        if isinstance(values, list):
            ids.update(str(value) for value in values)
    return ids


def remove_grouped_window_pin(desktop_id: str, config_dir: Path | None = None) -> bool:
    """ถอด desktop id ออกจาก `pinned-apps` ของ applet. คืน True ถ้าลบได้."""
    removed = False
    for path in _grouped_window_config_files(config_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(data, dict) or "pinned-apps" not in data:
            continue
        entry = data["pinned-apps"]
        values = entry.get("value") if isinstance(entry, dict) else entry
        if not isinstance(values, list) or desktop_id not in values:
            continue
        remaining = [value for value in values if value != desktop_id]
        if isinstance(entry, dict):
            entry["value"] = remaining
        else:
            data["pinned-apps"] = remaining
        try:
            path.write_text(json.dumps(data, indent=4), encoding="utf-8")
        except OSError:
            continue
        removed = True
    return removed


def remove_panel_launcher(desktop_id: str, runner: Runner = _run) -> None:
    current = read_panel_launchers(runner)
    remaining = [value for value in current if value != desktop_id]
    if remaining != current:
        runner(
            [
                "gsettings",
                "set",
                CINNAMON_SCHEMA,
                LAUNCHERS_KEY,
                _format_string_array(remaining),
            ]
        )


def pinned_desktop_ids(
    config_dir: Path | None = None, runner: Runner = _run
) -> set[str]:
    """desktop id ทั้งหมดที่ปักหมุดอยู่ (รวมทั้ง 2 วิธี)."""
    ids = grouped_window_pinned_ids(config_dir)
    if is_cinnamon():
        try:
            ids.update(read_panel_launchers(runner))
        except PinError:
            pass
    return ids


def is_pinned(
    desktop_id: str, config_dir: Path | None = None, runner: Runner = _run
) -> bool:
    return desktop_id in pinned_desktop_ids(config_dir, runner)


def reload_grouped_window_applet() -> bool:
    """สั่ง Cinnamon โหลด Grouped Window List ใหม่ผ่าน DBus ให้ไอคอนที่ pin โผล่ทันที."""
    if shutil.which("gdbus") is None:
        return False
    command = [
        "gdbus",
        "call",
        "--session",
        "--dest",
        CINNAMON_BUS,
        "--object-path",
        CINNAMON_PATH,
        "--method",
        f"{CINNAMON_INTERFACE}.ReloadXlet",
        GROUPED_WINDOW_APPLET,
        "APPLET",
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError:
        return False
    return result.returncode == 0


def pin_to_panel(
    desktop_id: str,
    runner: Runner = _run,
    config_dir: Path | None = None,
    refresh: bool = True,
) -> str:
    """ปักหมุด launcher (desktop id) ลง panel. คืนชื่อวิธีที่ใช้สำเร็จ."""
    if not is_cinnamon():
        raise PinError("เดสก์ท็อปไม่ใช่ Cinnamon")
    if os.environ.get("TASKBARGROUPS_NO_PIN"):
        raise PinError("ปิดการปักหมุดอัตโนมัติ (TASKBARGROUPS_NO_PIN)")
    if add_grouped_window_pin(desktop_id, config_dir):
        if refresh:
            reload_grouped_window_applet()
        return "grouped-window-list"
    add_panel_launcher(desktop_id, runner)
    return "panel-launchers"


def unpin_from_panel(
    desktop_id: str,
    runner: Runner = _run,
    config_dir: Path | None = None,
    refresh: bool = True,
) -> bool:
    """ถอด launcher (desktop id) ออกจาก panel. คืน True ถ้าถอดได้."""
    if not is_cinnamon():
        raise PinError("เดสก์ท็อปไม่ใช่ Cinnamon")
    if os.environ.get("TASKBARGROUPS_NO_PIN"):
        raise PinError("ปิดการปักหมุดอัตโนมัติ (TASKBARGROUPS_NO_PIN)")
    removed = remove_grouped_window_pin(desktop_id, config_dir)
    try:
        remove_panel_launcher(desktop_id, runner)
        removed = True
    except PinError:
        pass
    if refresh and removed:
        reload_grouped_window_applet()
    return removed
