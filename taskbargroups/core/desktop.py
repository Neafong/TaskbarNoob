"""สร้าง/ติดตั้ง .desktop launcher ต่อกลุ่ม (Linux panel/menu integration)."""

from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path

from .models import MAX_ITEM_NAME_LEN, Group, Shortcut
from .paths import app_dir
from .storage import ConfigStore, safe_dir_name

APP_ID = "taskbargroups"
FALLBACK_ICON = "applications-utilities"


def data_home() -> Path:
    env = os.environ.get("XDG_DATA_HOME")
    return Path(env) if env else Path.home() / ".local" / "share"


def applications_dir() -> Path:
    return data_home() / "applications"


def icons_home() -> Path:
    """รากของ user icon theme (hicolor) — อยู่บนดิสก์รากเสมอ ไม่หายตอน boot."""
    return data_home() / "icons"


def desktop_file_name(dir_name: str) -> str:
    slug = safe_dir_name(dir_name).lower().replace(" ", "-")
    return f"{APP_ID}-{slug}.desktop"


def launcher_id(dir_name: str) -> str:
    """ชื่อไอคอน/handle ของ launcher (ไม่มี `.desktop`)."""
    return desktop_file_name(dir_name)[: -len(".desktop")]



def _icon_subdir(ext: str) -> str:
    return "scalable" if ext == ".svg" else "256x256"


def install_launcher_icon(
    dir_name: str, source: str | os.PathLike[str], icons_root: Path | None = None
) -> str:
    """ติดตั้งไอคอนกลุ่มลง user icon theme (hicolor) แล้วคืนชื่อไอคอน.

    เก็บสำเนาไว้บนดิสก์รากเสมอ เพื่อให้ panel/Menu หาไอคอนเจอตอน boot
    แม้ drive ที่เก็บ config (เช่น USB) ยัง mount ไม่เสร็จ
    """
    root = Path(icons_root) if icons_root is not None else icons_home()
    src = Path(source)
    ext = src.suffix.lower() or ".png"
    name = launcher_id(dir_name)
    remove_launcher_icon(dir_name, root)
    dest_dir = root / "hicolor" / _icon_subdir(ext) / "apps"
    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest_dir / f"{name}{ext}")
    return name


def remove_launcher_icon(dir_name: str, icons_root: Path | None = None) -> bool:
    root = Path(icons_root) if icons_root is not None else icons_home()
    name = launcher_id(dir_name)
    removed = False
    for sub in ("scalable", "256x256"):
        for old in (root / "hicolor" / sub / "apps").glob(f"{name}.*"):
            try:
                old.unlink()
                removed = True
            except OSError:
                pass
    return removed


def build_exec(dir_name: str, python: str | None = None) -> str:
    """สร้างบรรทัด Exec ที่ใช้เปิด flyout ของกลุ่ม.

    รองรับ 3 โหมด: รันจาก source (`python -m taskbargroups`), รันจาก AppImage
    (`$APPIMAGE --open ...`) และ frozen exe (binary ตรงๆ)
    """
    if python:
        return f'"{python}" -m {APP_ID} --open "{dir_name}"'
    appimage = os.environ.get("APPIMAGE")
    if appimage:
        return f'"{appimage}" --open "{dir_name}"'
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --open "{dir_name}"'
    return f'"{sys.executable}" -m {APP_ID} --open "{dir_name}"'


def build_desktop_entry(
    group: Group,
    store: ConfigStore,
    dir_name: str,
    python: str | None = None,
    icon_name: str | None = None,
) -> str:
    if icon_name:
        icon = icon_name
    else:
        icon_file = store.resolve_relative(dir_name, group.icon)
        icon = str(icon_file) if icon_file is not None else FALLBACK_ICON
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        "Version=1.0",
        f"Name={group.name}",
        "Comment=TaskbarNoob group",
        f"Exec={build_exec(dir_name, python)}",
        f"Path={app_dir()}",
        f"Icon={icon}",
        "Terminal=false",
        "Categories=Utility;",
        "StartupNotify=false",
        "",
    ]
    return "\n".join(lines)


def install_launcher(
    group: Group,
    store: ConfigStore,
    dir_name: str,
    target_dir: Path | None = None,
    python: str | None = None,
    icons_root: Path | None = None,
) -> Path:
    directory = Path(target_dir) if target_dir is not None else applications_dir()
    directory.mkdir(parents=True, exist_ok=True)

    icon_name = None
    source = store.resolve_relative(dir_name, group.icon)
    if source is not None:
        try:
            icon_name = install_launcher_icon(dir_name, source, icons_root)
        except OSError:
            icon_name = None

    path = directory / desktop_file_name(dir_name)
    path.write_text(
        build_desktop_entry(group, store, dir_name, python, icon_name=icon_name),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def remove_launcher(
    dir_name: str,
    target_dir: Path | None = None,
    icons_root: Path | None = None,
) -> bool:
    directory = Path(target_dir) if target_dir is not None else applications_dir()
    path = directory / desktop_file_name(dir_name)
    existed = path.exists()
    if existed:
        try:
            path.unlink()
        except OSError:
            return False
    remove_launcher_icon(dir_name, icons_root)
    return existed


def read_desktop_name(path: str | os.PathLike[str]) -> str | None:
    candidate = Path(path)
    if not candidate.is_file():
        return None
    try:
        for line in candidate.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Name="):
                return line[len("Name=") :].strip() or None
    except OSError:
        return None
    return None


def shortcut_from_path(
    path: str | os.PathLike[str], max_len: int = MAX_ITEM_NAME_LEN
) -> Shortcut | None:
    """สร้าง Shortcut จากไฟล์ที่ลากมาวาง (รองรับ .desktop).

    .desktop → ใช้ Name= เป็นชื่อ และ target คือตัวไฟล์นั้น
    ไฟล์อื่น → ใช้ชื่อไฟล์ (ไม่มีนามสกุล)
    """
    p = Path(str(path)).expanduser()
    if not p.exists():
        return None
    if p.suffix.lower() == ".desktop":
        name = read_desktop_name(p) or p.stem
        target = str(p)
    else:
        name = p.stem or p.name
        target = str(p)
    name = (name.strip() or p.stem or "icon")[:MAX_ITEM_NAME_LEN]
    return Shortcut(name=name, target=target)
