"""ไดอะล็อกตั้ง global hotkey ให้กลุ่ม (Cinnamon/gsettings · Windows/RegisterHotKey)."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core import hotkeys
from taskbargroups.core.desktop import build_exec
from taskbargroups.core.i18n import tr
from taskbargroups.core.models import (
    MAX_FOCUS_SCALE,
    MIN_FOCUS_SCALE,
    Group,
)
from taskbargroups.core.storage import ConfigStore, StorageError

from .dialogs import show_information, show_warning

_MODIFIER_MAP = {
    "Ctrl": "<Control>",
    "Shift": "<Shift>",
    "Alt": "<Alt>",
    "Meta": "<Super>",
}


def qt_sequence_to_cinnamon(sequence: QKeySequence) -> str:
    text = sequence.toString()
    if not text:
        return ""
    parts = text.split("+")
    *modifiers, key = parts
    prefix = "".join(_MODIFIER_MAP.get(mod, f"<{mod}>") for mod in modifiers)
    base = key.lower() if len(key) == 1 else key
    return prefix + base


class HotkeyDialog(QDialog):
    def __init__(
        self,
        group: Group,
        store: ConfigStore,
        dir_name: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.group = group
        self.store = store
        self.dir_name = dir_name
        self.setWindowTitle(tr("hotkey.title", name=group.name))
        self.resize(480, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.command_edit = QLineEdit(build_exec(dir_name, center=True))
        self.command_edit.setReadOnly(True)
        form.addRow(tr("hotkey.command"), self.command_edit)

        self.key_edit = QKeySequenceEdit()
        self._existing = self._current_binding()
        if self._existing:
            self.key_edit.setKeySequence(
                QKeySequence(hotkeys.cinnamon_to_display(self._existing))
            )
        else:
            self.key_edit.setKeySequence(QKeySequence("Ctrl+Shift+G"))
        form.addRow(tr("hotkey.keys"), self.key_edit)

        self.preview = QLabel()
        form.addRow(tr("hotkey.cinnamon_format"), self.preview)
        self.key_edit.keySequenceChanged.connect(self._update_preview)

        self.scale_slider = QSlider(Qt.Horizontal)
        self.scale_slider.setRange(
            round(MIN_FOCUS_SCALE * 10), round(MAX_FOCUS_SCALE * 10)
        )
        self.scale_slider.setSingleStep(1)
        self.scale_slider.setPageStep(5)
        self.scale_slider.setValue(round(group.focus_scale * 10))
        self.scale_label = QLabel()
        self.scale_slider.valueChanged.connect(self._update_scale_label)
        scale_row = QHBoxLayout()
        scale_row.addWidget(self.scale_slider, 1)
        scale_row.addWidget(self.scale_label)
        scale_widget = QWidget()
        scale_widget.setLayout(scale_row)
        scale_widget.setToolTip(tr("hotkey.focus_scale_tip"))
        form.addRow(tr("hotkey.focus_scale"), scale_widget)

        layout.addLayout(form)

        note = QLabel(tr("hotkey.note"))
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(self)
        install_button = buttons.addButton(tr("hotkey.install"), QDialogButtonBox.AcceptRole)
        remove_button = buttons.addButton(tr("hotkey.remove"), QDialogButtonBox.DestructiveRole)
        remove_button.setEnabled(bool(self._existing))
        buttons.addButton(tr("hotkey.close"), QDialogButtonBox.RejectRole)
        install_button.clicked.connect(self._install)
        remove_button.clicked.connect(self._remove)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._update_preview()
        self._update_scale_label()

    def _update_preview(self) -> None:
        self.preview.setText(
            qt_sequence_to_cinnamon(self.key_edit.keySequence()) or tr("hotkey.empty")
        )

    def _update_scale_label(self) -> None:
        self.scale_label.setText(f"{self.scale_slider.value() / 10:.1f}x")

    def _save_focus_scale(self) -> None:
        scale = self.scale_slider.value() / 10
        if scale == self.group.focus_scale:
            return
        self.group.focus_scale = scale
        try:
            self.store.save_group(self.group)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))

    def _slot(self) -> str:
        return hotkeys.hotkey_slot(self.dir_name)

    def _hwnd(self) -> int:
        parent = self.parent()
        if parent is not None and hasattr(parent, "winId"):
            try:
                return int(parent.winId())
            except (TypeError, ValueError):
                pass
        return 0

    def _current_binding(self) -> str:
        if hotkeys.is_cinnamon():
            return hotkeys.get_binding(self._slot())
        if sys.platform == "win32":
            from taskbargroups.core.settings import Settings

            return Settings().get_hotkeys().get(self._slot(), "")
        return ""

    def _install_windows(self, binding: str) -> None:
        from taskbargroups.core.settings import Settings

        from .win32_hotkey import registry

        registry.register_slot(self._slot(), self.dir_name, binding, self._hwnd())
        Settings().set_hotkey(self._slot(), binding)

    def _remove_windows(self) -> None:
        from taskbargroups.core.settings import Settings

        from .win32_hotkey import registry

        registry.unregister_slot(self._slot(), self._hwnd())
        Settings().remove_hotkey(self._slot())

    def _install(self) -> None:
        binding = qt_sequence_to_cinnamon(self.key_edit.keySequence())
        if not binding:
            show_warning(self, tr("err.generic"), tr("hotkey.no_binding"))
            return
        self._save_focus_scale()
        if sys.platform == "win32":
            try:
                self._install_windows(binding)
            except OSError as exc:
                show_warning(self, tr("err.generic"), str(exc))
                return
        elif hotkeys.is_cinnamon():
            try:
                hotkeys.register_cinnamon_hotkey(
                    self._slot(),
                    self.group.name,
                    build_exec(self.dir_name, center=True),
                    binding,
                )
            except hotkeys.HotkeyError as exc:
                show_warning(self, tr("err.generic"), str(exc))
                return
        else:
            show_warning(
                self, tr("hotkey.unsupported_title"), tr("hotkey.unsupported_body")
            )
            return
        show_information(
            self,
            tr("hotkey.success_title"),
            tr("hotkey.success_body", binding=binding, name=self.group.name),
        )
        self.accept()

    def _remove(self) -> None:
        if sys.platform == "win32":
            try:
                self._remove_windows()
            except OSError as exc:
                show_warning(self, tr("err.generic"), str(exc))
                return
        elif hotkeys.is_cinnamon():
            try:
                hotkeys.unregister_cinnamon_hotkey(self._slot())
            except hotkeys.HotkeyError as exc:
                show_warning(self, tr("err.generic"), str(exc))
                return
        else:
            show_warning(
                self, tr("hotkey.unsupported_title"), tr("hotkey.unsupported_body")
            )
            return
        show_information(
            self,
            tr("hotkey.success_title"),
            tr("hotkey.remove_success", name=self.group.name),
        )
        self.accept()
