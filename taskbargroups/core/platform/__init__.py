"""จุดรวม Platform Backend ข้าม OS (`linux` / `win32`).

เรียก `get_backend()` เพื่อให้ได้ `PlatformBackend` ที่ตรงกับ `sys.platform`
(หรือใช้ฟังก์ชันระดับโมดูลที่เป็น facade ตรงไปยัง backend ปัจจุบัน)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, Sequence

from ..models import Group
from ..storage import ConfigStore
from .base import PlatformBackend
from .linux.hotkeys import HotkeyError, is_cinnamon
from .linux.panel import PinError


def get_backend(platform: str | None = None) -> PlatformBackend:
    """คืน PlatformBackend ตาม OS (รับ `platform` override ได้ในเทสต์)."""
    target = platform or sys.platform
    if target == "win32":
        from .win32.backend import Win32Backend

        return Win32Backend()
    from .linux.backend import LinuxCinnamonBackend

    return LinuxCinnamonBackend()


# --- Facade functions (ส่งต่อให้ backend ของ OS ปัจจุบัน) ---


def launcher_file_name(dir_name: str) -> str:
    return get_backend().launcher_file_name(dir_name)


desktop_file_name = launcher_file_name


def launcher_id(dir_name: str) -> str:
    return get_backend().launcher_id(dir_name)


def install_launcher(
    group: Group,
    store: ConfigStore,
    dir_name: str,
    target_dir: Path | str | None = None,
    python: str | None = None,
    icons_root: Path | str | None = None,
    default_icon: Path | str | None = None,
) -> Path:
    return get_backend().install_launcher(
        group, store, dir_name, target_dir, python, icons_root, default_icon
    )


def remove_launcher(
    dir_name: str,
    target_dir: Path | str | None = None,
    icons_root: Path | str | None = None,
) -> bool:
    return get_backend().remove_launcher(dir_name, target_dir, icons_root)


def read_launcher_name(path: str | os.PathLike[str]) -> str | None:
    return get_backend().read_launcher_name(path)


def pinned_desktop_ids(
    config_dir: Path | None = None, runner: Callable | None = None
) -> set[str]:
    return get_backend().pinned_desktop_ids(config_dir, runner)


def is_pinned(
    desktop_id: str,
    config_dir: Path | None = None,
    runner: Callable | None = None,
) -> bool:
    return get_backend().is_pinned(desktop_id, config_dir, runner)


def pin_to_panel(
    desktop_id: str,
    runner: Callable | None = None,
    config_dir: Path | None = None,
    refresh: bool = True,
) -> str:
    return get_backend().pin_to_panel(desktop_id, runner, config_dir, refresh)


def unpin_from_panel(
    desktop_id: str,
    runner: Callable | None = None,
    config_dir: Path | None = None,
    refresh: bool = True,
) -> bool:
    return get_backend().unpin_from_panel(desktop_id, runner, config_dir, refresh)


def stale_pin_label(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
    pinned: dict[str, str] | None = None,
) -> bool:
    return get_backend().stale_pin_label(dir_name, env, home, pinned)


def available_actions() -> Sequence[str]:
    return get_backend().available_actions()


__all__ = [
    "HotkeyError",
    "PinError",
    "PlatformBackend",
    "available_actions",
    "desktop_file_name",
    "get_backend",
    "install_launcher",
    "is_cinnamon",
    "is_pinned",
    "launcher_file_name",
    "launcher_id",
    "pin_to_panel",
    "pinned_desktop_ids",
    "read_launcher_name",
    "remove_launcher",
    "stale_pin_label",
    "unpin_from_panel",
]
