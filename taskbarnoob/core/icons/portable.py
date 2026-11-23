"""ดึงไอคอนจากแอป portable (เช่น Electron `resources/app.asar`, VS Code tarball) อัตโนมัติ."""

from __future__ import annotations

import hashlib
import json
import os
import struct
import tempfile
from pathlib import Path

from .cache import IMAGE_SUFFIXES

_ASAR_CACHE_DIRNAME = "taskbarnoob-asar-icons"
_ICON_EXTS = (".png", ".svg")
_MAX_ASAR_JSON_BYTES = 16 * 1024 * 1024  # กันไฟล์เสีย/ใหญ่ผิดปกติ
_MAX_ICON_BYTES = 10 * 1024 * 1024


def _asar_cache_dir() -> Path:
    return Path(tempfile.gettempdir()) / _ASAR_CACHE_DIRNAME


def _rank_icon_name(rel_path: str, size: int) -> tuple[int, int]:
    """ให้คะแนนความน่าจะเป็นว่าเป็นไอคอนหลักของแอป (ไม่เอา tray/template)."""
    low = rel_path.lower()
    name = Path(low).name
    stem = Path(low).stem
    if "tray" in low or "template" in low or "badge" in low:
        return (0, size)
    if stem in ("icon", "app-icon", "appicon", "logo"):
        priority = 5
    elif "icon" in name or "logo" in name:
        priority = 4
    elif "/linux/" in low or low.startswith("linux/"):
        priority = 3
    else:
        priority = 1
    # ถ้าไฟล์อยู่ที่รากของ asar (เช่น icon.png) ให้คะแนนเพิ่ม
    if "/" not in rel_path and priority >= 4:
        priority += 1
    return (priority, size)


def icon_from_asar(asar_path: Path) -> Path | None:
    """อ่าน header ของ Electron `app.asar` แล้วสกัดไฟล์ไอคอนหลักออกมาแคช (Python ล้วน)."""
    if not asar_path.is_file():
        return None
    try:
        stat = asar_path.stat()
    except OSError:
        return None
    key = hashlib.sha1(
        f"{asar_path}:{stat.st_mtime_ns}:{stat.st_size}".encode("utf-8", "replace")
    ).hexdigest()[:16]
    cache = _asar_cache_dir()
    if cache.is_dir():
        for existing in cache.glob(f"{key}.*"):
            if existing.is_file():
                return existing

    try:
        with asar_path.open("rb") as f:
            header = f.read(16)
            if len(header) < 16:
                return None
            p1_size, header_size, _, json_len = struct.unpack("<IIII", header)
            if p1_size != 4 or json_len <= 0 or json_len > _MAX_ASAR_JSON_BYTES:
                return None
            raw_json = f.read(json_len)
            tree = json.loads(raw_json.decode("utf-8"))
            if not isinstance(tree, dict) or not isinstance(tree.get("files"), dict):
                return None

            candidates: list[tuple[tuple[int, int], str, dict]] = []

            def walk(node: dict, prefix: str = "") -> None:
                files = node.get("files")
                if not isinstance(files, dict):
                    return
                for name, meta in files.items():
                    if not isinstance(meta, dict):
                        continue
                    rel = f"{prefix}/{name}" if prefix else name
                    if "files" in meta:
                        walk(meta, rel)
                        continue
                    ext = Path(name).suffix.lower()
                    if ext not in _ICON_EXTS:
                        continue
                    sz = int(meta.get("size", 0) or 0)
                    if sz <= 0 or sz > _MAX_ICON_BYTES:
                        continue
                    score = _rank_icon_name(rel, sz)
                    if score[0] > 0:
                        candidates.append((score, rel, meta))

            walk(tree)
            if not candidates:
                return None

            _, best_rel, best_meta = max(candidates, key=lambda item: item[0])
            ext = Path(best_rel).suffix.lower() or ".png"

            if best_meta.get("unpacked"):
                unpacked = asar_path.parent / f"{asar_path.name}.unpacked" / best_rel
                if unpacked.is_file():
                    return unpacked
                return None

            offset = int(best_meta.get("offset", -1))
            size = int(best_meta.get("size", 0))
            if offset < 0 or size <= 0:
                return None
            base_offset = 8 + header_size
            f.seek(base_offset + offset)
            data = f.read(size)
            if len(data) != size:
                return None
    except (OSError, ValueError, struct.error, UnicodeDecodeError):
        return None

    try:
        cache.mkdir(parents=True, exist_ok=True)
        dest = cache / f"{key}{ext}"
        dest.write_bytes(data)
        return dest
    except OSError:
        return None


def _find_loose_portable_icon(app_dir: Path, stem: str) -> Path | None:
    """หาไฟล์รูปไอคอนที่วางไว้ใกล้ตัวโปรแกรม portable (เช่น VS Code tarball)."""
    direct_names = [f"{stem}.png", f"{stem}.svg", "icon.png", "icon.svg"]
    for name in direct_names:
        candidate = app_dir / name
        if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
            return candidate
    for sub in (
        app_dir / "resources" / "app" / "resources" / "linux",
        app_dir / "resources",
    ):
        if not sub.is_dir():
            continue
        try:
            images = [
                p
                for p in sub.iterdir()
                if p.is_file() and p.suffix.lower() in _ICON_EXTS
            ]
        except OSError:
            continue
        if images:
            return max(
                images,
                key=lambda p: _rank_icon_name(p.name, p.stat().st_size),
            )
    return None


def icon_from_portable_app(target: str | os.PathLike[str]) -> Path | None:
    """หาไอคอนของแอป portable (ไฟล์ binary หรือโฟลเดอร์แอป) จากไฟล์ใกล้เคียงหรือ `resources/app.asar`."""
    candidate = Path(str(target))
    if candidate.is_file():
        app_dir = candidate.parent
        stem = candidate.stem
    elif candidate.is_dir():
        app_dir = candidate
        stem = candidate.name
    else:
        return None

    # ข้ามโฟลเดอร์ระบบทั่วไป (/usr/bin, /bin, /usr/local/bin) ไม่ต้องไปค้น resources
    if app_dir.name in ("bin", "sbin") and len(app_dir.parts) <= 4:
        return None

    loose = _find_loose_portable_icon(app_dir, stem)
    if loose is not None:
        return loose

    asar = app_dir / "resources" / "app.asar"
    if asar.is_file():
        return icon_from_asar(asar)
    return None
