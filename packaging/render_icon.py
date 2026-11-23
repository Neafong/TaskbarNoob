"""เรนเดอร์ไอคอนแอป SVG -> PNG/ICO (ไม่ต้องพึ่ง rsvg-convert/inkscape).

usage: render_icon.py <in.svg> <out.png|out.ico> [size]

`.ico` (Windows) ต้องมีหลายขนาดในไฟล์เดียว ไม่งั้น Explorer/taskbar
จะย่อด้วย nearest-neighbour แล้วเบลอ — ใช้ PNG-in-ICO format
"""

from __future__ import annotations

import io
import struct
import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

# ขนาดมาตรฐานที่ Windows ใช้ (16 = title bar, 256 = taskbar/Explorer ขนาดใหญ่)
ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def _render(renderer: QSvgRenderer, size: int) -> QImage:
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()
    return img


def _image_to_png_bytes(img: QImage) -> bytes:
    from PySide6.QtCore import QBuffer, QIODevice
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def _write_ico(out: str, images: list[QImage]) -> bool:
    """เขียน multi-res ICO ด้วย PNG-in-ICO format."""
    png_blobs: list[bytes] = []
    sizes: list[tuple[int, int]] = []
    for img in images:
        png_data = _image_to_png_bytes(img)
        png_blobs.append(png_data)
        sizes.append((img.width(), img.height()))

    num = len(png_blobs)
    header_size = 6
    entry_size = 16
    offset = header_size + num * entry_size

    data = struct.pack("<HHH", 0, 1, num)
    for (w, h), png_bytes in zip(sizes, png_blobs):
        entry = struct.pack(
            "<BBBBHHII",
            0 if w >= 256 else w,
            0 if h >= 256 else h,
            0, 0, 1, 32, len(png_bytes), offset,
        )
        data += entry
        offset += len(png_bytes)
    for png_bytes in png_blobs:
        data += png_bytes

    try:
        with open(out, "wb") as f:
            f.write(data)
        return True
    except OSError:
        return False


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: render_icon.py <in.svg> <out.png|out.ico> [size]", file=sys.stderr)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 256

    app = QApplication.instance() or QApplication([])
    renderer = QSvgRenderer(src)
    if not renderer.isValid():
        print(f"อ่าน SVG ไม่ได้: {src}", file=sys.stderr)
        return 1

    if not out.lower().endswith(".ico"):
        img = _render(renderer, size)
        if not img.save(out, "PNG"):
            print(f"บันทึกไม่สำเร็จ: {out}", file=sys.stderr)
            return 1
        print(f"เขียนไอคอนแล้ว: {out} ({size}x{size})")
        return 0

    # .ico หลายขนาด — render ทุกขนาดแล้วเขียน PNG-in-ICO
    images = [_render(renderer, s) for s in ICO_SIZES]
    if not _write_ico(out, images):
        print(f"บันทึก .ico ไม่สำเร็จ: {out}", file=sys.stderr)
        return 1
    print(f"เขียนไอคอนแล้ว: {out} ({', '.join(str(s) for s in ICO_SIZES)} px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
