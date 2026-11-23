"""ค้นหาและสแกนไอคอนจากธีมระบบ Freedesktop + Flatpak + Snap (Linux)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from .cache import IMAGE_SUFFIXES

_THEME_ICON_SUFFIXES = frozenset({".png", ".svg", ".xpm", ".jpg", ".jpeg"})
_CATEGORY_PREFIXES = ("categories", "places")
_APPS_PREFIXES = ("apps",)
_SIZE_DIR_RE = re.compile(r"^(\d+)(?:x\d+)?(?:@(\d+)x)?$", re.IGNORECASE)


def _dedup_existing_dirs(candidates: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for d in candidates:
        try:
            if not d.is_dir():
                continue
            resolved = d.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        out.append(d)
    return out


def _xdg_data_dirs() -> list[Path]:
    raw = os.environ.get("XDG_DATA_DIRS", "")
    return [Path(p) for p in raw.split(os.pathsep) if p.strip()]


def theme_search_dirs() -> list[Path]:
    """โฟลเดอร์มาตรฐานที่มักมีไอคอนของธีม (Linux + Flatpak + Snap)."""
    home = Path.home()
    dirs = [
        home / ".local" / "share" / "icons",
        home / ".icons",
        home / ".local" / "share" / "flatpak" / "exports" / "share" / "icons",
        Path("/var/lib/flatpak/exports/share/icons"),
        Path("/usr/local/share/icons"),
        Path("/usr/share/icons"),
        Path("/usr/share/pixmaps"),
        Path("/var/lib/snapd/desktop/icons"),
    ]
    for data_dir in _xdg_data_dirs():
        dirs.append(data_dir / "icons")
    return _dedup_existing_dirs(dirs)


def desktop_search_dirs() -> list[Path]:
    """โฟลเดอร์เก็บไฟล์ `.desktop` ของแอปในระบบ (Linux + Flatpak + Snap)."""
    home = Path.home()
    dirs = [
        home / ".local" / "share" / "applications",
        home / ".local" / "share" / "flatpak" / "exports" / "share" / "applications",
        Path("/var/lib/flatpak/exports/share/applications"),
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
        Path("/var/lib/snapd/desktop/applications"),
    ]
    for data_dir in _xdg_data_dirs():
        dirs.append(data_dir / "applications")
    return _dedup_existing_dirs(dirs)


def _size_from_path(icon_file: Path) -> int:
    """เดาความละเอียด (px) จากชื่อโฟลเดอร์บรรพบุรุษ เช่น `256x256`, `48@2x`."""
    for part in reversed(icon_file.parts[:-1]):
        match = _SIZE_DIR_RE.match(part)
        if match:
            base = int(match.group(1))
            scale = int(match.group(2) or 1)
            return base * scale
    return 0


def _theme_match_rank(icon_file: Path) -> tuple[int, int]:
    """ให้คะแนนไฟล์ไอคอน: SVG สี > PNG ความละเอียดสูง > เลี่ยง -symbolic."""
    score = 0
    is_symbolic = any("symbolic" in part.lower() for part in icon_file.parts)
    if icon_file.suffix.lower() == ".svg":
        score += 100_000
    score += _size_from_path(icon_file)
    if icon_file.parent.name.lower().startswith(_APPS_PREFIXES):
        score += 50
    if is_symbolic:
        score -= 200_000
    try:
        file_size = icon_file.stat().st_size
    except OSError:
        file_size = 0
    return (score, file_size)


def find_theme_icon(name: str, search_dirs: Iterable[Path] | None = None) -> Path | None:
    """หาไฟล์ไอคอนความละเอียดดีที่สุดจากชื่อในธีม (SVG > 256px > 128px > ... > 16px)."""
    lookup = (name or "").strip()
    if not lookup:
        return None
    dirs = list(search_dirs) if search_dirs is not None else theme_search_dirs()
    best: tuple[tuple[int, int], Path] | None = None
    for base in dirs:
        if not base.is_dir():
            continue
        for suffix in (".svg", ".png", ".xpm", ".ico"):
            direct = base / f"{lookup}{suffix}"
            if direct.is_file():
                rank = _theme_match_rank(direct)
                if best is None or rank > best[0]:
                    best = (rank, direct)
        try:
            for candidate in base.rglob(f"{lookup}.*"):
                if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
                    # ตรวจชื่อ stem ให้ตรงเป๊ะ (กัน firefox.png ชน firefox.alt.png)
                    if candidate.stem != lookup:
                        continue
                    rank = _theme_match_rank(candidate)
                    if best is None or rank > best[0]:
                        best = (rank, candidate)
        except OSError:
            continue
    return best[1] if best is not None else None


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
