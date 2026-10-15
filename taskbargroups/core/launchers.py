"""จุดรวมสร้าง/ลบ launcher เปิดกลุ่ม ข้าม OS — ชื่อฟังก์ชันเดียวกับที่ใช้ใน GUI.

- Linux → `.desktop` (core.desktop)
- Windows → `.lnk` ใน Start Menu (core.win32, ผ่าน PowerShell ไม่ต้องลงอะไรเพิ่ม)
- macOS → `.command` (core.macos)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import desktop as _desktop
from . import macos as _macos
from . import win32 as _win32
from .models import Group
from .paths import app_dir
from .storage import ConfigStore


def launcher_file_name(dir_name: str) -> str:
    """ชื่อไฟล์ launcher ต่อกลุ่ม (ลงท้ายตาม OS)."""
    if sys.platform == "win32":
        return _win32.lnk_name(dir_name)
    if sys.platform == "darwin":
        return _macos.command_name(dir_name)
    return _desktop.desktop_file_name(dir_name)


# ชื่อเดิมฝั่ง Linux — GUI ใช้เป็น id อ้างอิง launcher (alias ไว้กันแก้หลายจุด)
desktop_file_name = launcher_file_name


def launcher_id(dir_name: str) -> str:
    name = launcher_file_name(dir_name)
    suffix = Path(name).suffix
    return name[: -len(suffix)] if suffix else name


def _open_target(python: str | None = None) -> tuple[str, str, str]:
    """คืน (exe, arguments, workdir) สำหรับเปิด flyout ของกลุ่ม (`--open DIR`)."""
    if getattr(sys, "frozen", False):
        return sys.executable, "", str(app_dir())
    if python:
        return python, "", str(app_dir())
    return sys.executable, "", str(app_dir())


def install_launcher(
    group: Group,
    store: ConfigStore,
    dir_name: str,
    target_dir: Path | str | None = None,
    python: str | None = None,
    icons_root: Path | str | None = None,
) -> Path:
    """สร้าง launcher เปิดกลุ่ม คืน path (signature เดิม — GUI ไม่ต้องแก้)."""
    if sys.platform == "win32":
        exe, _args, workdir = _open_target(python)
        directory = Path(target_dir) if target_dir is not None else _win32.start_menu_dir()
        icon = store.resolve_relative(dir_name, group.icon)
        icon_location = (
            str(icon)
            if icon is not None and icon.suffix.lower() == ".ico"
            else ""
        )
        return _win32.create_lnk(
            directory / _win32.lnk_name(dir_name),
            exe,
            arguments=f'--open "{dir_name}"',
            workdir=workdir,
            icon_location=icon_location,
        )
    if sys.platform == "darwin":
        exe, _args, _workdir = _open_target(python)
        directory = (
            Path(target_dir)
            if target_dir is not None
            else _macos.launchers_dir()
        )
        return _macos.install_command_launcher(exe, dir_name, directory)
    return _desktop.install_launcher(
        group, store, dir_name, target_dir, python, icons_root
    )


def remove_launcher(
    dir_name: str,
    target_dir: Path | str | None = None,
    icons_root: Path | str | None = None,
) -> bool:
    """ลบ launcher เปิดกลุ่ม คืน True ถ้าเคยมี."""
    if sys.platform == "win32":
        directory = (
            Path(target_dir) if target_dir is not None else _win32.start_menu_dir()
        )
        path = directory / _win32.lnk_name(dir_name)
        if not path.is_file():
            return False
        try:
            path.unlink()
        except OSError as exc:
            raise _win32.WindowsError(str(exc)) from exc
        return True
    if sys.platform == "darwin":
        directory = (
            Path(target_dir)
            if target_dir is not None
            else _macos.launchers_dir()
        )
        return _macos.remove_command_launcher(dir_name, directory)
    return _desktop.remove_launcher(dir_name, target_dir, icons_root)


def read_launcher_name(path: str | os.PathLike[str]) -> str | None:
    """อ่านชื่อแสดงของ launcher (ไว้โชว์/debug)."""
    suffix = Path(path).suffix.lower()
    if suffix == ".lnk" and sys.platform == "win32":
        target = _win32.read_lnk_target(path)
        return Path(target).stem if target else None
    return _desktop.read_desktop_name(path)
