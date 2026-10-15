"""popup ข้อความมาตรฐาน: ปุ่มไม่มีไอคอน + ข้อความตามภาษาที่เลือก."""

from __future__ import annotations

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox, QPushButton, QWidget

from taskbargroups.core.i18n import tr

_BUTTON_TEXT = {
    QMessageBox.Ok: "dialog.ok",
    QMessageBox.Cancel: "dialog.cancel",
    QMessageBox.Close: "dialog.close",
    QMessageBox.Yes: "dialog.yes",
    QMessageBox.No: "dialog.no",
}


def style_message_box(box: QMessageBox) -> QMessageBox:
    """popup เล็ก: เอาไอคอนออกจากปุ่มทั้งหมด + ตั้งข้อความเป็นภาษาที่เลือก."""
    for button in box.findChildren(QPushButton):
        button.setIcon(QIcon())
    for standard, key in _BUTTON_TEXT.items():
        btn = box.button(standard)
        if btn is not None:
            btn.setText(tr(key))
            btn.setIcon(QIcon())
    return box


def show_warning(parent: QWidget | None, title: str, text: str) -> int:
    box = QMessageBox(QMessageBox.Warning, title, text, QMessageBox.Ok, parent)
    return style_message_box(box).exec()


def show_information(parent: QWidget | None, title: str, text: str) -> int:
    box = QMessageBox(QMessageBox.Information, title, text, QMessageBox.Ok, parent)
    return style_message_box(box).exec()


def show_critical(parent: QWidget | None, title: str, text: str) -> int:
    box = QMessageBox(QMessageBox.Critical, title, text, QMessageBox.Ok, parent)
    return style_message_box(box).exec()


def show_question(
    parent: QWidget | None,
    title: str,
    text: str,
    buttons: QMessageBox.StandardButtons = QMessageBox.Yes | QMessageBox.No,
    default: QMessageBox.StandardButton = QMessageBox.No,
) -> int:
    box = QMessageBox(QMessageBox.Question, title, text, buttons, parent)
    box.setDefaultButton(default)
    return style_message_box(box).exec()
