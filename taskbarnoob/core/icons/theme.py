"""ค้นหาและสแกนไอคอนจากธีมระบบ Freedesktop (Linux)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .cache import IMAGE_SUFFIXES

_THEME_ICON_SUFFIXES = frozenset({".png", ".svg", ".xpm", ".jpg", ".jpeg"})
_CATEGORY_PREFIXES = ("categories", "places")
_APPS_PREFIXES = ("apps",)


def theme_search_dirs() -> list[Path]:
    """โฟลเดอร์มาตรฐานที่มักมีไอคอนของธีม (Linux เป็นหลัก)."""
    home = Path.home()
    dirs = [
        home / ".local" / "share" / "icons",
        home / ".icons",
        Path("/usr/local/share/icons"),
        Path("/usr/share/icons"),
        Path("/usr/share/pixmaps"),
    ]
    return [d for d in dirs if d.is_dir()]


def desktop_search_dirs() -> list[Path]:
    home = Path.home()
    dirs = [
        home / ".local" / "share" / "applications",
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
    ]
    return [d for d in dirs if d.is_dir()]


def find_theme_icon(name: str, search_dirs: Iterable[Path] | None = None) -> Path | None:
    """หาไฟล์ไอคอนจากชื่อในธีม เช่น 'firefox' หรือ 'applications-internet'."""
    lookup = (name or "").strip()
    if not lookup:
        return None
    dirs = list(search_dirs) if search_dirs is not None else theme_search_dirs()
    for base in dirs:
        if not base.is_dir():
            continue
        for suffix in (".png", ".svg", ".xpm", ".ico"):
            direct = base / f"{lookup}{suffix}"
            if direct.is_file():
                return direct
        try:
            for candidate in base.rglob(f"{lookup}.*"):
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
                    return candidate
        except OSError:
            continue
    return None


def _matches_category(dir_name: str, category: str) -> bool:
    low = dir_name.lower()
    if category == "categories":
        return low.startswith(_CATEGORY_PREFIXES)
    if category == "apps":
        return low.startswith(_APPS_PREFIXES)
    return True


def _icon_priority(icon_file: Path, size: int, category: str) -> int:
    score = 0
    if icon_file.suffix.lower() == ".svg":
        score += 100000
    score += size
    parent = icon_file.parent.name.lower()
    if category == "categories" and parent.startswith(_CATEGORY_PREFIXES):
        score += 50
    elif parent.startswith(_APPS_PREFIXES):
        score += 50
    return score


def scan_theme_icons(
    search_dirs: Iterable[Path] | None = None,
    category: str = "all",
    limit: int = 4000,
) -> dict[str, Path]:
    """สแกนไอคอนจากธีม Freedesktop แยกตามหมวด ('categories' | 'apps' | 'all')."""
    bases = list(dict.fromkeys(
        search_dirs if search_dirs is not None else theme_search_dirs()
    ))
    best: dict[str, tuple[int, Path]] = {}
    for base in bases:
        if not base.is_dir() or len(best) >= limit:
            continue
        try:
            themes = list(base.iterdir())
        except OSError:
            continue
        for theme in themes:
            if not theme.is_dir():
                continue
            try:
                size_dirs = list(theme.iterdir())
            except OSError:
                continue
            for size_dir in size_dirs:
                if not size_dir.is_dir():
                    continue
                try:
                    size = int(size_dir.name.split("x")[0])
                except (ValueError, IndexError):
                    size = 0
                try:
                    cat_dirs = list(size_dir.iterdir())
                except OSError:
                    continue
                for cat_dir in cat_dirs:
                    if not cat_dir.is_dir():
                        continue
                    if not _matches_category(cat_dir.name, category):
                        continue
                    try:
                        files = list(cat_dir.iterdir())
                    except OSError:
                        continue
                    for icon_file in files:
                        if icon_file.suffix.lower() not in _THEME_ICON_SUFFIXES:
                            continue
                        name = icon_file.stem
                        if not name:
                            continue
                        score = _icon_priority(icon_file, size, category)
                        existing = best.get(name)
                        if existing is None or score > existing[0]:
                            best[name] = (score, icon_file)
                        if len(best) >= limit:
                            return {k: v[1] for k, v in best.items()}
    return {k: v[1] for k, v in best.items()}
