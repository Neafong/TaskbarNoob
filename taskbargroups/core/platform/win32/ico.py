"""Pure-Python multi-resolution `.png` → `.ico` converter with premultiplied-alpha area filter."""

from __future__ import annotations

import math
import os
import struct
import zlib
from pathlib import Path

from .lnk import _ps_quote


def build_png_to_ico_ps_script(
    png: str | os.PathLike[str], ico: str | os.PathLike[str]
) -> str:
    """สคริปต์ PowerShell แปลง .png → .ico (deprecated — ใช้ `png_to_ico` แทน)."""
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
        length = struct.unpack(">I", png[pos : pos + 4])[0]
        chunk = png[pos + 4 : pos + 8]
        data = png[pos + 8 : pos + 8 + length]
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
        row = bytearray(raw[y * row_size + 1 : y * row_size + 1 + stride])
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
                pixels[out_base : out_base + 4] = row[base : base + 4]
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
        raw.extend(pixels[y * stride : (y + 1) * stride])
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

    if dst_w <= src_w and dst_h <= src_h:
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
    """ย่อ PNG เป็นขนาด target_size x target_size. คืน PNG bytes หรือ None."""
    decoded = _png_decode(png_bytes)
    if decoded is None:
        return None
    src_w, src_h, pixels = decoded
    if src_w == target_size and src_h == target_size:
        return png_bytes
    resized = _resize_rgba(pixels, src_w, src_h, target_size, target_size)
    return _png_encode(target_size, target_size, resized)


def png_to_ico(png: str | os.PathLike[str]) -> Path | None:
    """แปลง .png → .ico (multi-resolution, lossless)."""
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
            return None
        width = struct.unpack(">I", data[16:20])[0]
        height = struct.unpack(">I", data[20:24])[0]
        if width == 0 or height == 0:
            return None

        ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)
        entries: list[tuple[int, int, bytes]] = []
        max_side = max(width, height)
        for side in ICO_SIZES:
            if side > max_side:
                continue
            if side == width and side == height:
                entries.append((side, side, data))
            else:
                resized = _resize_png(data, side)
                if resized is not None:
                    entries.append((side, side, resized))
                else:
                    entries.append((side, side, data))
        decoded = _png_decode(data)

        if decoded is None:
            header = struct.pack("<HHH", 0, 1, 1)
            entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(data), 22)
            ico.write_bytes(header + entry + data)
            return ico if ico.is_file() else None

        header_size = 6
        entry_size = 16
        num = len(entries)
        offset = header_size + num * entry_size
        ico_data = struct.pack("<HHH", 0, 1, num)
        image_blobs: list[bytes] = []
        for w, h, png_bytes in entries:
            entry = struct.pack(
                "<BBBBHHII",
                0 if w >= 256 else w,
                0 if h >= 256 else h,
                0,
                0,
                1,
                32,
                len(png_bytes),
                offset,
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
