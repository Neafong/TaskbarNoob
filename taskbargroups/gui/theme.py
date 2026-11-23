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
    # Windows native style (windowsvista) ไม่สนใจ QPalette → ใช้ Fusion ของ Qt ที่คุมสีได้เอง
    from PySide6.QtWidgets import QStyleFactory

    if app.style().objectName() != "fusion":
        app.setStyle(QStyleFactory.create("Fusion"))
    # Accent token (#1f9ede — ฟ้าสด ทันสมัย) ใช้ร่วมทุกธีม
    accent = QColor("#1f9ede")
    if theme != THEME_DARK:
        # เขียน light palette เองทั้งชุด — standardPalette คืนค่าไม่สม่ำเสมอบน
        # Windows dark mode (วิดเจ็ตบางตัวมืด บางตัวสว่าง → ดูประหลาด)
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#f5f5f5"))
        palette.setColor(QPalette.ColorRole.WindowText, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Base, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#f0f0f0"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Button, QColor("#e1e1e1"))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#ffffe1"))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#1e1e1e"))
        palette.setColor(QPalette.ColorRole.Highlight, accent)
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9e9e9e"))
        palette.setColor(QPalette.ColorRole.Link, accent.darker(110))
        palette.setColor(QPalette.ColorRole.Mid, QColor("#b0b0b0"))
        _apply_and_polish(app, palette)
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
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#9e9e9e"))
    palette.setColor(QPalette.ColorRole.Link, accent.darker(110))
    # Mid — ใช้เป็นเส้นขอบในปุ่ม/ช่องสี ต้องตั้งให้เป็นกลาง (ไม่ตกค้างจาก light)
    palette.setColor(QPalette.ColorRole.Mid, QColor("#5a5a5a"))
    _apply_and_polish(app, palette)


def _apply_and_polish(app: QApplication, palette: QPalette) -> None:
    """ตั้ง palette แล้ว force วิดเจ็ตทุกตัว refresh (กันสีค้างตอนสลับธีม)."""
    app.setPalette(palette)
    # Force style polish ทั้ง app — กัน Qt cache palette เก่าของวิดเจ็ตที่สร้างไปแล้ว
    app.style().polish(app)
    # Force repaint ทุก top-level widget (กันบาง widget ไม่ refresh ทัน)
    for widget in app.topLevelWidgets():
        widget.update()
        widget.style().polish(widget)


def app_color(role: QPalette.ColorRole) -> QColor:
    """สีจาก app palette ตรงๆ (ค่าจริงทันทีหลัง apply_theme ไม่ต้องรอ PaletteChange event).

    ใช้ทาสีไอคอน/สไตล์ตอนสลับธีม — กันบั๊ก "คลิก 2 รอบ" ที่อ่าน widget.palette()
    แล้วได้สีเก่าเพราะ event ยังส่งไม่ถึงวิดเจ็ต.
    """
    app = QApplication.instance()
    if app is None:
        return QColor()
    return app.palette().color(role)


def app_text_color() -> QColor:
    """สี text สำหรับ tint ไอคอน — อ่านจาก app ทันที ไม่รอ event."""
    return app_color(QPalette.ColorRole.Text)