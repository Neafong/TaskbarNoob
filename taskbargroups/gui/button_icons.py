"""ชุดไอคอน SVG ของเราเอง + ตกแต่งตามธีม (tint)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QIcon, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import Qt

_ASSETS = Path(__file__).resolve().parents[2] / "packaging" / "assets" / "icons"


def _svg_path(name: str) -> Path | None:
    path = _ASSETS / name
    if path.exists():
        return path
    return None


def _tinted_pixmap(svg_path: Path, size: int, color: QColor) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer = QSvgRenderer(str(svg_path))
    painter.setCompositionMode(QPainter.CompositionMode_Source)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), color)
    painter.end()
    return pixmap


def themed_icon(name: str, base_color: QColor | None = None) -> QIcon:
    """คืนไอคอนที่ tint ตามสีที่ส่ง (ถ้าไม่ส่ง จะใช้สี text ธีมผ่าน caller)."""
    icon = QIcon()
    svg = _svg_path(name)
    if svg is None:
        return icon
    # สร้างหลายขนาดให้ดูคม
    for sz in (16, 20, 24, 28, 32):
        if base_color is not None:
            icon.addPixmap(_tinted_pixmap(svg, sz, base_color))
    return icon


def text_color_from_palette(palette) -> QColor:
    return palette.color(palette.ColorRole.Text)
