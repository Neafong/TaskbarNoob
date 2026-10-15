"""System-wide hotkey ฝั่ง Windows (RegisterHotKey + native event filter).

ใช้เฉพาะบน win32 — import ได้ทุก OS แต่การเรียก API จะโยนนอก Windows.
ผัง: HotkeyRegistry เก็บ {slot: (id, dir_name)} · WinHotkeyFilter รับ WM_HOTKEY
แล้วให้ opener เปิด flyout กลุ่มผ่าน `exe --open <dir>` (โปรเซสใหม่ — single-instance
ฝั่ง flyout จัดการให้เหมือนกด .lnk).
"""

from __future__ import annotations

import ctypes
import subprocess

from PySide6.QtCore import QAbstractNativeEventFilter, QObject

from taskbargroups.core.win32 import (
    parse_hotkey_binding,
    register_hotkey,
    unregister_hotkey,
)

WM_HOTKEY = 0x0312


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.c_void_p),
        ("message", ctypes.c_uint),
        ("wParam", ctypes.c_size_t),
        ("lParam", ctypes.c_size_t),
        ("time", ctypes.c_ulong),
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


class HotkeyRegistry:
    """เก็บ map slot → (id เลข, ชื่อกลุ่ม) สำหรับ RegisterHotKey."""

    def __init__(self) -> None:
        self._entries: dict[str, tuple[int, str]] = {}
        self._next_id = 1

    def register_slot(
        self, slot: str, dir_name: str, binding: str, hwnd: int
    ) -> None:
        modifiers, vk = parse_hotkey_binding(binding)
        self.unregister_slot(slot, hwnd)
        hotkey_id = self._next_id
        self._next_id += 1
        register_hotkey(hotkey_id, hwnd, modifiers, vk)
        self._entries[slot] = (hotkey_id, dir_name)

    def unregister_slot(self, slot: str, hwnd: int) -> bool:
        entry = self._entries.pop(slot, None)
        if entry is None:
            return False
        unregister_hotkey(entry[0], hwnd)
        return True

    def find_dir(self, hotkey_id: int) -> str | None:
        for _slot, (entry_id, dir_name) in self._entries.items():
            if entry_id == hotkey_id:
                return dir_name
        return None

    def slots(self) -> dict[str, str]:
        return {slot: dir_name for slot, (_id, dir_name) in self._entries.items()}


class WinHotkeyFilter(QAbstractNativeEventFilter):
    """ดัก WM_HOTKEY แล้วเปิด flyout กลุ่มผ่านโปรเซสใหม่."""

    def __init__(
        self,
        registry: HotkeyRegistry,
        exe_args: list,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._registry = registry
        self._exe_args = list(exe_args)

    def nativeEventFilter(self, event_type, message):
        try:
            kind = bytes(event_type).decode("ascii", "ignore")
        except (TypeError, ValueError):
            kind = ""
        if "windows" not in kind.lower():
            return False, 0
        try:
            msg = ctypes.cast(int(message), ctypes.POINTER(_MSG)).contents
        except (TypeError, ValueError):
            return False, 0
        if msg.message != WM_HOTKEY:
            return False, 0
        dir_name = self._registry.find_dir(int(msg.wParam))
        if dir_name is None:
            return False, 0
        try:
            subprocess.Popen(
                [*self._exe_args, "--open", dir_name],
                start_new_session=True,
            )
        except OSError:
            return False, 0
        return True, 0


registry = HotkeyRegistry()
