"""Interface กลางสำหรับ Platform Backend (Linux Cinnamon / Windows 11).

แยก logic เฉพาะ OS ออกจาก `gui/` และ `core/` ส่วนกลาง ให้เรียกผ่าน `get_backend()`
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Sequence

from ..models import Group
from ..storage import ConfigStore


class PlatformBackend(ABC):
    """สัญญาเมธอดที่ backend ของแต่ละ OS ต้องรองรับ."""

    name: str = ""
    supports_direct_pin: bool = False
    supports_cinnamon_hotkeys: bool = False
    supports_win_hotkeys: bool = False

    # --- Process / Window Identity ---

    def set_app_process_id(self) -> None:
        """ตั้ง process identity ของหน้าต่างหลัก (เช่น AUMID บน Windows)."""

    def set_group_process_id(self, dir_name: str) -> None:
        """ตั้ง process identity ของหน้าต่าง flyout ต่อกลุ่ม."""

    # --- Launcher (.desktop / .lnk) ---

    @abstractmethod
    def launcher_file_name(self, dir_name: str) -> str:
        """ชื่อไฟล์ launcher ต่อกลุ่ม (เช่น `taskbargroups-game.desktop` หรือ `Game.lnk`)."""

    def launcher_id(self, dir_name: str) -> str:
        name = self.launcher_file_name(dir_name)
        suffix = Path(name).suffix
        return name[: -len(suffix)] if suffix else name

    @abstractmethod
    def install_launcher(
        self,
        group: Group,
        store: ConfigStore,
        dir_name: str,
        target_dir: Path | str | None = None,
        python: str | None = None,
        icons_root: Path | str | None = None,
        default_icon: Path | str | None = None,
    ) -> Path:
        """สร้างหรืออัปเดต launcher เปิดกลุ่ม คืน path."""

    @abstractmethod
    def remove_launcher(
        self,
        dir_name: str,
        target_dir: Path | str | None = None,
        icons_root: Path | str | None = None,
    ) -> bool:
        """ลบ launcher ของกลุ่ม คืน True ถ้าเคยมี."""

    @abstractmethod
    def read_launcher_name(self, path: str | os.PathLike[str]) -> str | None:
        """อ่านชื่อแสดงจากไฟล์ launcher."""

    # --- Taskbar / Panel Pinning ---

    @abstractmethod
    def pinned_desktop_ids(
        self, config_dir: Path | None = None, runner: Callable | None = None
    ) -> set[str]:
        """คืนชุด id launcher ทั้งหมดที่ปักอยู่บน panel/taskbar."""

    def is_pinned(
        self,
        desktop_id: str,
        config_dir: Path | None = None,
        runner: Callable | None = None,
    ) -> bool:
        return desktop_id in self.pinned_desktop_ids(config_dir, runner)

    @abstractmethod
    def pin_to_panel(
        self,
        desktop_id: str,
        runner: Callable | None = None,
        config_dir: Path | None = None,
        refresh: bool = True,
    ) -> str:
        """ปัก launcher ลง panel/taskbar คืนชื่อวิธีที่ใช้."""

    @abstractmethod
    def unpin_from_panel(
        self,
        desktop_id: str,
        runner: Callable | None = None,
        config_dir: Path | None = None,
        refresh: bool = True,
    ) -> bool:
        """ถอด launcher ออกจาก panel/taskbar คืน True ถ้าถอดได้."""

    def stale_pin_label(
        self,
        dir_name: str,
        env: dict | None = None,
        home: Path | str | None = None,
        pinned: dict[str, str] | None = None,
    ) -> bool:
        """True เมื่อป้ายบน taskbar ยังเป็นชื่อเก่าหลังเปลี่ยนชื่อกลุ่ม (เฉพาะ Windows)."""
        return False

    @abstractmethod
    def available_actions(self) -> Sequence[str]:
        """รายการวิธีปักที่รองรับบน OS นี้."""

    # --- Hotkey helpers ---

    def hotkey_slot(self, dir_name: str) -> str:
        from .linux.hotkeys import hotkey_slot as _slot

        return _slot(dir_name)

    def format_hotkey_display(self, binding: str) -> str:
        from .linux.hotkeys import cinnamon_to_display

        return cinnamon_to_display(binding)
