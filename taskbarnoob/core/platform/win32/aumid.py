"""Windows AppUserModelID (AUMID) helpers.

Windows รวมปุ่มบน taskbar ตาม AUMID — ถ้าทุกกลุ่มใช้ AUMID เดียวกับตัวแอป
ปุ่มจะซ้อนกันเหลือปุ่มเดียว จึงต้องแยก AUMID ต่อกลุ่มและของหน้าต่างหลัก
"""

from __future__ import annotations

import sys

APP_ID = "taskbarnoob"


def aumid(dir_name: str) -> str:
    """AppUserModelID เฉพาะกลุ่ม."""
    from ...storage import safe_dir_name

    slug = safe_dir_name(dir_name).lower().replace(" ", "-")
    return f"{APP_ID}.group.{slug}"


def app_aumid() -> str:
    """AppUserModelID กลางของหน้าต่างหลัก (แยกจากกลุ่ม ไม่ให้ไปสิงปุ่ม .lnk)."""
    return f"{APP_ID}.app"


def set_app_aumid() -> None:
    """ตั้ง AUMID ของโปรเซสหน้าต่างหลัก (ต้องเรียกก่อนเปิดหน้าต่างแรก)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_aumid())
    except (OSError, AttributeError):
        pass


def set_process_aumid(dir_name: str) -> None:
    """ตั้ง AUMID ของโปรเซสให้ตรงกับ `.lnk` ของกลุ่ม (ตอนเปิด flyout)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(aumid(dir_name))
    except (OSError, AttributeError):
        pass
