"""Windows backend แบบ portable (Python ล้วน ไม่ต้องลงอะไรเพิ่ม).

หลักการ:
- ไม่ใช้ pywin32 — สร้าง/อ่าน `.lnk` ผ่าน PowerShell (`WScript.Shell` มีใน Windows ทุกเครื่อง)
- ปัก Taskbar = คัดลอก `.lnk` เข้าโฟลเดอร์ User Pinned (best-effort — Win11 อาจต้องคลิกขวา Pin เอง)
- global hotkey = `RegisterHotKey` ผ่าน ctypes (GUI เป็นคน hook native event)
- ทุกฟังก์ชันรับ `runner`/`env`/`home` ได้ เพื่อให้เทสต์บน Linux ได้โดยไม่ต้องมี Windows
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

APP_ID = "taskbargroups"

Runner = Callable[[Sequence[str]], str]


class WindowsError(OSError):
    """โยนเมื่อคำสั่ง Windows ไม่สำเร็จ (เป็น OSError เพื่อให้ GUI จับแบบเดิมได้)."""


def _run(command: Sequence[str]) -> str:
    try:
        result = subprocess.run(list(command), capture_output=True, text=True)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    if result.returncode != 0:
        raise WindowsError(result.stderr.strip() or f"คำสั่งล้มเหลว: {' '.join(command)}")
    return result.stdout


def _home(home: Path | str | None = None) -> Path:
    return Path(home) if home is not None else Path.home()


def _appdata(env: dict | None = None, home: Path | str | None = None) -> Path:
    source = dict(os.environ) if env is None else dict(env)
    roaming = source.get("APPDATA")
    if roaming:
        return Path(roaming)
    return _home(home) / "AppData" / "Roaming"


def lnk_name(dir_name: str) -> str:
    """ชื่อไฟล์ .lnk ต่อกลุ่ม (slug เดียวกับ .desktop ฝั่ง Linux)."""
    from .storage import safe_dir_name

    slug = safe_dir_name(dir_name).lower().replace(" ", "-")
    return f"{APP_ID}-{slug}.lnk"


def launcher_id(dir_name: str) -> str:
    return lnk_name(dir_name)[: -len(".lnk")]


def start_menu_dir(
    env: dict | None = None, home: Path | str | None = None
) -> Path:
    """โฟลเดอร์ Start Menu ไว้เก็บ .lnk ของกลุ่ม."""
    return (
        _appdata(env, home)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "TaskbarNoob"
    )


def taskbar_pinned_dir(
    env: dict | None = None, home: Path | str | None = None
) -> Path:
    """โฟลเดอร์ User Pinned ของ taskbar (ปักโดยคัดลอก .lnk มาวาง)."""
    return (
        _appdata(env, home)
        / "Microsoft"
        / "Internet Explorer"
        / "Quick Launch"
        / "User Pinned"
        / "TaskBar"
    )


def _ps_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_lnk_ps_script(
    link: str | os.PathLike[str],
    target: str | os.PathLike[str],
    arguments: str = "",
    workdir: str | os.PathLike[str] = "",
    icon_location: str | os.PathLike[str] = "",
) -> str:
    """สคริปต์ PowerShell สร้าง/อัปเดต .lnk (คืน string เดียวพร้อมรัน)."""
    lines = [
        "$ws = New-Object -ComObject WScript.Shell",
        f"$sc = $ws.CreateShortcut({_ps_quote(str(link))})",
        f"$sc.TargetPath = {_ps_quote(str(target))}",
        f"$sc.Arguments = {_ps_quote(arguments)}",
    ]
    if workdir:
        lines.append(f"$sc.WorkingDirectory = {_ps_quote(str(workdir))}")
    if icon_location:
        lines.append(f"$sc.IconLocation = {_ps_quote(str(icon_location))}")
    lines.append("$sc.Save()")
    return "; ".join(lines)


def build_read_lnk_ps_script(link: str | os.PathLike[str]) -> str:
    return (
        "(New-Object -ComObject WScript.Shell)"
        f".CreateShortcut({_ps_quote(str(link))}).TargetPath"
    )


def lnk_command(script: str) -> list[str]:
    return ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]


def create_lnk(
    link: str | os.PathLike[str],
    target: str | os.PathLike[str],
    arguments: str = "",
    workdir: str | os.PathLike[str] = "",
    icon_location: str | os.PathLike[str] = "",
    runner: Runner = _run,
) -> Path:
    """สร้าง .lnk ของกลุ่ม คืน path (สร้างโฟลเดอร์แม่ให้ด้วย)."""
    dest = Path(link)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    runner(
        lnk_command(
            build_lnk_ps_script(link, target, arguments, workdir, icon_location)
        )
    )
    return dest


def read_lnk_target(
    link: str | os.PathLike[str], runner: Runner = _run
) -> str | None:
    """อ่าน TargetPath จาก .lnk (None ถ้าอ่านไม่ได้)."""
    try:
        out = runner(lnk_command(build_read_lnk_ps_script(link)))
    except WindowsError:
        return None
    text = out.strip()
    return text or None


def pinned_lnk_path(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
) -> Path:
    return taskbar_pinned_dir(env, home) / lnk_name(dir_name)


def is_pinned(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
) -> bool:
    return pinned_lnk_path(dir_name, env, home).is_file()


def pin_to_taskbar(
    source_lnk: str | os.PathLike[str],
    env: dict | None = None,
    home: Path | str | None = None,
) -> Path:
    """ปัก .lnk ลง taskbar (คัดลอกเข้า User Pinned). คืน path ปลายทาง."""
    import shutil

    dest = taskbar_pinned_dir(env, home) / Path(source_lnk).name
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_lnk, dest)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    return dest


def unpin_from_taskbar(
    dir_name: str,
    env: dict | None = None,
    home: Path | str | None = None,
) -> bool:
    name = str(dir_name)
    if name.lower().endswith(".lnk"):
        dest = taskbar_pinned_dir(env, home) / Path(name).name
    else:
        dest = pinned_lnk_path(name, env, home)
    if not dest.is_file():
        # เผื่อชื่อไม่ตรง (ผู้ใช้ปักเอง) — กวาดไฟล์ taskbargroups-*.lnk ที่ชี้ exe เรา
        return False
    try:
        dest.unlink()
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    return True


# --- global hotkey (RegisterHotKey) ---

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008

_MODIFIER_MAP = {
    "alt": MOD_ALT,
    "control": MOD_CONTROL,
    "ctrl": MOD_CONTROL,
    "shift": MOD_SHIFT,
    "super": MOD_WIN,
    "meta": MOD_WIN,
    "win": MOD_WIN,
}


def parse_hotkey_binding(binding: str) -> tuple[int, int]:
    """แปลง `<Control><Alt>t` → (modifiers, vk).

    vk มาจากตัวอักษรเดี่ยว (A–Z/0–9 → รหัส virtual-key ตรงตัว) · ถ้าไม่ใช่รูปแบบนี้
    ให้โยน WindowsError (GUI โชว์ให้ผู้ใช้เลือกใหม่).
    """
    text = (binding or "").strip()
    modifiers = 0
    while text.startswith("<"):
        end = text.find(">")
        if end == -1:
            break
        token = text[1:end].strip().lower()
        text = text[end + 1 :]
        modifiers |= _MODIFIER_MAP.get(token, 0)
    key = text.strip()
    if len(key) == 1 and ("a" <= key.lower() <= "z" or "0" <= key <= "9"):
        return modifiers, ord(key.upper())
    raise WindowsError(f"ปุ่มลัดใช้บน Windows ไม่ได้: {binding!r}")


def _user32():
    import ctypes

    return ctypes.WinDLL("user32", use_last_error=True)


def register_hotkey(hotkey_id: int, hwnd: int, modifiers: int, vk: int) -> None:
    """ลงทะเบียน global hotkey กับ Windows (โยน WindowsError ถ้าไม่สำเร็จ)."""
    if sys.platform != "win32":
        raise WindowsError("ฟังก์ชันนี้ใช้ได้บน Windows เท่านั้น")
    try:
        ok = _user32().RegisterHotKey(hwnd, hotkey_id, modifiers, vk)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    if not ok:
        raise WindowsError("ลงทะเบียนปุ่มลัดไม่สำเร็จ (อาจชนกับโปรแกรมอื่น)")


def unregister_hotkey(hotkey_id: int, hwnd: int) -> None:
    if sys.platform != "win32":
        return
    try:
        _user32().UnregisterHotKey(hwnd, hotkey_id)
    except OSError:
        pass
