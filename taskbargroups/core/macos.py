"""macOS backend แบบ portable (best-effort).

- launcher ต่อกลุ่ม = ไฟล์ `.command` (ดับเบิลคลิกแล้วรัน `exe --open Group` ผ่าน Terminal)
- ปัก Dock = เขียน `com.apple.dock persistent-apps` ผ่าน `defaults` + `killall Dock`
- global hotkey: ยังไม่รองรับ (ต้องขอ Accessibility + EventHotKey — โยนข้อความบอก)
- ทุกฟังก์ชันรับ `runner`/`home` ได้ เพื่อเทสต์บน Linux

⚠️ UNTESTED on real hardware — โค้ดชุดนี้ยังไม่เคยรันบนเครื่อง Mac จริง (ทีมไม่มีเครื่อง)
   เขียนไว้เป็น best-effort ให้ผู้ที่ต้องการ fork แล้ว build/ทดสอบเองได้ · ยังไม่รับประกัน
"""

from __future__ import annotations

import os
import plistlib
import stat
import subprocess
from pathlib import Path
from typing import Callable, Sequence

APP_ID = "taskbargroups"

Runner = Callable[[Sequence[str]], str]


class MacOSError(OSError):
    """โยนเมื่อคำสั่ง macOS ไม่สำเร็จ (เป็น OSError เพื่อให้ GUI จับแบบเดิมได้)."""


def _run(command: Sequence[str]) -> str:
    try:
        result = subprocess.run(list(command), capture_output=True, text=True)
    except OSError as exc:
        raise MacOSError(str(exc)) from exc
    if result.returncode != 0:
        raise MacOSError(result.stderr.strip() or f"คำสั่งล้มเหลว: {' '.join(command)}")
    return result.stdout


def command_name(dir_name: str) -> str:
    """ชื่อไฟล์ .command ต่อกลุ่ม."""
    from .storage import safe_dir_name

    slug = safe_dir_name(dir_name).lower().replace(" ", "-")
    return f"{APP_ID}-{slug}.command"


def launcher_id(dir_name: str) -> str:
    return command_name(dir_name)[: -len(".command")]


def launchers_dir(home: Path | str | None = None) -> Path:
    """โฟลเดอร์เก็บ .command ของกลุ่ม (portable: ข้าง config ถ้าเขียนได้)."""
    return (Path(home) if home is not None else Path.home()) / "Applications" / "TaskbarNoob"


def build_command_script(exe: str | os.PathLike[str], dir_name: str) -> str:
    return f'#!/bin/sh\nexec "{exe}" --open "{dir_name}"\n'


def install_command_launcher(
    exe: str | os.PathLike[str],
    dir_name: str,
    target_dir: Path | str | None = None,
) -> Path:
    """สร้างไฟล์ .command เปิดกลุ่ม (+x) คืน path."""
    directory = Path(target_dir) if target_dir is not None else launchers_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / command_name(dir_name)
        path.write_text(build_command_script(exe, dir_name), encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError as exc:
        raise MacOSError(str(exc)) from exc
    return path


def remove_command_launcher(
    dir_name: str, target_dir: Path | str | None = None
) -> bool:
    directory = Path(target_dir) if target_dir is not None else launchers_dir()
    path = directory / command_name(dir_name)
    if not path.is_file():
        return False
    try:
        path.unlink()
    except OSError as exc:
        raise MacOSError(str(exc)) from exc
    return True


def _dock_plist_command(*args: str) -> list[str]:
    return ["defaults", *args]


def read_dock_apps(runner: Runner = _run) -> list:
    """อ่าน persistent-apps ของ Dock (คืน list ดิบ — [] ถ้าอ่านไม่ได้)."""
    try:
        out = runner(
            _dock_plist_command("read", "com.apple.dock", "persistent-apps")
        )
    except MacOSError:
        return []
    try:
        return plistlib.loads(out.encode("utf-8", "replace"))
    except (ValueError, plistlib.InvalidFileException):
        return []


def _tile_path(tile: dict) -> str:
    try:
        return str(tile["tile-data"]["file-data"]["_CFURLString"])
    except (KeyError, TypeError):
        return ""


def dock_app_paths(runner: Runner = _run) -> set[str]:
    return {_tile_path(tile) for tile in read_dock_apps(runner) if isinstance(tile, dict)}


def _refresh_dock(runner: Runner = _run) -> None:
    try:
        runner(["killall", "Dock"])
    except MacOSError:
        pass


def pin_to_dock(app_path: str | os.PathLike[str], runner: Runner = _run) -> None:
    """ปักแอป/ไฟล์ลง Dock ท้ายสุด (best-effort)."""
    from urllib.request import pathname2url

    url = "file://" + pathname2url(str(app_path))
    tile = {"tile-data": {"file-data": {"_CFURLString": url, "_CFURLStringType": 0}}}
    apps = [t for t in read_dock_apps(runner) if isinstance(t, dict)]
    if url in {_tile_path(t) for t in apps}:
        return
    apps.append(tile)
    payload = plistlib.dumps(apps, fmt=plistlib.FMT_XML).decode("utf-8")
    runner(["defaults", "write", "com.apple.dock", "persistent-apps", payload])
    _refresh_dock(runner)


def unpin_from_dock(app_path: str | os.PathLike[str], runner: Runner = _run) -> bool:
    from urllib.request import pathname2url

    url = "file://" + pathname2url(str(app_path))
    apps = [t for t in read_dock_apps(runner) if isinstance(t, dict)]
    kept = [t for t in apps if _tile_path(t) != url]
    if len(kept) == len(apps):
        return False
    payload = plistlib.dumps(kept, fmt=plistlib.FMT_XML).decode("utf-8")
    runner(["defaults", "write", "com.apple.dock", "persistent-apps", payload])
    _refresh_dock(runner)
    return True
