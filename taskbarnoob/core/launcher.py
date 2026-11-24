"""เปิด shortcut แบบข้าม OS (Linux / Windows / macOS) — Python ล้วน ไม่ผูก GUI."""

from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from .models import Group, Shortcut

_URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")


def is_uri_target(target: str) -> bool:
    """คืน True เมื่อ target เป็น URI scheme เช่น steam://, https://, com.epicgames.launcher://."""
    return bool(_URI_SCHEME_RE.match((target or "").strip()))


def is_target_missing(target: str) -> bool:
    """คืน True เมื่อ target เป็นไฟล์/โฟลเดอร์หรือคำสั่งที่ไม่มีอยู่จริง (ไม่นับ URI scheme)."""
    raw = (target or "").strip()
    if not raw or is_uri_target(raw):
        return False
    if Path(raw).expanduser().exists():
        return False
    if "/" not in raw and "\\" not in raw:
        return shutil.which(raw) is None
    return True


class LaunchError(Exception):
    """โยนเมื่อเปิด shortcut ไม่สำเร็จ."""


# env ที่ AppImage/PyInstaller ยัดเข้ามา — ห้ามส่งต่อให้โปรเซสลูก
# ไม่งั้นโปรแกรมระบบ (nemo ผ่าน xdg-open) จะไปโหลด Qt/glib ที่พกมาแล้วพังเงียบๆ
_STRIP_ENV = (
    "LD_LIBRARY_PATH",
    "LD_PRELOAD",
    "PYTHONHOME",
    "PYTHONPATH",
    "QT_PLUGIN_PATH",
    "APPDIR",
    "APPIMAGE",
    "ARGV0",
    "OWD",
)


def child_env() -> dict[str, str]:
    """สภาพแวดล้อมสะอาดสำหรับโปรเซสลูกที่เปิดโปรแกรมภายนอก."""
    env = dict(os.environ)
    for key in _STRIP_ENV:
        env.pop(key, None)
    return env


def _split_arguments(arguments: str) -> list[str]:
    if not arguments or not arguments.strip():
        return []
    return shlex.split(arguments, posix=sys.platform != "win32")


def _resolve_cwd(working_dir: str | None) -> str | None:
    if not working_dir:
        return None
    path = Path(working_dir)
    return str(path) if path.is_dir() else None


def _looks_runnable(path: Path) -> bool:
    """ไฟล์นี้รันเป็นโปรแกรมได้จริงไหม (ดู magic ไม่ดูแค่ +x).

    +x เชื่อไม่ได้บนไดรฟ์ NTFS/exFAT/Samba (ทุกไฟล์ +x หมด — mp3 ยัง +x เลย)
    เลยต้องดูเนื้อหา: ELF (รวม AppImage) · shebang · MZ (Windows exe).
    """
    try:
        with path.open("rb") as handle:
            head = handle.read(4)
    except OSError:
        return False
    if head[:4] == b"\x7fELF" or head[:2] == b"#!" or head[:2] == b"MZ":
        return os.access(path, os.X_OK)
    return False


def launch(shortcut: Shortcut) -> None:
    target = shortcut.target.strip()
    if not target:
        raise LaunchError("shortcut ไม่มี target")
    args = _split_arguments(shortcut.arguments)
    cwd = _resolve_cwd(shortcut.working_dir)

    if sys.platform == "win32":
        _launch_windows(target, args, cwd)
    else:
        _launch_linux(target, args, cwd)


def _launch_linux(target: str, args: list[str], cwd: str | None) -> None:
    env = child_env()
    try:
        # URI scheme (เช่น steam://rungameid/..., https://...) → เปิดผ่าน handler ของระบบ
        if is_uri_target(target):
            try:
                subprocess.Popen(
                    ["gio", "open", target], cwd=cwd, env=env, start_new_session=True
                )
            except OSError:
                subprocess.Popen(
                    ["xdg-open", target], cwd=cwd, env=env, start_new_session=True
                )
            return
        # .desktop file
        if target.endswith(".desktop"):
            subprocess.Popen(
                ["gio", "launch", target], cwd=cwd, env=env, start_new_session=True
            )
            return
        path = Path(target)
        # โฟลเดอร์ → เปิดด้วย file manager (gio ผ่าน session bus ปลอดภัยกว่า
        #  ไม่รับ env ที่พังจาก AppImage · xdg-open เป็น fallback)
        if path.is_dir():
            try:
                subprocess.Popen(
                    ["gio", "open", str(path)], cwd=cwd, env=env, start_new_session=True
                )
            except OSError:
                subprocess.Popen(
                    ["xdg-open", str(path)], cwd=cwd, env=env, start_new_session=True
                )
            return
        if path.is_file():
            # ไฟล์ที่รันได้จริง (ดู magic ไม่ดูแค่ +x — บน NTFS/exFAT ทุกไฟล์ +x
            #  หมดแม้แต่ mp3) → รันตรง ๆ · ไฟล์อื่น (เอกสาร/มีเดีย) → gio open
            #  (ห้ามสลับกัน: gio open บนไฟล์รันได้จะเปิดผิด — editor/disk-mounter)
            if _looks_runnable(path):
                subprocess.Popen(
                    [str(path), *args], cwd=cwd, env=env, start_new_session=True
                )
                return
            # ไฟล์เอกสารทั่วไป → เปิดด้วยโปรแกรม Default
            try:
                subprocess.Popen(
                    ["gio", "open", str(path)], cwd=cwd, env=env, start_new_session=True
                )
            except OSError:
                subprocess.Popen(
                    ["xdg-open", str(path)], cwd=cwd, env=env, start_new_session=True
                )
            return
        # ไม่มีไฟล์จริง (เช่น คำสั่งใน PATH: firefox, code) → รันตรง
        subprocess.Popen([target, *args], cwd=cwd, env=env, start_new_session=True)
    except OSError as exc:
        raise LaunchError(f"เปิด '{target}' ไม่สำเร็จ: {exc}") from exc


def _launch_windows(target: str, args: list[str], cwd: str | None) -> None:
    try:
        if not args and not cwd:
            os.startfile(target)  # type: ignore[attr-defined]
            return
        flags = getattr(subprocess, "DETACHED_PROCESS", 0)
        subprocess.Popen([target, *args], cwd=cwd, creationflags=flags)
    except OSError as exc:
        raise LaunchError(f"เปิด '{target}' ไม่สำเร็จ: {exc}") from exc


def reveal_path(path: Path) -> None:
    """เปิด file manager ชี้ไปที่ไฟล์/โฟลเดอร์ (ข้าม OS — Linux / Windows)."""
    if not path.exists():
        return
    parent = path.parent
    if not parent.exists():
        return
    env = child_env()
    try:
        if sys.platform == "win32":
            # แยก "/select," ออกเป็นคนละอาร์กิวเมนต์ — กันกรณี path มีช่องว่าง
            subprocess.Popen(
                ["explorer", "/select,", str(path)],
                env=env,
                start_new_session=True,
            )
        else:
            subprocess.Popen(
                ["xdg-open", str(parent)], env=env, start_new_session=True
            )
    except OSError:
        if sys.platform != "linux":
            return
        try:
            subprocess.Popen(
                ["gio", "open", str(parent)], env=env, start_new_session=True
            )
        except OSError:
            pass


def launch_all(group: Group) -> list[str]:
    errors: list[str] = []
    for item in group.items:
        try:
            launch(item)
        except LaunchError as exc:
            errors.append(f"{item.name}: {exc}")
    return errors
