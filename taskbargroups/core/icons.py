"""ค้นหาและแคชไฟล์ไอคอน (Python ล้วน ข้าม OS ไม่ผูก GUI).

ทำหน้าที่สองอย่าง:
1. resolve — หา *ไฟล์รูปจริง* จาก target ที่ผู้ใช้ตั้งไว้ (ไฟล์รูปเอง,
   `.desktop` แล้วอ่านคีย์ `Icon=`, หรือชื่อไอคอนในธีมของระบบ)
2. cache — คัดลอกไฟล์รูปที่หาได้มาเก็บใน `icons/` ของกลุ่ม เพื่อให้เปิด
   กลุ่มได้เร็วและพกพา config ไปเครื่องอื่นได้
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

ICONS_DIR_NAME = "icons"

IMAGE_SUFFIXES = {".png", ".svg", ".jpg", ".jpeg", ".ico", ".bmp", ".xpm", ".gif"}

_SAFE_STEM = re.compile(r"[^A-Za-z0-9._-]+")

_APPIMAGE_TYPE2_MAGIC = b"AI\x02"
_APPIMAGE_EXTRACT_TIMEOUT = 120
_APPIMAGE_CACHE_DIRNAME = "taskbargroups-appimage-icons"


class IconError(Exception):
    """โยนเมื่อคัดลอกไฟล์ไอคอนไม่สำเร็จ."""


def is_image_file(path: str | os.PathLike[str]) -> bool:
    candidate = Path(path)
    return candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES


def safe_stem(name: str) -> str:
    """ทำชื่อให้ปลอดภัยพอใช้เป็นชื่อไฟล์ไอคอน."""
    stem = _SAFE_STEM.sub("_", (name or "").strip())
    return stem.strip("._") or "icon"


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


def desktop_search_dirs() -> list[Path]:
    home = Path.home()
    dirs = [
        home / ".local" / "share" / "applications",
        Path("/usr/local/share/applications"),
        Path("/usr/share/applications"),
    ]
    return [d for d in dirs if d.is_dir()]


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
    """อ่านคีย์ Icon= จากไฟล์ .desktop แล้วคืนไฟล์รูปจริง (ถ้าหาเจอ)."""
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
    if not icon_value:
        return None
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
    return None


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


def resolve_icon_source(target: str | os.PathLike[str] | None) -> Path | None:
    """หาไฟล์รูปที่ใช้เป็นไอคอนได้จาก target ที่ผู้ใช้ตั้งไว้."""
    if not target:
        return None
    candidate = Path(str(target))
    if candidate.suffix.lower() == ".desktop" and candidate.is_file():
        return icon_from_desktop_file(candidate)
    if is_image_file(candidate):
        return candidate
    if is_appimage(candidate):
        return _extract_appimage_icon(candidate)
    return None


def cache_icon(source: str | os.PathLike[str], icons_dir: Path, stem: str) -> str:
    """คัดลอกไฟล์รูปเข้าโฟลเดอร์ไอคอน คืนชื่อไฟล์ที่บันทึก."""
    src = Path(source)
    if not src.is_file():
        raise IconError(f"ไม่พบไฟล์ไอคอน: {source}")
    safe = safe_stem(stem)
    try:
        icons_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise IconError(f"สร้างโฟลเดอร์ไอคอนไม่สำเร็จ: {exc}") from exc
    for old in icons_dir.glob(f"{safe}.*"):
        try:
            old.unlink()
        except OSError:
            pass
    dest = icons_dir / f"{safe}{src.suffix.lower()}"
    try:
        shutil.copy2(src, dest)
    except OSError as exc:
        raise IconError(f"คัดลอกไอคอนไม่สำเร็จ: {exc}") from exc
    return dest.name


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
    if not stem:
        stem = Path(str(target or "")).stem or "icon"
    name = cache_icon(src, icons_dir, stem)
    return f"{ICONS_DIR_NAME}/{name}"


def platform_note() -> str:
    """หมายเหตุสั้นๆ ว่าดึงไอคอนจากโปรแกรมได้แค่ไหนในแต่ละ OS."""
    if sys.platform == "win32":
        return "Windows: ดึงไอคอนอัตโนมัติได้จาก .lnk/.desktop หรือเลือกไฟล์เอง"
    if sys.platform == "darwin":
        return "macOS: แนะนำเลือกไฟล์ไอคอนเอง (.icns/.png)"
    return (
        "Linux: ดึงจาก .desktop/ชื่อไอคอนในธีม/ไอคอนใน AppImage หรือเลือกไฟล์เองได้"
    )
