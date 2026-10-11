"""สร้างไอคอนแอป (PNG) ด้วย Qt — ไม่ต้องพึ่ง Pillow/Inkscape.

ใช้งาน: QT_QPA_PLATFORM=offscreen python packaging/make_icon.py <out.png>
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter


def render(size: int = 256) -> QImage:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)

    margin = size * 0.06
    radius = size * 0.22
    background = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)

    gradient = QLinearGradient(background.topLeft(), background.bottomRight())
    gradient.setColorAt(0.0, QColor("#2bb673"))
    gradient.setColorAt(1.0, QColor("#115e59"))
    painter.setBrush(gradient)
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(background, radius, radius)

    tiles = size * 0.16
    gap = size * 0.075
    grid_w = 3 * tiles + 2 * gap
    grid_h = 2 * tiles + gap
    start_x = (size - grid_w) / 2
    start_y = (size - grid_h) / 2
    tile_radius = tiles * 0.28

    for row in range(2):
        for col in range(3):
            x = start_x + col * (tiles + gap)
            y = start_y + row * (tiles + gap)
            alpha = 235 if (row + col) % 2 == 0 else 165
            painter.setBrush(QColor(255, 255, 255, alpha))
            painter.drawRoundedRect(QRectF(x, y, tiles, tiles), tile_radius, tile_radius)

    painter.end()
    return image


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "packaging/appimage/taskbargroups.png"
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 256
    image = render(size)
    if not image.save(out, "PNG"):
        print(f"บันทึกไอคอนไม่สำเร็จ: {out}", file=sys.stderr)
        return 1
    print(f"เขียนไอคอนแล้ว: {out} ({size}x{size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
