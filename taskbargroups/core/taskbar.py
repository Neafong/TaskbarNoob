"""จุดรวมปัก/ถอน launcher ของกลุ่ม ข้าม OS — ชื่อฟังก์ชันเดียวกับที่ใช้ใน GUI.

- Linux (Cinnamon) → core.panel (Grouped Window List / panel-launchers)
- Windows → คัดลอก .lnk เข้าโฟลเดอร์ User Pinned (best-effort)
- macOS → เขียน com.apple.dock persistent-apps (best-effort)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Sequence

from . import macos as _macos
from . import win32 as _win32
from .panel import PinError, Runner, _run
from .panel import is_cinnamon


def pinned_desktop_ids(
    config_dir: Path | None = None, runner: Runner = _run
) -> set[str]:
    """id launcher ทั้งหมดที่ปักอยู่ (ชื่อไฟล์ .desktop/.lnk/.command)."""
    if sys.platform == "win32":
        directory = _win32.taskbar_pinned_dir()
        try:
            return {
                path.name
                for path in directory.glob(f"{_win32.APP_ID}-*.lnk")
                if path.is_file()
            }
        except OSError:
            return set()
    if sys.platform == "darwin":
        ids: set[str] = set()
        try:
            from urllib.request import url2pathname

            for url in _macos.dock_app_paths():
                name = Path(url2pathname(url.replace("file://", ""))).name
                if name.startswith(f"{_macos.APP_ID}-"):
                    ids.add(name)
        except (OSError, ValueError):
            pass
        return ids
    from .panel import pinned_desktop_ids as _linux_ids

    return _linux_ids(config_dir, runner)


def is_pinned(
    desktop_id: str, config_dir: Path | None = None, runner: Runner = _run
) -> bool:
    return desktop_id in pinned_desktop_ids(config_dir, runner)


def _find_source_lnk(desktop_id: str) -> Path | None:
    for directory in (_win32.start_menu_dir(),):
        candidate = directory / desktop_id
        if candidate.is_file():
            return candidate
    return None


def pin_to_panel(
    desktop_id: str,
    runner: Runner = _run,
    config_dir: Path | None = None,
    refresh: bool = True,
) -> str:
    """ปัก launcher ลง taskbar/dock/panel. คืนชื่อวิธีที่ใช้สำเร็จ."""
    if sys.platform == "win32":
        source = _find_source_lnk(desktop_id)
        if source is None:
            raise PinError(f"หาไฟล์ {desktop_id} ใน Start Menu ไม่เจอ (ติดตั้ง launcher ก่อน)")
        try:
            _win32.pin_to_taskbar(source)
        except _win32.WindowsError as exc:
            raise PinError(str(exc)) from exc
        return "taskbar-pinned"
    if sys.platform == "darwin":
        try:
            path = _macos.launchers_dir() / desktop_id
            _macos.pin_to_dock(path)
        except _macos.MacOSError as exc:
            raise PinError(str(exc)) from exc
        return "dock-pinned"
    if not is_cinnamon():
        raise PinError("เดสก์ท็อปไม่ใช่ Cinnamon")
    if os.environ.get("TASKBARGROUPS_NO_PIN"):
        raise PinError("ปิดการปักหมุดอัตโนมัติ (TASKBARGROUPS_NO_PIN)")
    from .panel import pin_to_panel as _linux_pin

    return _linux_pin(desktop_id, runner, config_dir, refresh)


def unpin_from_panel(
    desktop_id: str,
    runner: Runner = _run,
    config_dir: Path | None = None,
    refresh: bool = True,
) -> bool:
    """ถอด launcher ออกจาก taskbar/dock/panel. คืน True ถ้าถอดได้."""
    if sys.platform == "win32":
        try:
            return _win32.unpin_from_taskbar(desktop_id)
        except _win32.WindowsError as exc:
            raise PinError(str(exc)) from exc
    if sys.platform == "darwin":
        try:
            return _macos.unpin_from_dock(_macos.launchers_dir() / desktop_id)
        except _macos.MacOSError as exc:
            raise PinError(str(exc)) from exc
    if not is_cinnamon():
        raise PinError("เดสก์ท็อปไม่ใช่ Cinnamon")
    if os.environ.get("TASKBARGROUPS_NO_PIN"):
        raise PinError("ปิดการปักหมุดอัตโนมัติ (TASKBARGROUPS_NO_PIN)")
    from .panel import unpin_from_panel as _linux_unpin

    return _linux_unpin(desktop_id, runner, config_dir, refresh)


def available_actions() -> Sequence[str]:
    """วิธีปักที่ใช้ได้บน OS นี้ (ไว้โชว์ใน UI)."""
    if sys.platform == "win32":
        return ("taskbar-pinned",)
    if sys.platform == "darwin":
        return ("dock-pinned",)
    return ("grouped-window-list", "panel-launchers")
