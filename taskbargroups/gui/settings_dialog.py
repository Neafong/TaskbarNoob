"""หน้าต่างตั้งค่าแอป: ธีม (apply ทันที) + ภาษา (สลับทันที) + ที่เก็บ config."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core import i18n
from taskbargroups.core.archive import delete_backups, list_backups
from taskbargroups.core.i18n import available_languages, export_language, import_language, tr
from taskbargroups.core.settings import Settings

from .theme import apply_theme, resolve_theme

_THEME_VALUES = ("auto", "light", "dark")


class SettingsDialog(QDialog):
    def __init__(self, main_window, parent=None) -> None:
        widget_parent = parent
        if widget_parent is None and isinstance(main_window, QWidget):
            widget_parent = main_window
        super().__init__(widget_parent)
        self._main = main_window
        self._settings = Settings()
        self.setWindowTitle(tr("settings.title"))
        self.resize(460, 360)

        layout = QVBoxLayout(self)
        self._form = QFormLayout()

        self.theme_combo = QComboBox()
        for value in _THEME_VALUES:
            self.theme_combo.addItem(tr(f"settings.theme_{value}"), value)
        current = self._settings.get_theme()
        index = self.theme_combo.findData(current)
        self.theme_combo.setCurrentIndex(max(0, index))
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._form.addRow(tr("settings.theme"), self.theme_combo)

        self.theme_hint = QLabel(tr("settings.theme_hint"))
        self.theme_hint.setWordWrap(True)
        self._form.addRow("", self.theme_hint)

        self.language_combo = QComboBox()
        for code, label in available_languages(self._settings.config_dir):
            self.language_combo.addItem(label, code)
        lang_index = self.language_combo.findData(self._settings.get_language())
        self.language_combo.setCurrentIndex(max(0, lang_index))
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        self._form.addRow(tr("settings.language"), self.language_combo)

        lang_buttons = QHBoxLayout()
        self.export_button = QPushButton(tr("settings.export_lang"))
        self.export_button.setToolTip(tr("settings.export_lang_tip"))
        self.export_button.clicked.connect(self._on_export_language)
        self.import_button = QPushButton(tr("settings.import_lang"))
        self.import_button.setToolTip(tr("settings.import_lang_tip"))
        self.import_button.clicked.connect(self._on_import_language)
        lang_buttons.addWidget(self.export_button)
        lang_buttons.addWidget(self.import_button)
        lang_buttons.addStretch(1)
        self._form.addRow("", lang_buttons)

        self.export_all_button = QPushButton(tr("settings.export_all"))
        self.export_all_button.setToolTip(tr("settings.export_all_tip"))
        self.export_all_button.clicked.connect(self._on_export_all)
        self.import_all_button = QPushButton(tr("settings.import_all"))
        self.import_all_button.setToolTip(tr("settings.import_all_tip"))
        self.import_all_button.clicked.connect(self._on_import_all)
        self.delete_backups_button = QPushButton(tr("settings.delete_backups"))
        self.delete_backups_button.setToolTip(tr("settings.delete_backups_tip"))
        self.delete_backups_button.clicked.connect(self._on_delete_backups)
        backup_buttons = QHBoxLayout()
        backup_buttons.addWidget(self.export_all_button)
        backup_buttons.addWidget(self.import_all_button)
        backup_buttons.addWidget(self.delete_backups_button)
        backup_buttons.addStretch(1)
        self._form.addRow("", backup_buttons)

        self.config_button = QPushButton(str(self._settings.config_dir))
        self.config_button.setCursor(Qt.PointingHandCursor)
        self.config_button.setToolTip(tr("settings.open_config_dir"))
        self.config_button.clicked.connect(self._on_open_config)
        self._style_config_button()
        self._form.addRow(tr("settings.config_dir"), self.config_button)

        layout.addLayout(self._form)

        bottom = QHBoxLayout()
        self.credits_label = QLabel(tr("settings.credits"))
        credits_font = self.credits_label.font()
        credits_font.setItalic(True)
        self.credits_label.setFont(credits_font)
        bottom.addWidget(self.credits_label)
        bottom.addStretch(1)
        self.close_button = QPushButton(tr("settings.close"))
        self.close_button.clicked.connect(self.accept)
        bottom.addWidget(self.close_button)
        layout.addLayout(bottom)

    def _style_config_button(self) -> None:
        """ปุ่มเปิดโฟลเดอร์ config ให้ดู "กดได้" (กรอบ + hover) ไม่แบนเหมือนข้อความ."""
        pal = self.palette()
        border = pal.color(QPalette.ColorRole.Mid).name()
        text = pal.color(QPalette.ColorRole.Text).name()
        hover_bg = pal.color(QPalette.ColorRole.AlternateBase).name()
        self.config_button.setStyleSheet(
            "text-align: left;"
            f"QPushButton {{ border: 1px solid {border}; border-radius: 4px;"
            f" padding: 4px 10px; color: {text}; background: transparent; }}"
            f"QPushButton:hover {{ background: {hover_bg}; }}"
        )

    def _on_theme_changed(self, index: int) -> None:
        value = self.theme_combo.itemData(index)
        self._settings.set_theme(value)
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, resolve_theme(value, app))
        self._style_config_button()

    def _on_language_changed(self, index: int) -> None:
        code = self.language_combo.itemData(index)
        if not code:
            return
        self._settings.set_language(code)
        i18n.setup(code, self._settings.config_dir)
        self._retranslate()
        if isinstance(self._main, QWidget):
            self._main.retranslate()

    def _retranslate(self) -> None:
        self.setWindowTitle(tr("settings.title"))
        for i, value in enumerate(_THEME_VALUES):
            self.theme_combo.setItemText(i, tr(f"settings.theme_{value}"))
        self.theme_hint.setText(tr("settings.theme_hint"))
        for widget, key in (
            (self.theme_combo, "settings.theme"),
            (self.language_combo, "settings.language"),
            (self.config_button, "settings.config_dir"),
        ):
            label = self._form.labelForField(widget)
            if label is not None:
                label.setText(tr(key))
        self.export_button.setText(tr("settings.export_lang"))
        self.export_button.setToolTip(tr("settings.export_lang_tip"))
        self.import_button.setText(tr("settings.import_lang"))
        self.import_button.setToolTip(tr("settings.import_lang_tip"))
        self.export_all_button.setText(tr("settings.export_all"))
        self.export_all_button.setToolTip(tr("settings.export_all_tip"))
        self.import_all_button.setText(tr("settings.import_all"))
        self.import_all_button.setToolTip(tr("settings.import_all_tip"))
        self.delete_backups_button.setText(tr("settings.delete_backups"))
        self.delete_backups_button.setToolTip(tr("settings.delete_backups_tip"))
        self.config_button.setToolTip(tr("settings.open_config_dir"))
        self.credits_label.setText(tr("settings.credits"))
        self.close_button.setText(tr("settings.close"))

    def _on_open_config(self) -> None:
        path = self._settings.config_dir
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def _on_export_all(self) -> None:
        from taskbargroups.core import archive

        default = self._settings.config_dir.parent / archive.EXPORT_DEFAULT_NAME.format(
            ts=archive._timestamp()
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("settings.export_all_dialog_title"),
            str(default),
            "ZIP (*.zip)",
        )
        if not path:
            return
        try:
            out = archive.export_config(self._settings.config_dir, path)
        except archive.ArchiveError as exc:
            QMessageBox.warning(self, tr("err.generic"), self._archive_error(exc))
            return
        report = archive.inspect_zip(out)
        QMessageBox.information(
            self,
            tr("settings.export_all_dialog_title"),
            tr(
                "settings.export_all_ok",
                count=len(report.groups),
                path=str(out),
                size=self._human_size(report.total_size),
            ),
        )

    def _on_import_all(self) -> None:
        from taskbargroups.core import archive

        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings.import_all_dialog_title"),
            str(self._settings.config_dir.parent),
            "ZIP (*.zip)",
        )
        if not path:
            return
        try:
            report = archive.inspect_zip(path)
        except archive.ArchiveError as exc:
            QMessageBox.warning(self, tr("err.generic"), self._archive_error(exc))
            return

        box = QMessageBox(self)
        box.setWindowTitle(tr("settings.import_confirm_title"))
        box.setText(tr("settings.import_confirm_merge", count=len(report.groups)))
        merge_btn = box.addButton(
            tr("settings.import_merge_button"), QMessageBox.AcceptRole
        )
        replace_btn = box.addButton(
            tr("settings.import_replace_button"), QMessageBox.DestructiveRole
        )
        box.addButton(tr("settings.cancel"), QMessageBox.RejectRole)
        box.setDefaultButton(merge_btn)
        box.exec()
        clicked = box.clickedButton()
        if clicked is merge_btn:
            self._run_import(path, "merge")
        elif clicked is replace_btn:
            confirm = QMessageBox.question(
                self,
                tr("settings.import_confirm_title"),
                tr("settings.import_confirm_replace"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm == QMessageBox.Yes:
                self._run_import(path, "replace")

    def _run_import(self, path: str, mode: str) -> None:
        from taskbargroups.core import archive

        try:
            report = archive.import_config(path, self._settings.config_dir, mode=mode)
        except archive.ArchiveError as exc:
            QMessageBox.warning(self, tr("err.generic"), self._archive_error(exc))
            return
        message = tr("settings.import_summary", count=len(report.groups_imported))
        if report.groups_kept:
            message += tr(
                "settings.import_summary_renamed", count=len(report.groups_kept)
            )
        if report.backup_dir is not None:
            message += tr("settings.import_backup_note", path=str(report.backup_dir))
        if isinstance(self._main, QWidget):
            self._main.refresh()
        QMessageBox.information(
            self, tr("settings.import_confirm_title"), message
        )

    @staticmethod
    def _human_size(size: int) -> str:
        value = float(size)
        for unit in ("B", "KB", "MB", "GB"):
            if value < 1024 or unit == "GB":
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} GB"

    @staticmethod
    def _dir_size(path: Path) -> int:
        total = 0
        for root, _dirs, files in os.walk(path):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    continue
        return total

    def _on_delete_backups(self) -> None:
        backups = list_backups(self._settings.config_dir)
        if not backups:
            QMessageBox.information(
                self,
                tr("settings.delete_backups_title"),
                tr("settings.delete_backups_none"),
            )
            return
        sizes = {b: self._dir_size(b) for b in backups}
        total = sum(sizes.values())
        details = "\n".join(
            f"• {b.name}  ({self._human_size(sizes[b])})" for b in backups
        )
        box = QMessageBox(self)
        box.setWindowTitle(tr("settings.delete_backups_title"))
        box.setText(
            tr(
                "settings.delete_backups_confirm",
                n=len(backups),
                size=self._human_size(total),
            )
        )
        box.setDetailedText(details)
        delete_btn = box.addButton(
            tr("settings.delete_backups"), QMessageBox.DestructiveRole
        )
        box.addButton(tr("settings.cancel"), QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is not delete_btn:
            return
        try:
            removed = delete_backups(self._settings.config_dir, backups)
        except OSError as exc:
            QMessageBox.warning(
                self,
                tr("err.generic"),
                f"{tr('err.backup_delete_failed')}: {exc}",
            )
            return
        QMessageBox.information(
            self,
            tr("settings.delete_backups_title"),
            tr("settings.delete_backups_done", n=removed),
        )

    @staticmethod
    def _archive_error(exc: Exception) -> str:
        text = str(exc)
        if "unsafe" in text:
            return tr("err.archive_slip")
        if "too large" in text or "ใหญ่เกิน" in text:
            return tr("err.archive_too_big")
        if "backup" in text or "สำรอง" in text:
            return tr("err.archive_backup_failed")
        if "zip" in text or "ไฟล์" in text:
            return tr("err.archive_invalid")
        return text

    def _on_export_language(self) -> None:
        language = self.language_combo.currentData() or "th"
        default = i18n.lang_dir(self._settings.config_dir) / f"{language}.json"
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("settings.export_dialog_title"),
            str(default),
            "JSON (*.json)",
        )
        if not path:
            return
        try:
            export_language(Path(path), language, self._settings.config_dir)
        except OSError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        QMessageBox.information(
            self,
            tr("settings.export_dialog_title"),
            tr("settings.export_ok", path=path),
        )

    def _on_import_language(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("settings.import_dialog_title"),
            str(i18n.lang_dir(self._settings.config_dir)),
            "JSON (*.json)",
        )
        if not path:
            return
        code = import_language(Path(path), self._settings.config_dir)
        if code is None:
            QMessageBox.warning(
                self, tr("err.generic"), tr("settings.import_invalid")
            )
            return
        if self.language_combo.findData(code) < 0:
            label = code
            for option_code, option_label in available_languages(self._settings.config_dir):
                if option_code == code:
                    label = option_label
                    break
            self.language_combo.addItem(label, code)
        self.language_combo.setCurrentIndex(self.language_combo.findData(code))
        QMessageBox.information(
            self,
            tr("settings.import_dialog_title"),
            tr("settings.import_ok", language=code),
        )
