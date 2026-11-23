"""ดึงไอคอนเกม Steam จาก `steam://rungameid/<appid>` ข้าม OS (Linux + Windows)."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable

from .cache import IMAGE_SUFFIXES

_STEAM_APPID_RE = re.compile(r"steam://(?:rungameid|run)/(\d+)", re.IGNORECASE)


def extract_steam_appid(text: str | None) -> str | None:
    """ดึง Steam AppID จากข้อความหรือ URL เช่น `steam://rungameid/730`."""
    if not text:
        return None
    match = _STEAM_APPID_RE.search(text)
    return match.group(1) if match else None


def steam_appid_from_file(path: str | os.PathLike[str]) -> str | None:
    """อ่าน Steam AppID จากไฟล์ `.desktop` (Exec=/URL=) หรือ `.url` (URL=)."""
    candidate = Path(path)
    if not candidate.is_file():
        return None
    suffix = candidate.suffix.lower()
    if suffix not in (".desktop", ".url"):
        return None
    try:
        text = candidate.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        low = stripped.lower()
        if suffix == ".desktop" and (low.startswith("exec=") or low.startswith("url=")):
            appid = extract_steam_appid(stripped)
            if appid:
                return appid
        elif suffix == ".url" and low.startswith("url="):
            appid = extract_steam_appid(stripped)
            if appid:
                return appid
    return None


def _read_windows_steam_path() -> Path | None:
    """อ่าน `SteamPath` จาก Windows Registry (HKCU\\Software\\Valve\\Steam)."""
    if sys.platform != "win32":
        return None
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            value, _ = winreg.QueryValueEx(key, "SteamPath")
            if value:
                return Path(str(value))
    except OSError:
        return None
    return None


def steam_librarycache_dirs(steam_root: Path | None = None) -> list[Path]:
    """คืนโฟลเดอร์ `appcache/librarycache` ของ Steam ที่พบจริงบนเครื่อง."""
    candidates: list[Path] = []
    if steam_root is not None:
        candidates.append(steam_root / "appcache" / "librarycache")
    elif sys.platform == "win32":
        reg_path = _read_windows_steam_path()
        if reg_path is not None:
            candidates.append(reg_path / "appcache" / "librarycache")
        for env_key in ("ProgramFiles(x86)", "ProgramFiles"):
            base = os.environ.get(env_key)
            if base:
                candidates.append(Path(base) / "Steam" / "appcache" / "librarycache")
    else:
        home = Path.home()
        candidates.extend(
            [
                home / ".local" / "share" / "Steam" / "appcache" / "librarycache",
                home / ".steam" / "steam" / "appcache" / "librarycache",
                home / ".steam" / "debian-installation" / "appcache" / "librarycache",
                home
                / ".var"
                / "app"
                / "com.valvesoftware.Steam"
                / ".local"
                / "share"
                / "Steam"
                / "appcache"
                / "librarycache",
            ]
        )
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


def _pick_best_subdir_icon(appid_dir: Path) -> Path | None:
    """เลือกไฟล์รูปที่เหมาะเป็นไอคอนที่สุดจากโฟลเดอร์ใหม่ `<librarycache>/<appid>/`."""
    try:
        files = [
            p
            for p in appid_dir.rglob("*")
            if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
        ]
    except OSError:
        return None
    if not files:
        return None

    def rank(p: Path) -> tuple[int, int]:
        name = p.name.lower()
        if "icon" in name:
            priority = 4
        elif "logo" in name:
            priority = 3
        elif "header" in name or "capsule" in name:
            priority = 2
        else:
            priority = 1
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        return (priority, size)

    return max(files, key=rank)


def find_steam_game_icon(
    appid: str, cache_dirs: Iterable[Path] | None = None
) -> Path | None:
    """หาไฟล์รูปไอคอนของเกม Steam จาก `librarycache` (รองรับทั้งโครงสร้างเก่าและใหม่)."""
    clean_id = (appid or "").strip()
    if not clean_id or not clean_id.isdigit():
        return None
    dirs = list(cache_dirs) if cache_dirs is not None else steam_librarycache_dirs()
    legacy_names = (
        f"{clean_id}_icon.jpg",
        f"{clean_id}_icon.png",
        f"{clean_id}_logo.png",
        f"{clean_id}_header.jpg",
    )
    for base in dirs:
        if not base.is_dir():
            continue
        # โครงสร้างเก่า: <librarycache>/<appid>_icon.jpg
        for name in legacy_names:
            direct = base / name
            if direct.is_file():
                return direct
        # โครงสร้างใหม่ (Steam 2024+): <librarycache>/<appid>/...
        subdir = base / clean_id
        if subdir.is_dir():
            picked = _pick_best_subdir_icon(subdir)
            if picked is not None:
                return picked
    return None


def icon_from_steam_shortcut(
    path: str | os.PathLike[str], cache_dirs: Iterable[Path] | None = None
) -> Path | None:
    """หาไอคอนเกม Steam จากไฟล์ `.desktop` หรือ `.url` ที่มี `steam://rungameid/`."""
    appid = steam_appid_from_file(path)
    if not appid:
        return None
    return find_steam_game_icon(appid, cache_dirs=cache_dirs)
