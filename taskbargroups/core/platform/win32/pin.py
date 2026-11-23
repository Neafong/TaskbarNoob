"""Windows taskbar pin inspection, Explorer reveal, and pinned shortcut repointing."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .aumid import APP_ID, aumid
from .lnk import (
    Runner,
    WindowsError,
    _appdata,
    _home,
    _run_lenient,
    lnk_name,
    notify_icon_changed,
    read_lnk_aumid,
)


def taskbar_pinned_dir(
    env: dict | None = None, home: Path | str | None = None
) -> Path:
    """โฟลเดอร์ User Pinned ของ taskbar."""
    return (
        _appdata(env, home)
        / "Microsoft"
        / "Internet Explorer"
        / "Quick Launch"
        / "User Pinned"
        / "TaskBar"
    )


def pinned_lnk_path(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
) -> Path:
    return taskbar_pinned_dir(env, home) / lnk_name(dir_name)


def pinned_aumid_files(
    env: dict | None = None, home: Path | None = None
) -> dict[str, str]:
    """สแกน User Pinned ครั้งเดียว → {aumid: ชื่อไฟล์} (เฉพาะที่เป็นของเรา)."""
    try:
        directory = taskbar_pinned_dir(env, home)
    except OSError:
        return {}
    found: dict[str, str] = {}
    try:
        for path in directory.glob("*.lnk"):
            if not path.is_file():
                continue
            value = read_lnk_aumid(path) or ""
            if value.startswith(f"{APP_ID}.group."):
                found[value] = path.name
    except OSError:
        return {}
    return found


def is_pinned(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
) -> bool:
    return pinned_lnk_path(dir_name, env, home).is_file()


def stale_pin_label(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
    pinned: dict[str, str] | None = None,
) -> bool:
    """True เมื่อปุ่มบน taskbar ยังโชว์ชื่อเก่าหลังผู้ใช้เปลี่ยนชื่อกลุ่ม."""
    if sys.platform != "win32":
        return False
    try:
        files = pinned if pinned is not None else pinned_aumid_files(env, home)
    except OSError:
        return False
    filename = files.get(aumid(dir_name))
    if filename is None:
        return False
    return filename != lnk_name(dir_name)


def repoint_pinned(old_dir_name: str, new_lnk: Path) -> bool:
    """หลังเปลี่ยนชื่อกลุ่ม — ให้ `.lnk` ที่ปักอยู่บน taskbar ชี้กลุ่มใหม่."""
    old_value = aumid(old_dir_name)
    directory = taskbar_pinned_dir()
    try:
        candidates = list(directory.glob("*.lnk"))
    except OSError:
        return False
    for path in candidates:
        if not path.is_file():
            continue
        try:
            if (read_lnk_aumid(path) or "") != old_value:
                continue
            shutil.copy2(new_lnk, path)
            notify_icon_changed(path)
            return True
        except OSError:
            continue
    return False


def repoint_desktop_copies(old_dir_name: str, new_lnk: Path) -> int:
    """อัปเดต `.lnk` ที่ผู้ใช้ลากไปวางบน Desktop ให้ใช้ `.lnk` ใหม่ (มีไอคอนใหม่)."""
    old_value = aumid(old_dir_name)
    desktop = _home() / "Desktop"
    try:
        candidates = list(desktop.glob("*.lnk"))
    except OSError:
        return 0
    updated = 0
    for path in candidates:
        if not path.is_file():
            continue
        try:
            if (read_lnk_aumid(path) or "") != old_value:
                continue
            shutil.copy2(new_lnk, path)
            notify_icon_changed(path)
            updated += 1
        except OSError:
            continue
    return updated


def _reveal_fire_and_forget(command: str) -> str:
    """เปิด Explorer แบบไม่รอ — ไม่จับ stdout/stderr เพื่อไม่ให้ค้าง."""
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    return ""


def reveal_in_explorer(
    path: str | os.PathLike[str],
    runner: Runner | None = None,
) -> None:
    """เปิด Explorer โดยเลือกไฟล์ไว้ (ให้ผู้ใช้ลากไปวางบน taskbar ได้เลย)."""
    target = os.path.normpath(str(path))
    try:
        (runner or _reveal_fire_and_forget)(f'explorer /select,"{target}"')
    except OSError as exc:
        raise WindowsError(str(exc)) from exc


def pin_to_taskbar(
    source_lnk: str | os.PathLike[str],
    env: dict | None = None,
    home: Path | str | None = None,
    runner: Runner = _run_lenient,
) -> Path:
    """Windows 11 ปิดการปัก taskbar จากโปรแกรม — เปิด Explorer ให้ผู้ใช้ลากวางเอง."""
    source = Path(source_lnk)
    reveal_in_explorer(source, runner=runner)
    return source


def unpin_from_taskbar(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
) -> bool:
    name = str(dir_name)
    if name.lower().endswith(".lnk"):
        dest = taskbar_pinned_dir(env, home) / Path(name).name
    else:
        dest = pinned_lnk_path(name, env, home)
    if not dest.is_file():
        return False
    try:
        dest.unlink()
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    return True
