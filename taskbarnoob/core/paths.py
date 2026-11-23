"""ตัวช่วยหา path ของ layout แบบ Portable (config อยู่ในโฟลเดอร์แอป)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

CONFIG_ENV_VAR = "TASKBARNOOB_CONFIG"
LEGACY_CONFIG_ENV_VAR = "TASKBARGROUPS_CONFIG"
APPIMAGE_ENV_VAR = "APPIMAGE"
CONFIG_DIR_NAME = "config"
GROUPS_DIR_NAME = "groups"
LIB_DIR_NAME = "lib"
APP_ICON_NAME = "taskbarnoob.png"


def bundled_lib_dirs() -> list[Path]:
    """โฟลเดอร์ไลบรารีที่พกมากับแอป (เช่น libxcb-cursor สำหรับรันจากซอร์ส)."""
    return [app_dir() / LIB_DIR_NAME]


def _is_writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write-probe"
        probe.touch()
        probe.unlink()
        return True
    except OSError:
        return False


def app_dir() -> Path:
    """โฟลเดอร์ของแอป (รากของโหมด portable).

    - รันเป็น AppImage → ใช้โฟลเดอร์เดียวกับไฟล์ `.AppImage` (พกพาได้)
    - ถูก bundle (PyInstaller) → โฟลเดอร์ของ binary
    - รันจากซอร์ส → รากโปรเจกต์
    """
    appimage = os.environ.get(APPIMAGE_ENV_VAR)
    if appimage:
        return Path(appimage).resolve().parent
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bundled_assets_dir() -> Path | None:
    """โฟลเดอร์ assets ที่ `--add-data` วางไว้ใน bundle.

    PyInstaller 6 (onedir) วาง data ใต้ `_internal/` · layout เก่า/โหมดอื่นวางตรง ๆ —
    ลองทั้งสองแบบ (แบบเดียวกับที่ใช้หาไอคอนแอป + ไอคอนปุ่ม SVG).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        for sub in ("_internal/taskbarnoob/assets", "taskbarnoob/assets"):
            candidate = Path(meipass) / sub
            if candidate.is_dir():
                return candidate
    return None


def app_icon_path() -> Path | None:
    """หาไฟล์ไอค่อนแอป (PNG) ทั้งโหมด bundle / AppImage / รันจากซอร์ส."""
    candidates = []
    bundled = bundled_assets_dir()
    if bundled:
        candidates.append(bundled / APP_ICON_NAME)
    candidates.append(app_dir() / "packaging" / "appimage" / APP_ICON_NAME)
    candidates.append(app_dir() / APP_ICON_NAME)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def default_config_dir() -> Path:
    """config dir เริ่มต้น — override ได้ด้วย env TASKBARNOOB_CONFIG (รองรับ TASKBARGROUPS_CONFIG เก่า)."""
    override = os.environ.get(CONFIG_ENV_VAR) or os.environ.get(LEGACY_CONFIG_ENV_VAR)
    if override:
        return Path(override).expanduser()
    preferred = app_dir() / CONFIG_DIR_NAME
    if _is_writable(preferred):
        return preferred
    fallback_home = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    new_dir = fallback_home / "taskbarnoob"
    legacy_dir = fallback_home / "taskbargroups"
    if not new_dir.exists() and legacy_dir.is_dir():
        return legacy_dir
    return new_dir


def groups_root(config_dir: Path | None = None) -> Path:
    root = Path(config_dir) if config_dir is not None else default_config_dir()
    return root / GROUPS_DIR_NAME
