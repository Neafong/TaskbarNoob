"""Dialog เพิ่ม/แก้ไข shortcut เดี่ยวภายในกลุ่ม."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from taskbargroups.core import icons as core_icons
from taskbargroups.core.i18n import tr
from taskbargroups.core.models import Shortcut

from .button_icons import themed_icon
from .dialogs import show_information, show_warning
from .icon_picker import (
    _PROVIDER_ICON_CACHE_DIRNAME,
    _PROVIDER_ICON_SUFFIXES,
    _cached_provider_png,
)
from .theme import app_text_color

_FALLBACK_GRID_ICON = "application-x-executable"
_ICON_FILTER = "รูปภาพ (*.png *.svg *.jpg *.jpeg *.ico *.bmp *.xpm);;ทุกไฟล์ (*)"


def _style_dialog_buttons(box: QDialogButtonBox) -> None:
    """ปุ่ม OK/Cancel ของ dialog: ใช้ข้อความตามภาษา + ไอคอน SVG ของเรา."""
    ok_button = box.button(QDialogButtonBox.Ok)
    if ok_button is not None:
        ok_button.setText(tr("dialog.ok"))
        icon = themed_icon("check-fill.svg", app_text_color())
        if not icon.isNull():
            ok_button.setIcon(icon)
    cancel_button = box.button(QDialogButtonBox.Cancel)
    if cancel_button is not None:
        cancel_button.setText(tr("dialog.cancel"))
        icon = themed_icon("x-fill.svg", app_text_color())
        if not icon.isNull():
            cancel_button.setIcon(icon)


class ShortcutDialog(QDialog):
    def __init__(
        self, parent: QWidget | None = None, shortcut: Shortcut | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("shortcut.title"))
        self.resize(460, 260)
        self._shortcut = shortcut or Shortcut(name="", target="")
        self._icon_source: str | None = None

        form = QFormLayout(self)

        self.name_edit = QLineEdit(self._shortcut.name)
        self.name_edit.setMaxLength(27)
        form.addRow(tr("shortcut.display_name"), self.name_edit)

        target_row = QHBoxLayout()
        self.target_edit = QLineEdit(self._shortcut.target)
        self.target_edit.textChanged.connect(self._on_target_changed)
        target_browse = QPushButton(tr("shortcut.browse"))
        target_browse.clicked.connect(self._browse_target)
        target_row.addWidget(self.target_edit)
        target_row.addWidget(target_browse)
        target_widget = QWidget()
        target_widget.setLayout(target_row)
        form.addRow(tr("shortcut.target"), target_widget)

        cwd_row = QHBoxLayout()
        self.cwd_edit = QLineEdit(self._shortcut.working_dir or "")
        cwd_browse = QPushButton(tr("shortcut.browse"))
        cwd_browse.clicked.connect(self._browse_cwd)
        cwd_row.addWidget(self.cwd_edit)
        cwd_row.addWidget(cwd_browse)
        cwd_widget = QWidget()
        cwd_widget.setLayout(cwd_row)
        form.addRow(tr("shortcut.working_dir"), cwd_widget)

        self.args_edit = QLineEdit(self._shortcut.arguments)
        form.addRow(tr("shortcut.arguments"), self.args_edit)

        icon_row = QHBoxLayout()
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(48, 48)
        self.icon_preview.setAlignment(Qt.AlignCenter)
        pick_icon = QPushButton(tr("shortcut.pick_file"))
        pick_icon.clicked.connect(self._pick_icon)
        auto_icon = QPushButton(tr("shortcut.auto_icon"))
        auto_icon.setToolTip(core_icons.platform_note())
        auto_icon.clicked.connect(self._auto_icon)
        icon_row.addWidget(self.icon_preview)
        icon_row.addWidget(pick_icon)
        icon_row.addWidget(auto_icon)
        icon_widget = QWidget()
        icon_widget.setLayout(icon_row)
        form.addRow(icon_widget)
        self._update_icon_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        _style_dialog_buttons(buttons)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse_target(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("shortcut.pick_target_dialog"))
        if path:
            self.target_edit.setText(path)
            if not self.name_edit.text().strip():
                self.name_edit.setText(Path(path).stem)

    def _browse_cwd(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr("shortcut.pick_cwd_dialog"))
        if path:
            self.cwd_edit.setText(path)

    def _on_target_changed(self) -> None:
        if self._icon_source is None:
            self._update_icon_preview()

    def _update_icon_preview(self) -> None:
        """โชว์รูปไอคอนปัจจุบัน (48px) แทนข้อความ."""
        pixmap: QPixmap | None = None
        for candidate in (
            Path(self._icon_source) if self._icon_source else None,
            Path(self._shortcut.icon) if self._shortcut.icon else None,
        ):
            if candidate is not None and candidate.is_file():
                loaded = QPixmap(str(candidate))
                if not loaded.isNull():
                    pixmap = loaded
                    break
        if pixmap is None:
            auto = core_icons.resolve_icon_source(
                self.target_edit.text().strip() or None
            )
            if auto is not None and auto.is_file():
                loaded = QPixmap(str(auto))
                if not loaded.isNull():
                    pixmap = loaded
        if pixmap is None:
            pixmap = QIcon.fromTheme(_FALLBACK_GRID_ICON).pixmap(48, 48)
        if pixmap is not None and not pixmap.isNull():
            self.icon_preview.setPixmap(
                pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.icon_preview.clear()

    def _pick_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("shortcut.pick_icon_dialog"), "", _ICON_FILTER
        )
        if path:
            self._icon_source = path
            self._update_icon_preview()

    def _auto_icon(self) -> None:
        target = self.target_edit.text().strip()
        source = core_icons.resolve_icon_source(target)
        if (
            source is None
            and target
            and Path(target).suffix.lower() in _PROVIDER_ICON_SUFFIXES
        ):
            cache = Path(tempfile.gettempdir()) / _PROVIDER_ICON_CACHE_DIRNAME
            source = _cached_provider_png(Path(target), cache)
        if source is None and target and os.access(target, os.X_OK):
            source = core_icons.icon_from_executable(target)
        if source is None:
            show_information(
                self,
                tr("shortcut.no_icon_title"),
                tr("shortcut.no_icon_body"),
            )
            return
        self._icon_source = str(source)
        self._update_icon_preview()

    def _on_accept(self) -> None:
        if not self.target_edit.text().strip():
            show_warning(self, tr("err.generic"), tr("shortcut.missing_target"))
            return
        self.accept()

    def result_shortcut(self) -> Shortcut:
        return Shortcut(
            name=self.name_edit.text().strip(),
            target=self.target_edit.text().strip(),
            working_dir=self.cwd_edit.text().strip() or None,
            arguments=self.args_edit.text(),
            icon=self._shortcut.icon,
        )

    def icon_source(self) -> str | None:
        return self._icon_source
