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
    """เหมือน `_run` แต่ไม่สนใจ exit code — สำหรับ `explorer.exe`

    `explorer.exe` คืน 1 เสมอแม้ทำงานสำเร็จ (มันส่งคำขอให้ process เดิมแล้วจบ)
    ถ้าเช็ค exit code จะเด้ง error ทั้งที่เปิดหน้าต่างสำเร็จ
    """
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
    """ชื่อไฟล์ .lnk ต่อกลุ่ม = ชื่อกลุ่ม (Windows เอาชื่อไฟล์ไปแสดงบน taskbar/Start).

    ต้นฉบับ (Taskbar Groups) ใช้ชื่อกลุ่มตรงๆ เพื่อให้ปุ่มบน taskbar อ่านรู้เรื่อง
    ถ้าใช้ `taskbargroups-game.lnk` ปุ่มจะโชว์ชื่อยาวแบบนั้น
    """
    from .storage import safe_dir_name

    return f"{safe_dir_name(dir_name)}.lnk"


def launcher_id(dir_name: str) -> str:
    return lnk_name(dir_name)[: -len(".lnk")]


def aumid(dir_name: str) -> str:
    """AppUserModelID เฉพาะกลุ่ม.

    Windows รวมปุ่มบน taskbar ตาม AUMID — ถ้าทุกกลุ่มใช้ AUMID เดียวกับตัวแอป
    ปุ่มจะซ้อนกันเหลือปุ่มเดียว (ต้นฉบับเขียนว่า *"tricks Windows to think they are
    from different applications even though they are from the same .exe"*)
    """
    from .storage import safe_dir_name

    slug = safe_dir_name(dir_name).lower().replace(" ", "-")
    return f"{APP_ID}.group.{slug}"


def shortcuts_dir(config_dir: Path | str | None = None) -> Path:
    """โฟลเดอร์เก็บ `.lnk` ของกลุ่ม — อยู่ใน config ของแอป (portable เหมือนฝั่ง Linux)."""
    if config_dir is not None:
        root = Path(config_dir)
    else:
        from .paths import default_config_dir

        root = default_config_dir()
    return root / "shortcuts"


