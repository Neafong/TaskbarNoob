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


def pinned_aumid_files(
    env: dict | None = None, home: Path | None = None
) -> dict[str, str]:
    """สแกน User Pinned ครั้งเดียว → {aumid: ชื่อไฟล์} (เฉพาะที่เป็นของเรา).

    Windows เป็นคนเขียนไฟล์พวกนี้ตอนผู้ใช้ลากวาง และ**เปลี่ยนชื่อให้เองได้**
    (เช่นชนกับ `.lnk` ของแอปอื่น → `Game.lnk` กลายเป็น `Game (2).lnk`)
    จึงระบุตัวตนจาก AUMID อย่างเดียว อย่าเชื่อชื่อไฟล์
    """
    try:
        directory = _win32.taskbar_pinned_dir(env, home)
    except OSError:
        return {}
    found: dict[str, str] = {}
    try:
        for path in directory.glob("*.lnk"):
            if not path.is_file():
                continue
            value = _win32.read_lnk_aumid(path) or ""
            if value.startswith(f"{_win32.APP_ID}.group."):
                found[value] = path.name
    except OSError:
        return {}
    return found


def _win_pinned_aumids() -> set[str]:
    """AUMID ของ `.lnk` ใน User Pinned ที่เป็นของเรา."""
    return set(pinned_aumid_files())


def pinned_desktop_ids(
    config_dir: Path | None = None, runner: Runner = _run
) -> set[str]:
    """id launcher ทั้งหมดที่ปักอยู่ (ชื่อไฟล์ .desktop/.lnk/.command)."""
    if sys.platform == "win32":
        pinned = set(pinned_aumid_files())
        if not pinned:
            return set()
        from .storage import ConfigStore

        try:
            names = ConfigStore(config_dir).list_groups()
        except OSError:
            return set()
        return {
            _win32.lnk_name(name) for name in names if _win32.aumid(name) in pinned
        }
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
    for directory in (_win32.shortcuts_dir(),):
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
            _win32.pin_to_taskbar(source, runner=runner)
        except _win32.WindowsError as exc:
            raise PinError(str(exc)) from exc
        return "taskbar-manual"
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


def stale_pin_label(
    dir_name: str,
    env: dict | None = None,
    home: Path | None = None,
    pinned: dict[str, str] | None = None,
) -> bool:
    """True เมื่อปุ่มบน taskbar ยังโชว์ชื่อเก่าหลังผู้ใช้เปลี่ยนชื่อกลุ่ม

    Windows เอา**ชื่อไฟล์** ไปเป็นป้ายบน taskbarตอนผู้ใช้ลากวาง
    และ**ลบไฟล์ทิ้งทันที** ถ้าเรา rename ให้ → ป้ายจึงแก้ไม่ได้
    (เนื้อในไฟล์แก้ได้ เรา repoint ให้อยู่แล้ว → กดแล้วเปิดกลุ่มถูกต้อง)
    ทางแก้คือถอนแล้วลากวางใหม่

    ส่ง `pinned` (ผลจาก `pinned_aumid_files`) มาได้เพื่อเลี่ยงสแกนซ้ำต่อกลุ่ม
    """
    if sys.platform != "win32":
        return False
    try:
        files = pinned if pinned is not None else pinned_aumid_files(env, home)
    except OSError:
        return False
    filename = files.get(_win32.aumid(dir_name))
    if filename is None:
        return False
    return filename != _win32.lnk_name(dir_name)


def available_actions() -> Sequence[str]:
    """วิธีปักที่ใช้ได้บน OS นี้ (ไว้โชว์ใน UI)."""
    if sys.platform == "win32":
        return ("taskbar-manual",)
    if sys.platform == "darwin":
        return ("dock-pinned",)
    return ("grouped-window-list", "panel-launchers")
