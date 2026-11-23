"""Windows `.lnk` launcher creation, inspection, paths, and shell icon notifications."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

Runner = Callable[[Sequence[str] | str], str]


class WindowsError(OSError):
    """โยนเมื่อคำสั่ง Windows ไม่สำเร็จ (เป็น OSError เพื่อให้ GUI จับแบบเดิมได้)."""


def _run(command: Sequence[str] | str) -> str:
    """รันคำสั่ง Windows. รับ string เดี่ยวได้ (ต้องการตอน quoting สำคัญ เช่น explorer /select)."""
    try:
        if isinstance(command, str):
            result = subprocess.run(command, capture_output=True, text=True)
        else:
            result = subprocess.run(list(command), capture_output=True, text=True)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    if result.returncode != 0:
        raise WindowsError(result.stderr.strip() or f"คำสั่งล้มเหลว: {command}")
    return result.stdout


def _run_lenient(command: Sequence[str] | str) -> str:
    """เหมือน `_run` แต่ไม่สนใจ exit code — สำหรับ `explorer.exe`."""
    try:
        if isinstance(command, str):
            subprocess.run(command, capture_output=True, text=True)
        else:
            subprocess.run(list(command), capture_output=True, text=True)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    return ""


def _home(home: Path | str | None = None) -> Path:
    return Path(home) if home is not None else Path.home()


def _appdata(env: dict | None = None, home: Path | str | None = None) -> Path:
    source = dict(os.environ) if env is None else dict(env)
    roaming = source.get("APPDATA")
    if roaming:
        return Path(roaming)
    return _home(home) / "AppData" / "Roaming"


def lnk_name(dir_name: str) -> str:
    """ชื่อไฟล์ .lnk ต่อกลุ่ม = ชื่อกลุ่ม (Windows เอาชื่อไฟล์ไปแสดงบน taskbar/Start)."""
    from ...storage import safe_dir_name

    return f"{safe_dir_name(dir_name)}.lnk"


def launcher_id(dir_name: str) -> str:
    return lnk_name(dir_name)[: -len(".lnk")]


def notify_icon_changed(path: str | os.PathLike[str] | None = None) -> None:
    """แจ้ง Windows ให้รีเฟรช icon cache (SHChangeNotify)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        SHCNE_UPDATEITEM = 0x00002000
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_PATHW = 0x0005
        SHCNF_FLUSHNOWAIT = 0x2000
        shell32 = ctypes.windll.shell32
        if path:
            shell32.SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATHW, str(path), None)
        else:
            shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_FLUSHNOWAIT, None, None)
    except Exception:
        pass


def shortcuts_dir(config_dir: Path | str | None = None) -> Path:
    """โฟลเดอร์เก็บ `.lnk` ของกลุ่ม — อยู่ใน config ของแอป (portable เหมือนฝั่ง Linux)."""
    if config_dir is not None:
        root = Path(config_dir)
    else:
        from ...paths import default_config_dir

        root = default_config_dir()
    return root / "shortcuts"


def start_menu_dir(
    env: dict | None = None, home: Path | str | None = None
) -> Path:
    """โฟลเดอร์ Start Menu ของผู้ใช้."""
    return (
        _appdata(env, home)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
    )


def create_lnk(
    link: str | os.PathLike[str],
    target: str | os.PathLike[str],
    arguments: str = "",
    workdir: str | os.PathLike[str] = "",
    icon_location: str | os.PathLike[str] = "",
    aumid_value: str = "",
    description: str = "",
) -> Path:
    """สร้าง `.lnk` ผ่าน COM `IShellLinkW` (ตั้ง AUMID ได้ — PowerShell ตั้งไม่ได้)."""
    dest = Path(link)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    try:
        from . import com as win32_com

        win32_com.write_lnk(
            dest,
            str(target),
            arguments=arguments,
            workdir=str(workdir),
            icon_location=str(icon_location),
            description=description,
            aumid=aumid_value,
        )
    except OSError:
        raise
    except Exception as exc:
        raise WindowsError(f"สร้าง shortcut ไม่สำเร็จ: {exc}") from exc
    return dest


def read_lnk_target(link: str | os.PathLike[str]) -> str | None:
    """อ่าน TargetPath จาก .lnk (None ถ้าอ่านไม่ได้)."""
    try:
        from . import com as win32_com

        return win32_com.read_target(Path(link))
    except Exception:
        return None


def read_lnk_aumid(link: str | os.PathLike[str]) -> str | None:
    """อ่าน AppUserModelID จาก .lnk (ใช้บอกว่าไฟล์ใน User Pinned เป็นของเราหรือไม่)."""
    try:
        from . import com as win32_com

        return win32_com.read_aumid(Path(link))
    except Exception:
        return None


def read_lnk_arguments(link: str | os.PathLike[str]) -> str | None:
    """อ่าน Arguments ของ .lnk (เช่น `--open "Game"`)."""
    try:
        from . import com as win32_com

        return win32_com.read_arguments(Path(link))
    except Exception:
        return None
