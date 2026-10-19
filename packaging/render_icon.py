"""เรนเดอร์ไอคอนแอป SVG -> PNG/ICO (ไม่ต้องพึ่ง rsvg-convert/inkscape).

usage: render_icon.py <in.svg> <out.png|out.ico> [size]

`.ico` (Windows) ต้องมีหลายขนาดในไฟล์เดียว ไม่งั้น Explorer/taskbar
จะย่อด้วย nearest-neighbour แล้วเบลอ — Qt เขียน .ico ให้เองได้
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QImage, QPainter, QPixmap
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
        if not _render(renderer, size).save(out, "PNG"):
            print(f"บันทึกไม่สำเร็จ: {out}", file=sys.stderr)
            return 1
        print(f"เขียนไอคอนแล้ว: {out} ({size}x{size})")
        return 0

    # .ico หลายขนาด — QIcon เก็บทุกขนาดแล้ว save เป็น ICO ได้
    icon = QIcon()
    for side in ICO_SIZES:
        icon.addPixmap(QPixmap.fromImage(_render(renderer, side)))
    if not icon.pixmap(ICO_SIZES[-1], ICO_SIZES[-1]).save(out, "ICO"):
        print(f"บันทึก .ico ไม่สำเร็จ: {out}", file=sys.stderr)
        return 1
    print(f"เขียนไอคอนแล้ว: {out} ({', '.join(str(s) for s in ICO_SIZES)} px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())