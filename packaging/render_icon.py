"""เรนเดอร์ไอค่อนแอป SVG -> PNG (ไม่ต้องพึ่ง rsvg-convert/inkscape).

usage: render_icon.py <in.svg> <out.png> [size]
"""
from __future__ import annotations

import sys

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: render_icon.py <in.svg> <out.png> [size]", file=sys.stderr)
        return 2
    src, out = sys.argv[1], sys.argv[2]
    size = int(sys.argv[3]) if len(sys.argv) > 3 else 256

    app = QApplication.instance() or QApplication([])
    renderer = QSvgRenderer(src)
    if not renderer.isValid():
        print(f"อ่าน SVG ไม่ได้: {src}", file=sys.stderr)
        return 1

    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    if not img.save(out, "PNG"):
        print(f"บันทึกไม่สำเร็จ: {out}", file=sys.stderr)
        return 1
    print(f"เขียนไอค่อนแล้ว: {out} ({size}x{size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
