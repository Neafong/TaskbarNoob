"""หน้าต่างเลือกไอคอนจากระบบ (Linux Freedesktop themes แยกหมวด / Windows DLL + Start Menu)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from typing import Iterable

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core import icons as core_icons
from taskbargroups.core.i18n import tr

from .icons import (
    _PROVIDER_ICON_CACHE_DIRNAME,
    _cached_provider_png,
    _provider_png,
    extract_dll_icon_png,
    list_dll_icons,
)

_ICON_SCAN_LIMIT = 4000
_ICON_DISPLAY_LIMIT = 1000

_PROVIDER_ICON_SUFFIXES = frozenset(
    {".exe", ".lnk", ".bat", ".cmd", ".msc", ".cpl", ".scr", ".url"}
)

_NOISE_SHORTCUT_WORDS = (
    "uninstall",
    "remove ",
    "readme",
    "manual",
    "license",
    "release notes",
    "ถอนการติดตั้ง",
    "คู่มือ",
)


def _windows_shortcut_dirs() -> list[Path]:
    """โฟลเดอร์ Start Menu ของผู้ใช้ + ทั้งเครื่อง (Windows)."""
    dirs: list[Path] = []
    for env_name in ("ProgramData", "APPDATA"):
        root = os.environ.get(env_name)
        if not root:
            continue
        dirs.append(Path(root) / "Microsoft" / "Windows" / "Start Menu" / "Programs")
    out: list[Path] = []
    for d in dirs:
        try:
            if d.is_dir():
                out.append(d)
        except OSError:
            continue
    return out


def _iter_windows_shortcuts(dirs: Iterable[Path]):
    """เดินหาไฟล์ .lnk ทุกไฟล์ในโฟลเดอร์ Start Menu (ไม่รวมตัวโมดูลเองซ้ำ)."""
    seen: set[str] = set()
    for base in dirs:
        try:
            entries = sorted(base.rglob("*.lnk"))
        except OSError:
            continue
        for path in entries:
            key = path.name.lower()
            if key in seen:
                continue
            seen.add(key)
            yield path


def _is_noise_shortcut(name: str) -> bool:
    """กรองทางลัดที่ไม่ใช่ตัวแอปจริง (เช่น Uninstall, Readme, Manual)."""
    low = name.strip().lower()
    if not low:
        return True
    if any(word in low for word in _NOISE_SHORTCUT_WORDS):
        return True
    return low.endswith((" help", " docs", " documentation"))


def _windows_system_icon_dlls() -> list[Path]:
    """ไฟล์ DLL ไอคอนระบบมาตรฐานของ Windows (imageres.dll, shell32.dll)."""
    sys32 = Path(os.environ.get("SystemRoot") or r"C:\Windows") / "System32"
    return [
        p
        for name in ("imageres.dll", "shell32.dll")
        if (p := sys32 / name).is_file()
    ]


class SystemIconDialog(QDialog):
    """สแกนรายชื่อไอคอนจากชุดธีมของระบบ แล้วให้เลือก/ค้นหาไอคอนได้."""

    def __init__(
        self, parent: QWidget | None = None, cache_dir: Path | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("system_icon.title"))
        self.resize(560, 480)
        self._path: str | None = None
        self._names: dict[str, str] = {}
        self._linux_cache: dict[str, dict[str, str]] = {}
        self._dll_entries: list[tuple[str, Path, int, QIcon]] = []
        self._apps_scanned = False
        self._cache_dir = cache_dir

        layout = QVBoxLayout(self)
        self.source_combo = QComboBox()
        if sys.platform == "win32":
            self.source_combo.addItem(tr("system_icon.source_system"), "system")
            self.source_combo.addItem(tr("system_icon.source_apps"), "apps")
        else:
            self.source_combo.addItem(tr("system_icon.linux_categories"), "categories")
            self.source_combo.addItem(tr("system_icon.linux_apps"), "apps")
            self.source_combo.addItem(tr("system_icon.linux_all"), "all")
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        layout.addWidget(self.source_combo)

        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("system_icon.search_placeholder"))
        self.search.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search)

        self.grid = QListWidget()
        self.grid.setViewMode(QListView.IconMode)
        self.grid.setIconSize(QSize(40, 40))
        self.grid.setGridSize(QSize(64, 64))
        self.grid.setResizeMode(QListView.Adjust)
        self.grid.setMovement(QListView.Static)
        self.grid.setWordWrap(False)
        self.grid.setSelectionMode(QAbstractItemView.SingleSelection)
        self.grid.itemDoubleClicked.connect(lambda _item: self.accept())
        self.grid.itemActivated.connect(lambda _item: self.accept())
        layout.addWidget(self.grid, 1)

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
        if result == QDialog.Accepted and self.grid.currentItem() is not None:
            data = self.grid.currentItem().data(Qt.UserRole)
            if isinstance(data, tuple) and len(data) == 3 and data[0] == "dll":
                _, dll_str, idx = data
                dll_path = Path(dll_str)
                dest = self._effective_cache_dir() / f"{dll_path.stem}_{idx}.png"
                png = extract_dll_icon_png(dll_path, idx, dest, size=256)
                self._path = str(png) if png is not None else None
            else:
                self._path = data
        super().done(result)

    def _on_source_changed(self) -> None:
        mode = self.source_combo.currentData()
        if sys.platform == "win32":
            if mode == "apps" and not self._apps_scanned:
                self._scan_windows()
        else:
            self._scan_linux(str(mode or "categories"))
        self._apply_filter(self.search.text())

    def _scan(self) -> None:
        if sys.platform == "win32":
            self._scan_windows_dlls()
        else:
            self._scan_linux(str(self.source_combo.currentData() or "categories"))

    def _scan_windows_dlls(self) -> None:
        """Windows: ดึงไอคอนระบบจาก imageres.dll + shell32.dll."""
        self._dll_entries.clear()
        for dll in _windows_system_icon_dlls():
            stem = dll.stem.lower()
            for idx, icon in list_dll_icons(dll):
                self._dll_entries.append((f"{stem} #{idx}", dll, idx, icon))

    def _scan_windows(self) -> None:
        """Windows: สกัดไอคอนแอปจาก .lnk ใน Start Menu (กรอง Uninstall/Manual ออก)."""
        self._apps_scanned = True
        cache = self._effective_cache_dir()
        for lnk in _iter_windows_shortcuts(_windows_shortcut_dirs()):
            if len(self._names) >= _ICON_SCAN_LIMIT:
                return
            name = lnk.stem
            if not name or name in self._names or _is_noise_shortcut(name):
                continue
            png = _cached_provider_png(lnk, cache)
            if png is not None:
                self._names[name] = str(png)

    def _linux_search_dirs(self) -> list[Path]:
        return list(
            dict.fromkeys(
                [Path(p) for p in QIcon.themeSearchPaths()]
                + core_icons.theme_search_dirs()
            )
        )

    def _scan_linux(self, category: str = "categories") -> None:
        cached = self._linux_cache.get(category)
        if cached is None:
            scanned = core_icons.scan_theme_icons(
                search_dirs=self._linux_search_dirs(),
                category=category,
                limit=_ICON_SCAN_LIMIT,
            )
            cached = {name: str(path) for name, path in scanned.items()}
            self._linux_cache[category] = cached
        self._names = cached

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        self.grid.clear()
        shown = 0
        capped = False
        if sys.platform == "win32" and self.source_combo.currentData() == "system":
            for label, dll_path, idx, icon in self._dll_entries:
                if needle and needle not in label.lower():
                    continue
                if shown >= _ICON_DISPLAY_LIMIT:
                    capped = True
                    break
                item = QListWidgetItem(icon, label)
                item.setData(Qt.UserRole, ("dll", str(dll_path), idx))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                item.setToolTip(label)
                self.grid.addItem(item)
                shown += 1
        else:
            for name in sorted(self._names):
                if needle and needle not in name.lower():
                    continue
                if shown >= _ICON_DISPLAY_LIMIT:
                    capped = True
                    break
                item = QListWidgetItem(QIcon(self._names[name]), name)
                item.setData(Qt.UserRole, self._names[name])
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
                item.setToolTip(name)
                self.grid.addItem(item)
                shown += 1
        if needle:
            self.count_label.setText(tr("system_icon.count", n=shown))
        elif capped:
            self.count_label.setText(tr("system_icon.count_capped", n=shown))
        else:
            self.count_label.setText(tr("system_icon.count", n=shown))


_SystemIconDialog = SystemIconDialog

__all__ = [
    "SystemIconDialog",
    "_PROVIDER_ICON_CACHE_DIRNAME",
    "_PROVIDER_ICON_SUFFIXES",
    "_SystemIconDialog",
    "_cached_provider_png",
    "_is_noise_shortcut",
    "_iter_windows_shortcuts",
    "_provider_png",
    "_windows_shortcut_dirs",
    "_windows_system_icon_dlls",
]
