"""การจัดการธีม light/dark/auto ทั้งแอป (หน้าต่างหลัก + แก้ไข + flyout chrome)."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

THEME_LIGHT = "light"
THEME_DARK = "dark"


def resolve_theme(setting: str, app: QApplication) -> str:
    """แปลงค่าตั้ง (auto/light/dark) เป็นสีที่ใช้ได้จริง."""
    if setting == "auto":
        scheme = app.styleHints().colorScheme()
        return THEME_DARK if scheme == Qt.ColorScheme.Dark else THEME_LIGHT
    if setting in (THEME_LIGHT, THEME_DARK):
        return setting
    return THEME_LIGHT


def apply_theme(app: QApplication, theme: str) -> None:
    """ใช้ธีมผ่าน QPalette (ไม่แตะไอคอน/ปุ่มบน Taskbar)."""
    if theme != THEME_DARK:
        app.setPalette(app.style().standardPalette())
        return
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#eeeeee"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#262626"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#dddddd"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#3c3c3c"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#eeeeee"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#3c3c3c"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#eeeeee"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#2f5d8a"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9e9e9e"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#5a9bd4"))
    app.setPalette(palette)