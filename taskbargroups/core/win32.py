"""Windows backend แบบ portable (Python ล้วน ไม่ต้องลงอะไรเพิ่ม).

หลักการ:
- ไม่ใช้ pywin32 — สร้าง/อ่าน `.lnk` ผ่าน PowerShell (`WScript.Shell` มีใน Windows ทุกเครื่อง)
- ปัก Taskbar = คัดลอก `.lnk` เข้าโฟลเดอร์ User Pinned (best-effort — Win11 อาจต้องคลิกขวา Pin เอง)
- global hotkey = `RegisterHotKey` ผ่าน ctypes (GUI เป็นคน hook native event)
- ทุกฟังก์ชันรับ `runner`/`env`/`home` ได้ เพื่อให้เทสต์บน Linux ได้โดยไม่ต้องมี Windows
"""

from __future__ import annotations

import os
import struct
import subprocess
import sys
import zlib
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


def notify_icon_changed(path: str | os.PathLike[str] | None = None) -> None:
    """แจ้ง Windows ให้รีเฟรช icon cache (SHChangeNotify).

    ใช้หลังเปลี่ยน .ico/.lnk แล้ว Windows ยังโชว์ไอคอนเก่า (cache ตาม path).
    ถ้า path ให้มา → แจ้งเฉพาะไฟล์นั้น (SHCNE_UPDATEITEM) ไม่งั้นแจ้งทั้งระบบ (SHCNE_ASSOCCHANGED).
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        SHCNE_UPDATEITEM = 0x00002000
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_PATHW = 0x0005
        SHCNF_FLUSH = 0x1000
        SHCNF_FLUSHNOWAIT = 0x2000
        shell32 = ctypes.windll.shell32
        if path:
            shell32.SHChangeNotify(SHCNE_UPDATEITEM, SHCNF_PATHW, str(path), None)
        else:
            shell32.SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_FLUSHNOWAIT, None, None)
    except Exception:
        pass


def aumid(dir_name: str) -> str:
    """AppUserModelID เฉพาะกลุ่ม.

    Windows รวมปุ่มบน taskbar ตาม AUMID — ถ้าทุกกลุ่มใช้ AUMID เดียวกับตัวแอป
    ปุ่มจะซ้อนกันเหลือปุ่มเดียว
    (ต้นฉบับเขียนว่า *"tricks Windows to think they are from different applications even though they are from the same .exe"*)
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
    """สคริปต์ PowerShell แปลง .png → .ico (System.Drawing มีใน Windows ทุกเครื่อง).

    .. deprecated:: 0.3.0
        ใช้ :func:`png_to_ico` แทน — pure Python, lossless, ไม่ต้อง spawn PowerShell
    """
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


