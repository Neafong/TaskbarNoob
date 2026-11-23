"""ดึงไอคอนจากไฟล์ AppImage (Linux) โดยแตกผ่าน --appimage-extract."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .cache import IMAGE_SUFFIXES

_APPIMAGE_TYPE2_MAGIC = b"AI\x02"
_APPIMAGE_EXTRACT_TIMEOUT = 120
_APPIMAGE_CACHE_DIRNAME = "taskbarnoob-appimage-icons"

_APPIMAGE_ENV_STRIP = (
    "APPDIR",
    "APPIMAGE",
    "ARGV0",
    "OWD",
    "APPIMAGE_EXTRACT_AND_RUN",
    "APPIMAGE_SILENT_INSTALL",
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "PYTHONHOME",
    "PYTHONPATH",
)


def is_appimage(path: str | os.PathLike[str]) -> bool:
    """ตรวจว่าไฟล์เป็น AppImage (ชนิด 2 ขึ้นไป) หรือไม่."""
    candidate = Path(str(path))
    if not candidate.is_file():
        return False
    try:
        with candidate.open("rb") as handle:
            header = handle.read(12)
    except OSError:
        return False
    if header[:4] == b"\x7fELF" and header[8:11] == _APPIMAGE_TYPE2_MAGIC:
        return True
    return candidate.suffix.lower() == ".appimage"


def _appimage_cache_dir() -> Path:
    return Path(tempfile.gettempdir()) / _APPIMAGE_CACHE_DIRNAME


def _clean_appimage_env() -> dict[str, str]:
    """ตัด env ของ AppImage ตัวเองออกก่อนรัน target AppImage (กัน runtime สับสน)."""
    env = dict(os.environ)
    for key in _APPIMAGE_ENV_STRIP:
        env.pop(key, None)
    return env


def _icon_from_appimage_desktop(root: Path, desktop: Path) -> Path | None:
    try:
        text = desktop.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    icon_value = ""
    for line in text.splitlines():
        if line.startswith("Icon=") and not line.startswith("Icon["):
            icon_value = line[len("Icon=") :].strip()
            break
    if not icon_value:
        return None
    names = [icon_value, Path(icon_value).stem]
    bases = (
        root,
        root / "usr" / "share" / "icons",
        root / "usr" / "share" / "pixmaps",
    )
    for base in bases:
        if not base.is_dir():
            continue
        for name in names:
            if not name:
                continue
            direct = base / name
            if direct.is_file() and direct.suffix.lower() in IMAGE_SUFFIXES:
                return direct
    for name in names:
        if not name:
            continue
        try:
            matches = [
                p
                for p in root.rglob(f"{Path(name).name}.*")
                if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES
            ]
        except OSError:
            continue
        if matches:
            return max(matches, key=lambda p: p.stat().st_size)
    return None


def _find_appimage_icon(root: Path) -> Path | None:
    dir_icon = root / ".DirIcon"
    try:
        if dir_icon.exists():
            resolved = dir_icon.resolve()
            if resolved.is_file() and resolved.suffix.lower() in IMAGE_SUFFIXES:
                return resolved
    except OSError:
        pass
    for desktop in sorted(root.glob("*.desktop")):
        icon = _icon_from_appimage_desktop(root, desktop)
        if icon is not None:
            return icon
    images: list[Path] = []
    try:
        for path in root.rglob("*"):
            try:
                if (
                    path.is_file()
                    and path.suffix.lower() in IMAGE_SUFFIXES
                    and path.stat().st_size > 0
                ):
                    images.append(path)
            except OSError:
                continue
    except OSError:
        return None
    if images:
        return max(images, key=lambda p: p.stat().st_size)
    return None


def _extract_appimage_icon(path: Path) -> Path | None:
    """แตกไฟล์ AppImage แล้วดึงไอคอนจริงออกมาแคชไว้ใน temp."""
    try:
        stat = path.stat()
    except OSError:
        return None
    key = hashlib.sha1(
        f"{path}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8", "replace")
    ).hexdigest()[:16]
    cache = _appimage_cache_dir()
    if cache.is_dir():
        for existing in cache.glob(f"{key}.*"):
            if existing.is_file():
                return existing
    with tempfile.TemporaryDirectory(prefix="tbg-appimage-") as tmp:
        try:
            subprocess.run(
                [str(path), "--appimage-extract"],
                cwd=tmp,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=_APPIMAGE_EXTRACT_TIMEOUT,
                check=False,
                env=_clean_appimage_env(),
            )
        except (OSError, subprocess.SubprocessError):
            return None
        root = Path(tmp) / "squashfs-root"
        if not root.is_dir():
            return None
        icon = _find_appimage_icon(root)
        if icon is None:
            return None
        try:
            cache.mkdir(parents=True, exist_ok=True)
        except OSError:
            return None
        dest = cache / f"{key}{icon.suffix.lower() or '.png'}"
        try:
            shutil.copy2(icon, dest)
        except OSError:
            return None
        return dest


def icon_from_appimage(path: str | os.PathLike[str]) -> Path | None:
    """ดึงไอคอนจริงจากไฟล์ AppImage โดยแตกผ่าน runtime (ไม่ต้อง mount)."""
    candidate = Path(str(path))
    if not is_appimage(candidate):
        return None
    return _extract_appimage_icon(candidate)
