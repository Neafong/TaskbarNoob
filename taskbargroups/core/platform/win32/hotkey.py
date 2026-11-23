"""Windows global hotkey registration (`RegisterHotKey` / `UnregisterHotKey`)."""

from __future__ import annotations

import sys

from .lnk import WindowsError

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

_MODIFIER_MAP = {
    "alt": MOD_ALT,
    "control": MOD_CONTROL,
    "ctrl": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "super": MOD_WIN,
    "meta": MOD_WIN,
    "win": MOD_WIN,
}


def parse_hotkey_binding(binding: str) -> tuple[int, int]:
    """แปลง `<Control><Alt>t` → (modifiers, vk).

    vk มาจากตัวอักษรเดี่ยว (A–Z/0–9 → รหัส virtual-key ตรงตัว) · ถ้าไม่ใช่รูปแบบนี้
    ให้โยน WindowsError (GUI โชว์ให้ผู้ใช้เลือกใหม่).
    """
    text = (binding or "").strip()
    modifiers = 0
    while text.startswith("<"):
        end = text.find(">")
        if end == -1:
            break
        token = text[1:end].strip().lower()
        text = text[end + 1 :]
        modifiers |= _MODIFIER_MAP.get(token, 0)
    key = text.strip()
    if len(key) == 1 and ("a" <= key.lower() <= "z" or "0" <= key <= "9"):
        return modifiers, ord(key.upper())
    raise WindowsError(f"ปุ่มลัดใช้บน Windows ไม่ได้: {binding!r}")


def _user32():
    import ctypes

    return ctypes.WinDLL("user32", use_last_error=True)


def register_hotkey(hotkey_id: int, hwnd: int, modifiers: int, vk: int) -> None:
    """ลงทะเบียน global hotkey กับ Windows (โยน WindowsError ถ้าไม่สำเร็จ)."""
    if sys.platform != "win32":
        raise WindowsError("ฟังก์ชันนี้ใช้ได้บน Windows เท่านั้น")
    try:
        import ctypes
        from ctypes import wintypes

        user32 = _user32()
        user32.RegisterHotKey.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.RegisterHotKey.restype = wintypes.BOOL
        ok = user32.RegisterHotKey(hwnd, hotkey_id, modifiers, vk)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    if not ok:
        raise WindowsError("ลงทะเบียนปุ่มลัดไม่สำเร็จ (อาจชนกับโปรแกรมอื่น)")


def unregister_hotkey(hotkey_id: int, hwnd: int) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        user32 = _user32()
        user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.UnregisterHotKey.restype = wintypes.BOOL
        user32.UnregisterHotKey(hwnd, hotkey_id)
    except OSError:
        pass
