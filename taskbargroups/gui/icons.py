"""ตัวช่วยแปลง shortcut/กลุ่ม เป็น QIcon."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider

from taskbargroups.core import icons as core_icons
from taskbargroups.core.models import Group, Shortcut
from taskbargroups.core.storage import ConfigStore

_provider = QFileIconProvider()
_FALLBACK = "application-x-executable"

# นามสกุลที่ให้ QFileIconProvider ดึงไอคอนระบบให้ (Windows/macOS)
# — core ดึงให้ไม่ได้ (ไม่ใช่ไฟล์รูป) แต่ Qt อ่านไอคอนฝังของ OS ได้
_PROVIDER_SUFFIXES = frozenset(
    {".exe", ".lnk", ".bat", ".cmd", ".app", ".command"}
)


def _from_file(path: Path) -> QIcon | None:
    if path.is_file():
        return QIcon(str(path))
    return None


def _provider_icon(target: str) -> QIcon | None:
    """ไอคอนจาก OS ผ่าน QFileIconProvider."""
    path = Path((target or "").strip())
    if sys.platform in ("win32", "darwin"):
        if path.suffix.lower() not in _PROVIDER_SUFFIXES or not path.is_file():
            return None
    else:
        if not path.exists():
            return None
    icon = _provider.icon(QFileInfo(str(path)))
    return icon if not icon.isNull() else None


def shortcut_icon(shortcut: Shortcut, store: ConfigStore, dir_name: str) -> QIcon:
    cached = store.resolve_relative(dir_name, shortcut.icon)
    if cached is not None:
        icon = _from_file(cached)
        if icon is not None:
            return icon
    target = shortcut.target.strip()
    if target:
        icon = _from_file(Path(target))
        if icon is not None and not icon.isNull():
            return icon
        icon = _provider_icon(target)
        if icon is not None:
            return icon
    return QIcon.fromTheme(_FALLBACK)


def group_icon(group: Group, store: ConfigStore, dir_name: str) -> QIcon:
    cached = store.resolve_relative(dir_name, group.icon)
    if cached is not None:
        icon = _from_file(cached)
        if icon is not None:
            return icon
    fallback = _from_file(default_group_icon_file(store))
    if fallback is not None:
        return fallback
    return QIcon.fromTheme("folder")


def default_group_icon_file(store: ConfigStore) -> Path | None:
    """ไฟล์ไอคอนสำรองของกลุ่ม — ดึงไอคอนโฟลเดอร์จากระบบมาแคชไว้ครั้งเดียว.

    ต้องเป็น **ไฟล์จริง** ไม่ใช่ QIcon เปล่า เพราะ `.lnk` บน Windows รับได้แค่พาธ
    (IconLocation) — ถ้าไม่มีไฟล์ ปุ่มบน taskbar จะโชว์ไอคอน shortcut ทั่วไปของ Windows

    เก็บใน `config/cache/` (ไม่ใช่ `config/groups/`) เพื่อไม่ให้สับสนกับกลุ่มจริง
    """
    cache = store.cache_dir() / "icons"
    png = cache / "default.png"
    if png.is_file():
        return png
    source = cache if cache.is_dir() else store.groups_dir
    icon = _provider.icon(QFileInfo(str(source if source.is_dir() else Path.home())))
    pixmap = icon.pixmap(256, 256)
    if pixmap.isNull():
        return None
    try:
        cache.mkdir(parents=True, exist_ok=True)
        if not pixmap.save(str(png), "PNG"):
            return None
    except (OSError, RuntimeError):
        return None
    return png


def cache_provider_icon(
    store: ConfigStore,
    dir_name: str,
    target: str | None,
    stem: str,
    size: int = 256,
) -> str | None:
    """แคชไอคอนจาก OS ลง icons/ ของกลุ่ม คืน path สัมพัทธ์ (None ถ้าทำไม่ได้).

    ใช้ตอนบันทึก เผื่อไฟล์พวก .exe/.lnk ที่ core แคชให้ไม่ได้ — จะได้พกพา config
    ข้ามเครื่องได้เหมือนไอคอนชนิดอื่น.
    """
    path = Path((target or "").strip())
    if path.suffix.lower() not in _PROVIDER_SUFFIXES or not path.is_file():
        return None
    icon = _provider.icon(QFileInfo(str(path)))
    if icon.isNull():
        return None
    pixmap = icon.pixmap(size, size)
    if pixmap.isNull():
        return None
    icons_dir = store.icons_dir(dir_name)
    try:
        icons_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    safe = core_icons.safe_stem(stem or path.stem or "icon")
    for old in icons_dir.glob(f"{safe}.*"):
        try:
            old.unlink()
        except OSError:
            pass
    dest = icons_dir / f"{safe}.png"
    try:
        if not pixmap.save(str(dest), "PNG"):
            return None
    except (OSError, RuntimeError):
        return None
    return f"{core_icons.ICONS_DIR_NAME}/{dest.name}"
