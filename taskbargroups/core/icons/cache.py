"""แคชไฟล์ไอคอนและค่าคงที่พื้นฐาน (Python ล้วน ข้าม OS)."""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path

ICONS_DIR_NAME = "icons"
PROVIDER_ICON_CACHE_DIRNAME = "provider-icons-v3"

IMAGE_SUFFIXES = {".png", ".svg", ".jpg", ".jpeg", ".ico", ".bmp", ".xpm", ".gif"}

_SAFE_STEM = re.compile(r"[^A-Za-z0-9._-]+")


class IconError(Exception):
    """โยนเมื่อคัดลอกไฟล์ไอคอนไม่สำเร็จ."""


def is_image_file(path: str | os.PathLike[str]) -> bool:
    candidate = Path(path)
    return candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES


def safe_stem(name: str) -> str:
    """ทำชื่อให้ปลอดภัยพอใช้เป็นชื่อไฟล์ไอคอน."""
    stem = _SAFE_STEM.sub("_", (name or "").strip())
    return stem.strip("._") or "icon"


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