def start_menu_dir(
    env: dict | None = None, home: Path | str | None = None
) -> Path:
    """โฟลเดอร์ Start Menu ของผู้ใช้ — ใช้ตรวจว่า Windows เห็น .lnk ของเราเป็นแอปไหม."""
    return (
        _appdata(env, home)
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
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


def build_png_to_ico_ps_script(png: str | os.PathLike[str], ico: str | os.PathLike[str]) -> str:
    """สคริปต์ PowerShell แปลง .png → .ico (System.Drawing มีใน Windows ทุกเครื่อง)."""
    return (
        "Add-Type -AssemblyName System.Drawing; "
        f"$src = [System.Drawing.Image]::FromFile({_ps_quote(str(png))}); "
        "try { "
        "$bmp = New-Object System.Drawing.Bitmap($src, 256, 256); "
        "$hicon = $bmp.GetHicon(); "
        "$icon = [System.Drawing.Icon]::FromHandle($hicon); "
        f"$fs = [System.IO.File]::Create({_ps_quote(str(ico))}); "
        "try { $icon.Save($fs) } finally { $fs.Close() }; "
        "$bmp.Dispose() "
        "} finally { $src.Dispose() }"
    )


def png_to_ico(
    png: str | os.PathLike[str],
    runner: Runner = _run,
) -> Path | None:
    """แปลง .png → .ico (คืน path .ico หรือ None ถ้าแปลงไม่ได้)."""
    src = Path(png)
    if not src.is_file() or src.suffix.lower() != ".png":
        return None
    ico = src.with_suffix(".ico")
    try:
        runner(lnk_command(build_png_to_ico_ps_script(src, ico)))
    except WindowsError:
        return None
    return ico if ico.is_file() else None


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
        from . import win32_com

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
    except Exception as exc:  # COM ใช้ไม่ได้นอก Windows / ล้มเหลวแปลก ๆ
        raise WindowsError(f"สร้าง shortcut ไม่สำเร็จ: {exc}") from exc
    return dest


def read_lnk_target(link: str | os.PathLike[str]) -> str | None:
    """อ่าน TargetPath จาก .lnk (None ถ้าอ่านไม่ได้)."""
    try:
        from . import win32_com

        return win32_com.read_target(Path(link))
    except Exception:
        return None


def read_lnk_aumid(link: str | os.PathLike[str]) -> str | None:
    """อ่าน AppUserModelID จาก .lnk (ใช้บอกว่าไฟล์ใน User Pinned เป็นของเราหรือไม่)."""
    try:
        from . import win32_com

        return win32_com.read_aumid(Path(link))
    except Exception:
        return None


def read_lnk_arguments(link: str | os.PathLike[str]) -> str | None:
    """อ่าน Arguments ของ .lnk (เช่น `--open "Game"`)."""
    try:
        from . import win32_com

        return win32_com.read_arguments(Path(link))
    except Exception:
        return None


def repoint_pinned(old_dir_name: str, new_lnk: Path) -> bool:
    """หลังเปลี่ยนชื่อกลุ่ม — ให้ `.lnk` ที่ปักอยู่บน taskbar ชี้กลุ่มใหม่

    Windows ก๊อปไฟล์ไปไว้ใน `User Pinned` ตอนผู้ใช้ลากวาง ตัวนั้นจะยังชี้
    `--open "<ชื่อเก่า>"` เสมอ → กดแล้วเปิดกลุ่มที่ไม่มีแล้ว (flyout ว่างเปล่า)
    เราแก้ได้แค่ *เขียนทับไฟล์* (สร้าง pin ใหม่ไม่ได้ แต่แก้ของเดิมได้)
    """
    old_value = aumid(old_dir_name)
    directory = taskbar_pinned_dir()
    try:
        candidates = list(directory.glob("*.lnk"))
    except OSError:
        return False
    for path in candidates:
        if not path.is_file():
            continue
        try:
            if (read_lnk_aumid(path) or "") != old_value:
                continue
            # เขียนทับไฟล์ที่ Windows เป็นคนสร้าง (ชื่อไฟล์คงเดิม — Windows จัดการเอง)
            import shutil

            shutil.copy2(new_lnk, path)
            return True
        except OSError:
            continue
    return False


def set_process_aumid(dir_name: str) -> None:
    """ตั้ง AUMID ของโปรเซสให้ตรงกับ `.lnk` ของกลุ่ม (ตอนเปิด flyout).

    Windows เอาปุ่มบน taskbar มาแสดงรวมกับหน้าต่างที่กำลังรัน —
    ถ้าตรงกัน ปุ่มที่ปักไว้จะกลายเป็นปุ่มของกลุ่มนั้นทันที
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(aumid(dir_name))
    except (OSError, AttributeError):
        pass


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


def reveal_in_explorer(
    path: str | os.PathLike[str],
    runner: Runner | None = None,
) -> None:
    """เปิด Explorer โดยเลือกไฟล์ไว้ (ให้ผู้ใช้ลากไปวางบน taskbar ได้เลย).

    ต้องส่งเป็น string เดี่ยว ไม่ใช่ list — เพราะ `explorer /select,"path with spaces"`
    ต้องการ quote ติดกับพาธ ถ้าเป็น list Python จะ escape quote ให้แล้ว Explorer อ่านไม่ออก
    (path ที่มีช่องว่างเช่น ...\\My Tools\\... จะพัดไปเปิดโฟลเดอร์ Documents แทน)
    """
    target = os.path.normpath(str(path))
    try:
        (runner or _run_lenient)(f'explorer /select,"{target}"')
    except OSError as exc:
        raise WindowsError(str(exc)) from exc


def pin_to_taskbar(
    source_lnk: str | os.PathLike[str],
    env: dict | None = None,
    home: Path | str | None = None,
    runner: Runner = _run_lenient,
) -> Path:
    """Windows 11 ปิดการปัก taskbar จากโปรแกรม — เปิด Explorer ให้ผู้ใช้คลิกขวาเอง.

    คืน path ของ .lnk ที่เปิดให้ (ผู้ใช้คลิกขวา → Pin to taskbar ต่อเอง)
    """
    source = Path(source_lnk)
    reveal_in_explorer(source, runner=runner)
    return source


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