def _png_decode(png: bytes) -> tuple[int, int, bytearray] | None:
    """ถอดรหัส PNG (RGBA8/RGB8/GA8/Gray8, no interlace) → (w, h, pixels RGBA). คืน None ถ้าไม่รองรับ."""
    if not png or png[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    w = h = 0
    bit_depth = color_type = 0
    idat = bytearray()
    while pos < len(png):
        if pos + 12 > len(png):
            return None
        length = struct.unpack(">I", png[pos:pos + 4])[0]
        chunk = png[pos + 4:pos + 8]
        data = png[pos + 8:pos + 8 + length]
        if chunk == b"IHDR":
            w, h, bit_depth, color_type, comp, filt, inter = struct.unpack(
                ">IIBBBBB", data[:13]
            )
            if bit_depth != 8 or inter != 0:
                return None
            if color_type not in (2, 6, 4, 0):
                return None
        elif chunk == b"IDAT":
            idat.extend(data)
        elif chunk == b"IEND":
            break
        pos += 12 + length
    if w <= 0 or h <= 0 or not idat:
        return None
    try:
        raw = zlib.decompress(bytes(idat))
    except zlib.error:
        return None
    if color_type == 6:
        channels = 4
    elif color_type == 2:
        channels = 3
    elif color_type == 4:
        channels = 2
    else:
        channels = 1
    stride = w * channels
    pixels = bytearray(w * h * 4)
    prev_row = bytearray(stride)
    row_size = stride + 1
    for y in range(h):
        if y * row_size + row_size > len(raw):
            return None
        filt = raw[y * row_size]
        row = bytearray(raw[y * row_size + 1:y * row_size + 1 + stride])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            above = prev_row[x]
            above_left = prev_row[x - channels] if x >= channels else 0
            if filt == 0:
                pass
            elif filt == 1:
                row[x] = (row[x] + left) & 0xFF
            elif filt == 2:
                row[x] = (row[x] + above) & 0xFF
            elif filt == 3:
                row[x] = (row[x] + ((left + above) // 2)) & 0xFF
            elif filt == 4:
                p = left + above - above_left
                pa = abs(p - left)
                pb = abs(p - above)
                pc = abs(p - above_left)
                if pa <= pb and pa <= pc:
                    predictor = left
                elif pb <= pc:
                    predictor = above
                else:
                    predictor = above_left
                row[x] = (row[x] + predictor) & 0xFF
            else:
                return None
        for x in range(w):
            base = x * channels
            out_base = (y * w + x) * 4
            if channels == 4:
                pixels[out_base:out_base + 4] = row[base:base + 4]
            elif channels == 3:
                pixels[out_base] = row[base]
                pixels[out_base + 1] = row[base + 1]
                pixels[out_base + 2] = row[base + 2]
                pixels[out_base + 3] = 255
            elif channels == 2:
                pixels[out_base] = row[base]
                pixels[out_base + 1] = row[base]
                pixels[out_base + 2] = row[base]
                pixels[out_base + 3] = row[base + 1]
            else:
                v = row[base]
                pixels[out_base] = v
                pixels[out_base + 1] = v
                pixels[out_base + 2] = v
                pixels[out_base + 3] = 255
        prev_row = row
    return w, h, pixels


def _png_encode(w: int, h: int, pixels: bytearray) -> bytes:
    """เข้ารหัส RGBA pixels → PNG bytes."""
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)
        raw.extend(pixels[y * stride:(y + 1) * stride])
    compressed = zlib.compress(bytes(raw), 9)
    out = b"\x89PNG\r\n\x1a\n"
    out += struct.pack(">I", 13) + b"IHDR" + ihdr
    out += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    out += struct.pack(">I", len(compressed)) + b"IDAT" + compressed
    out += struct.pack(">I", zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF)
    out += struct.pack(">I", 0) + b"IEND"
    out += struct.pack(">I", zlib.crc32(b"IEND") & 0xFFFFFFFF)
    return out


def _resize_rgba(
    pixels: bytearray, src_w: int, src_h: int, dst_w: int, dst_h: int
) -> bytearray:
    """ย่อ/ขยาย RGBA pixels ด้วย premultiplied-alpha area filter (ลดขอบหยักบนไอคอนวงกลม)."""
    if src_w == dst_w and src_h == dst_h:
        return bytearray(pixels)
    result = bytearray(dst_w * dst_h * 4)
    x_ratio = src_w / dst_w
    y_ratio = src_h / dst_h

    # ย่อขนาด → area/box filter แบบ premultiplied alpha (เฉลี่ยทุกพิกเซลในพื้นที่จริง)
    if dst_w <= src_w and dst_h <= src_h:
        import math

        for dy in range(dst_h):
            sy0 = dy * y_ratio
            sy1 = (dy + 1) * y_ratio
            iy0 = int(sy0)
            iy1 = min(src_h, math.ceil(sy1))
            y_weights = [
                (sy, min(sy + 1.0, sy1) - max(float(sy), sy0))
                for sy in range(iy0, iy1)
            ]
            row_dst = dy * dst_w
            for dx in range(dst_w):
                sx0 = dx * x_ratio
                sx1 = (dx + 1) * x_ratio
                ix0 = int(sx0)
                ix1 = min(src_w, math.ceil(sx1))
                r_sum = g_sum = b_sum = a_sum = w_sum = 0.0
                for sy, wy in y_weights:
                    row_src = sy * src_w
                    for sx in range(ix0, ix1):
                        wx = min(sx + 1.0, sx1) - max(float(sx), sx0)
                        w = wx * wy
                        idx = (row_src + sx) * 4
                        a = pixels[idx + 3]
                        wa = w * a
                        r_sum += pixels[idx] * wa
                        g_sum += pixels[idx + 1] * wa
                        b_sum += pixels[idx + 2] * wa
                        a_sum += wa
                        w_sum += w
                out_idx = (row_dst + dx) * 4
                if a_sum > 0.0 and w_sum > 0.0:
                    result[out_idx] = min(255, int(r_sum / a_sum + 0.5))
                    result[out_idx + 1] = min(255, int(g_sum / a_sum + 0.5))
                    result[out_idx + 2] = min(255, int(b_sum / a_sum + 0.5))
                    result[out_idx + 3] = min(255, int(a_sum / w_sum + 0.5))
        return result

    # ขยายขนาด → bilinear แบบ premultiplied alpha
    for dy in range(dst_h):
        src_y = (dy + 0.5) * y_ratio - 0.5
        y0 = max(0, int(src_y))
        y1 = min(src_h - 1, y0 + 1)
        fy = max(0.0, src_y - y0)
        for dx in range(dst_w):
            src_x = (dx + 0.5) * x_ratio - 0.5
            x0 = max(0, int(src_x))
            x1 = min(src_w - 1, x0 + 1)
            fx = max(0.0, src_x - x0)
            weights = (
                ((y0 * src_w + x0) * 4, (1.0 - fx) * (1.0 - fy)),
                ((y0 * src_w + x1) * 4, fx * (1.0 - fy)),
                ((y1 * src_w + x0) * 4, (1.0 - fx) * fy),
                ((y1 * src_w + x1) * 4, fx * fy),
            )
            r_sum = g_sum = b_sum = a_sum = 0.0
            for idx, w in weights:
                a = pixels[idx + 3]
                wa = w * a
                r_sum += pixels[idx] * wa
                g_sum += pixels[idx + 1] * wa
                b_sum += pixels[idx + 2] * wa
                a_sum += wa
            out_idx = (dy * dst_w + dx) * 4
            if a_sum > 0.0:
                result[out_idx] = min(255, int(r_sum / a_sum + 0.5))
                result[out_idx + 1] = min(255, int(g_sum / a_sum + 0.5))
                result[out_idx + 2] = min(255, int(b_sum / a_sum + 0.5))
                result[out_idx + 3] = min(255, int(a_sum + 0.5))
    return result


def _resize_png(png_bytes: bytes, target_size: int) -> bytes | None:
    """ย่อ PNG เป็นขนาด target_size x target_size ด้วย bilinear. คืน PNG bytes หรือ None."""
    decoded = _png_decode(png_bytes)
    if decoded is None:
        return None
    src_w, src_h, pixels = decoded
    if src_w == target_size and src_h == target_size:
        return png_bytes
    resized = _resize_rgba(pixels, src_w, src_h, target_size, target_size)
    return _png_encode(target_size, target_size, resized)


def png_to_ico(png: str | os.PathLike[str]) -> Path | None:
    """แปลง .png → .ico (multi-resolution, lossless).

    สร้าง .ico ที่มีหลายขนาด (16, 24, 32, 48, 64, 128, 256) โดยย่อ
    ต้นฉบับด้วย bilinear interpolation แล้วฝังเป็น PNG-in-ICO (lossless)
    ไม่ผ่าน GDI HICON → ไม่มี palette quantization

    ถ้าถอดรหัส PNG ไม่ได้ (เช่น ไฟล์ทดสอบ) → fallback เป็น single-res (ฝังต้นฉบับตรงๆ)
    """
    src = Path(png)
    if not src.is_file() or src.suffix.lower() != ".png":
        return None
    ico = src.with_suffix(".ico")
    if ico.is_file():
        try:
            if ico.stat().st_mtime >= src.stat().st_mtime:
                return ico
        except OSError:
            pass
    try:
        data = src.read_bytes()
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            return None  # ไม่ใช่ PNG จริง
        width = struct.unpack(">I", data[16:20])[0]
        height = struct.unpack(">I", data[20:24])[0]
        if width == 0 or height == 0:
            return None

        # ขนาดมาตรฐานที่ Windows taskbar/Explorer ใช้
        ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
        # สร้าง PNG สำหรับแต่ละขนาด (ย่อถ้าจำเป็น)
        entries: list[bytes] = []
        max_side = max(width, height)
        for side in ICO_SIZES:
            if side > max_side:
                continue  # ไม่ขยาย (ป้องกัน upscale ที่ทำให้เบลอ)
            if side == width and side == height:
                entries.append((side, side, data))
            else:
                resized = _resize_png(data, side)
                if resized is not None:
                    entries.append((side, side, resized))
                else:
                    # ถอดรหัสไม่ได้ → ใช้ต้นฉบับ (single fallback)
                    entries.append((side, side, data))
        decoded = _png_decode(data)

        if decoded is None:
            # ถอดรหัสไม่ได้ (เช่น ไฟล์ทดสอบ) → single-res ฝังต้นฉบับตรงๆ (backward compat)
            # width/height byte = 0 (256 convention) เหมือนโค้ดเดิม
            header = struct.pack("<HHH", 0, 1, 1)
            entry = struct.pack(
                "<BBBBHHII",
                0, 0, 0, 0, 1, 32, len(data), 22,
            )
            ico.write_bytes(header + entry + data)
            return ico if ico.is_file() else None

        # ถ้ามี entry เดียวและเป็นต้นฉบับ → single-res (backward compat)
        # สร้าง ICO
        # คำนวณ offset
        header_size = 6
        entry_size = 16
        num = len(entries)
        offset = header_size + num * entry_size
        # สร้าง header
        ico_data = struct.pack("<HHH", 0, 1, num)
        # สร้าง entries
        image_blobs: list[bytes] = []
        for w, h, png_bytes in entries:
            entry = struct.pack(
                "<BBBBHHII",
                0 if w >= 256 else w,  # width byte (0 = 256)
                0 if h >= 256 else h,  # height byte (0 = 256)
                0,  # color count
                0,  # reserved
                1,  # planes
                32,  # bit count
                len(png_bytes),  # size
                offset,  # offset
            )
            ico_data += entry
            image_blobs.append(png_bytes)
            offset += len(png_bytes)
        for blob in image_blobs:
            ico_data += blob
        ico.write_bytes(ico_data)
    except OSError:
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
            notify_icon_changed(path)
            return True
        except OSError:
            continue
    return False


def repoint_desktop_copies(old_dir_name: str, new_lnk: Path) -> int:
    """อัปเดต `.lnk` ที่ผู้ใช้ลากไปวางบน Desktop ให้ใช้ `.lnk` ใหม่ (มีไอคอนใหม่).

    Windows ก๊อปไฟล์ตอนลากวาง → สำเนาบน Desktop ยังชี้ไอคอนเก่า · เราสร้าง pin ใหม่
    ไม่ได้ แต่เขียนทับไฟล์ของเดิมได้ — คืนจำนวนไฟล์ที่อัปเดต.
    """
    old_value = aumid(old_dir_name)
    desktop = _home() / "Desktop"
    try:
        candidates = list(desktop.glob("*.lnk"))
    except OSError:
        return 0
    updated = 0
    import shutil

    for path in candidates:
        if not path.is_file():
            continue
        try:
            if (read_lnk_aumid(path) or "") != old_value:
                continue
            shutil.copy2(new_lnk, path)
            notify_icon_changed(path)
            updated += 1
        except OSError:
            continue
    return updated


def app_aumid() -> str:
    """AppUserModelID กลางของหน้าต่างหลัก (แยกจากกลุ่ม ไม่ให้ไปสิงปุ่ม .lnk)."""
    return f"{APP_ID}.app"


def set_app_aumid() -> None:
    """ตั้ง AUMID ของโปรเซสหน้าต่างหลัก (ต้องเรียกก่อนเปิดหน้าต่างแรก)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_aumid())
    except (OSError, AttributeError):
        pass


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


def _reveal_fire_and_forget(command: str) -> str:
    """เปิด Explorer แบบไม่รอ — `explorer /select,"path"` ส่งคำขอให้ process เดิมแล้วจบ

    ถ้าใช้ `subprocess.run(capture_output=True)` จะรอ EOF ของ handle ที่ explorer
    process หลักถือไว้ (มันมีชีวิตถาวร) → ค้างหลายวินาที. เราไม่ต้องการ output จึงทิ้ง pipe
    """
    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    return ""


def reveal_in_explorer(
    path: str | os.PathLike[str],
    runner: Runner | None = None,
) -> None:
    """เปิด Explorer โดยเลือกไฟล์ไว้ (ให้ผู้ใช้ลากไปวางบน taskbar ได้เลย).

    ต้องส่งเป็น string เดี่ยว ไม่ใช่ list — เพราะ `explorer /select,"path with spaces"`
    ต้องการ quote ติดกับพาธ ถ้าเป็น list Python จะ escape quote ให้แล้ว Explorer อ่านไม้ออก
    (path ที่มีช่องว่างเช่น ...\\My Tools\\... จะพัดไปเปิดโฟลเดอร์ Documents แทน)
    """
    target = os.path.normpath(str(path))
    try:
        (runner or _reveal_fire_and_forget)(f'explorer /select,"{target}"')
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
        import ctypes
        from ctypes import wintypes

        user32 = _user32()
        user32.RegisterHotKey.argtypes = [
            wintypes.HWND,
            ctypes.c_int,
            wintypes.UINT,
            wintypes.UINT,
        ]
        user32.RegisterHotKey.restype = wintypes.BOOL
        ok = user32.RegisterHotKey(hwnd, hotkey_id, modifiers, vk)
    except OSError as exc:
        raise WindowsError(str(exc)) from exc
    if not ok:
        raise WindowsError("ลงทะเบียนปุ่มลัดไม่สำเร็จ (อาจชนกับโปรแกรมอื่น)")


def unregister_hotkey(hotkey_id: int, hwnd: int) -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        from ctypes import wintypes

        user32 = _user32()
        user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.UnregisterHotKey.restype = wintypes.BOOL
        user32.UnregisterHotKey(hwnd, hotkey_id)
    except OSError:
        pass
