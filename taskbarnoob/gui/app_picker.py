"""หน้าต่างเลือกแอปที่ติดตั้งในเครื่อง (Linux .desktop + Flatpak + Snap / Windows Start Menu)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from taskbarnoob.core import icons as core_icons
from taskbarnoob.core.i18n import tr

from .icon_picker import (
    _is_noise_shortcut,
    _iter_windows_shortcuts,
    _windows_shortcut_dirs,
)
from .icons import _PROVIDER_ICON_CACHE_DIRNAME, _cached_provider_png

_FALLBACK_APP_ICON = "application-x-executable"


def _parse_desktop_app(path: Path) -> tuple[str, str] | None:
    """อ่าน (Name, Icon) จาก `[Desktop Entry]` คืน None ถ้าเป็น NoDisplay/Hidden/ไม่ใช่ Application."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    in_entry = False
    name = ""
    icon = ""
    app_type = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            if in_entry:
                break
            in_entry = line == "[Desktop Entry]"
            continue
        if not in_entry or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip()
        if key == "Type":
            app_type = val
        elif key in ("NoDisplay", "Hidden") and val.lower() == "true":
            return None
        elif key == "Name" and not name:
            name = val
        elif key == "Icon" and not icon:
            icon = val
    if app_type and app_type != "Application":
        return None
    if not name:
        return None
    return (name, icon)


def scan_installed_linux_apps(
    dirs: Iterable[Path] | None = None,
) -> list[tuple[str, Path, str]]:
    """สแกนแอปที่ติดตั้งจากโฟลเดอร์ `.desktop` คืนรายการ `(display_name, desktop_path, icon_key)`."""
    search = list(dirs) if dirs is not None else core_icons.desktop_search_dirs()
    seen_ids: set[str] = set()
    entries: list[tuple[str, Path, str]] = []
    for base in search:
        if not base.is_dir():
            continue
        try:
            files = sorted(base.glob("*.desktop"))
        except OSError:
            continue
        for desktop in files:
            key = desktop.name.lower()
            if key in seen_ids or key.startswith(("taskbarnoob-", "taskbargroups-")):
                continue
            parsed = _parse_desktop_app(desktop)
            if parsed is None:
                continue
            seen_ids.add(key)
            name, icon_key = parsed
            entries.append((name, desktop, icon_key))
    entries.sort(key=lambda item: item[0].casefold())
    return entries


class AppPickerDialog(QDialog):
    """ไดอะล็อกค้นหาและเลือกแอปที่ติดตั้งในเครื่องเพื่อเพิ่มเข้ากลุ่มในคลิกเดียว."""

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_dir: Path | None = None,
        desktop_dirs: Iterable[Path] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("app_picker.title"))
        self.resize(480, 460)
        self._path: str | None = None
        self._cache_dir = cache_dir
        self._desktop_dirs = desktop_dirs
        self._entries: list[tuple[str, str, QIcon]] = []

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("app_picker.search_placeholder"))
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.setIconSize(QSize(28, 28))
        self.list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self.accept())
        self.list_widget.itemActivated.connect(lambda _item: self.accept())
        layout.addWidget(self.list_widget, 1)

        row = QHBoxLayout()
        self.count_label = QLabel()
        choose = QPushButton(tr("system_icon.choose"))
        choose.setDefault(True)
        choose.clicked.connect(self.accept)
        row.addWidget(self.count_label)
        row.addStretch(1)
        row.addWidget(choose)
        layout.addLayout(row)

        self._scan()
        self._apply_filter("")

    def selected_path(self) -> str | None:
        return self._path

    def _effective_cache_dir(self) -> Path:
        if self._cache_dir is not None:
            return self._cache_dir
        return Path(tempfile.gettempdir()) / _PROVIDER_ICON_CACHE_DIRNAME

    def done(self, result: int) -> None:
        if result == QDialog.Accepted and self.list_widget.currentItem() is not None:
            self._path = self.list_widget.currentItem().data(Qt.UserRole)
        super().done(result)

    def _scan(self) -> None:
        if sys.platform == "win32":
            self._scan_windows()
        else:
            self._scan_linux()

    def _scan_windows(self) -> None:
        cache = self._effective_cache_dir()
        for lnk in _iter_windows_shortcuts(_windows_shortcut_dirs()):
            name = lnk.stem
            if not name or _is_noise_shortcut(name):
                continue
            png = _cached_provider_png(lnk, cache)
            icon = QIcon(str(png)) if png is not None else QIcon.fromTheme(_FALLBACK_APP_ICON)
            self._entries.append((name, str(lnk), icon))
        self._entries.sort(key=lambda item: item[0].casefold())

    def _scan_linux(self) -> None:
        fallback = QIcon.fromTheme(_FALLBACK_APP_ICON)
        for name, desktop, icon_key in scan_installed_linux_apps(self._desktop_dirs):
            icon = QIcon.fromTheme(icon_key) if icon_key else QIcon()
            if icon.isNull():
                resolved = core_icons.icon_from_desktop_file(desktop)
                if resolved is not None and resolved.is_file():
                    icon = QIcon(str(resolved))
            if icon.isNull():
                icon = fallback
            self._entries.append((name, str(desktop), icon))

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        self.list_widget.clear()
        shown = 0
        for name, path_str, icon in self._entries:
            if needle and needle not in name.lower() and needle not in Path(path_str).stem.lower():
                continue
            item = QListWidgetItem(icon, name)
            item.setData(Qt.UserRole, path_str)
            item.setToolTip(path_str)
            self.list_widget.addItem(item)
            shown += 1
        self.count_label.setText(tr("app_picker.count", n=shown))
