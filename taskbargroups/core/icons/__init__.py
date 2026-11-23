"""ค้นหาและแคชไฟล์ไอคอน (Python ล้วน ข้าม OS ไม่ผูก GUI).

ทำหน้าที่สองอย่าง:
1. resolve — หา *ไฟล์รูปจริง* จาก target ที่ผู้ใช้ตั้งไว้ (ไฟล์รูปเอง,
   `.desktop`, `.url`, Steam `steam://rungameid/<appid>`, AppImage, หรือธีมระบบ)
2. cache — คัดลอกไฟล์รูปที่หาได้มาเก็บใน `icons/` ของกลุ่ม เพื่อให้เปิด
   กลุ่มได้เร็วและพกพา config ไปเครื่องอื่นได้
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .appimage import (
    _APPIMAGE_TYPE2_MAGIC,
    _appimage_cache_dir,
    _clean_appimage_env,
    _extract_appimage_icon,
    icon_from_appimage,
    is_appimage,
)
from .cache import (
    ICONS_DIR_NAME,
    IMAGE_SUFFIXES,
    PROVIDER_ICON_CACHE_DIRNAME,
    IconError,
    cache_icon,
    is_image_file,
    safe_stem,
)
from .steam import (
    extract_steam_appid,
    find_steam_game_icon,
    icon_from_steam_shortcut,
    steam_appid_from_file,
    steam_librarycache_dirs,
)
from .theme import (
    desktop_search_dirs,
    find_theme_icon,
    scan_theme_icons,
    theme_search_dirs,
)


def _exec_basename(exec_value: str) -> str:
    value = (exec_value or "").strip()
    if not value:
        return ""
    first = value.split()[0]
    return Path(first.strip("\"'")).name


def icon_from_executable(target: str | os.PathLike[str]) -> Path | None:
    """หาไอคอนจริงของโปรแกรมจากไฟล์ executable โดยจับคู่ Exec= ใน .desktop."""
    candidate = Path(str(target))
    if is_appimage(candidate):
        icon = _extract_appimage_icon(candidate)
        if icon is not None:
            return icon
    name = candidate.name
    if not name:
        return None
    for base in desktop_search_dirs():
        try:
            entries = sorted(base.glob("*.desktop"))
        except OSError:
            continue
        for desktop in entries:
            try:
                text = desktop.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for line in text.splitlines():
                if line.startswith("Exec="):
                    if _exec_basename(line[5:]) == name:
                        icon = icon_from_desktop_file(desktop)
                        if icon:
                            return icon
                    break
    return None


def icon_from_desktop_file(path: str | os.PathLike[str]) -> Path | None:
    """อ่านคีย์ Icon= จากไฟล์ .desktop แล้วคืนไฟล์รูปจริง (fallback Steam librarycache)."""
    candidate = Path(path)
    if not candidate.is_file():
        return None
    icon_value: str | None = None
    try:
        for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("Icon="):
                icon_value = line[len("Icon=") :].strip()
                break
    except OSError:
        return None
    if icon_value:
        expanded = Path(icon_value).expanduser()
        if expanded.is_file():
            return expanded
        theme = find_theme_icon(icon_value)
        if theme is not None:
            return theme
        if not expanded.suffix:
            for suffix in IMAGE_SUFFIXES:
                sibling = expanded.with_suffix(suffix)
                if sibling.is_file():
                    return sibling
    return icon_from_steam_shortcut(candidate)


def _read_url_icon_file(path: Path) -> Path | None:
    """อ่าน `IconFile=` จากไฟล์ .url (Internet shortcut)."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith("iconfile="):
            value = stripped[len("iconfile=") :].strip()
            if value:
                return Path(os.path.expandvars(value))
    return None


def resolve_icon_source(target: str | os.PathLike[str] | None) -> Path | None:
    """หาไฟล์รูปที่ใช้เป็นไอคอนได้จาก target ที่ผู้ใช้ตั้งไว้."""
    if not target:
        return None
    raw = str(target).strip()
    if not raw:
        return None
    appid = extract_steam_appid(raw)
    if appid:
        return find_steam_game_icon(appid)
    candidate = Path(raw)
    if candidate.suffix.lower() == ".desktop" and candidate.is_file():
        return icon_from_desktop_file(candidate)
    if candidate.suffix.lower() == ".url" and candidate.is_file():
        icon_file = _read_url_icon_file(candidate)
        if icon_file is not None and icon_file.is_file():
            return icon_file
        return icon_from_steam_shortcut(candidate)
    if is_image_file(candidate):
        return candidate
    if is_appimage(candidate):
        return _extract_appimage_icon(candidate)
    return None


def cache_shortcut_icon(
    icons_dir: Path,
    target: str | None,
    stem: str,
    source: str | os.PathLike[str] | None = None,
) -> str | None:
    """แคชไอคอนให้ shortcut คืน path สัมพัทธ์ในโฟลเดอร์กลุ่ม หรือ None.

    ถ้า `source` ถูกส่งมาจะใช้ไฟล์นั้นก่อน ไม่งั้นจะพยายาม resolve จาก target.
    """
    src = Path(source) if source else resolve_icon_source(target)
    if src is None or not src.is_file():
        return None
    # .ico/.exe/.lnk ไม่พกพาได้ดี (Qt โหลดได้แค่ขนาดเดียว หรือไม่โหลดเลย)
    # → คืน None เพื่อให้ฝั่ง GUI ใช้ cache_provider_icon สกัดเป็น .png แทน
    if src.suffix.lower() in (".ico", ".exe", ".lnk", ".dll"):
        return None
    if not stem:
        stem = Path(str(target or "")).stem or "icon"
    name = cache_icon(src, icons_dir, stem)
    return f"{ICONS_DIR_NAME}/{name}"


def platform_note() -> str:
    """หมายเหตุสั้นๆ ว่าดึงไอคอนจากโปรแกรมได้แค่ไหนในแต่ละ OS."""
    if sys.platform == "win32":
        return "Windows: ดึงไอคอนอัตโนมัติได้จาก .lnk/.url/.desktop/Steam หรือเลือกไฟล์เอง"
    return (
        "Linux: ดึงจาก .desktop/ชื่อไอคอนในธีม/AppImage/Steam หรือเลือกไฟล์เองได้"
    )


__all__ = [
    "ICONS_DIR_NAME",
    "IMAGE_SUFFIXES",
    "PROVIDER_ICON_CACHE_DIRNAME",
    "IconError",
    "_APPIMAGE_TYPE2_MAGIC",
    "_appimage_cache_dir",
    "_clean_appimage_env",
    "cache_icon",
    "cache_shortcut_icon",
    "desktop_search_dirs",
    "extract_steam_appid",
    "find_steam_game_icon",
    "find_theme_icon",
    "icon_from_appimage",
    "icon_from_desktop_file",
    "icon_from_executable",
    "icon_from_steam_shortcut",
    "is_appimage",
    "is_image_file",
    "platform_note",
    "resolve_icon_source",
    "safe_stem",
    "scan_theme_icons",
    "steam_appid_from_file",
    "steam_librarycache_dirs",
    "theme_search_dirs",
]
