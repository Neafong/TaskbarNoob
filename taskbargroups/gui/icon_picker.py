"""หน้าต่างเลือกไอคอนจากระบบ (Linux Freedesktop themes / Windows DLL + Start Menu)."""

from __future__ import annotations

import hashlib
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

from taskbargroups.core.i18n import tr

from .icons import extract_dll_icon_png, extract_os_icon_png, list_dll_icons

_ICON_SUFFIXES = {".png", ".svg", ".xpm", ".jpg", ".jpeg"}
_ICON_SCAN_LIMIT = 4000
_ICON_DISPLAY_LIMIT = 1000

_PROVIDER_ICON_SUFFIXES = frozenset(
    {".exe", ".lnk", ".bat", ".cmd", ".msc", ".cpl", ".scr", ".url"}
)
_PROVIDER_ICON_CACHE_DIRNAME = "provider-icons-v3"

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


def _provider_png(source: Path, dest: Path, size: int = 256) -> Path | None:
    """สกัดไอคอนที่ฝังในไฟล์ของ OS (.exe/.lnk/.dll) ออกมาเป็น PNG."""
    return extract_os_icon_png(source, dest, size)


def _cached_provider_png(source: Path, base: Path, size: int = 256) -> Path | None:
    """สกัดไอคอนจากไฟล์ OS แล้วแคชเป็น PNG (ข้ามถ้าแคชยังใหม่กว่าไฟล์ต้นทาง)."""
    try:
        mtime = source.stat().st_mtime
    except OSError:
        return None
    digest = hashlib.sha1(f"{source}|{int(mtime)}".encode("utf-8")).hexdigest()[:16]
    dest = base / f"{digest}.png"
    if dest.is_file():
        try:
            if dest.stat().st_mtime >= mtime:
                return dest
        except OSError:
            pass
    return _provider_png(source, dest, size)


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
        self._dll_entries: list[tuple[str, Path, int, QIcon]] = []
        self._apps_scanned = False
        self._cache_dir = cache_dir

        layout = QVBoxLayout(self)
        self.source_combo: QComboBox | None = None
        if sys.platform == "win32":
            self.source_combo = QComboBox()
            self.source_combo.addItem(tr("system_icon.source_system"), "system")
            self.source_combo.addItem(tr("system_icon.source_apps"), "apps")
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
        if (
            self.source_combo is not None
            and self.source_combo.currentData() == "apps"
            and not self._apps_scanned
        ):
            self._scan_windows()
        self._apply_filter(self.search.text())

    def _scan(self) -> None:
        if sys.platform == "win32":
            self._scan_windows_dlls()
        else:
            self._scan_linux()

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

    def _scan_linux(self) -> None:
        bases = dict.fromkeys(
            [Path(p) for p in QIcon.themeSearchPaths()] + [Path("/usr/share/icons")]
        )
        for base in bases:
            if not base.is_dir() or len(self._names) >= _ICON_SCAN_LIMIT:
                continue
            for theme in base.iterdir():
                if not theme.is_dir():
                    continue
                for size_dir in theme.iterdir():
                    if not size_dir.is_dir():
                        continue
                    try:
                        size = int(size_dir.name.split("x")[0])
                    except (ValueError, IndexError):
                        size = 0
                    for category in size_dir.iterdir():
                        if not category.is_dir():
                            continue
                        for icon_file in category.iterdir():
                            if icon_file.suffix.lower() not in _ICON_SUFFIXES:
                                continue
                            self._best_icon(icon_file, size)
                            if len(self._names) >= _ICON_SCAN_LIMIT:
                                return

    def _best_icon(self, icon_file: Path, size: int) -> None:
        name = icon_file.stem
        if not name:
            return
        current = self._names.get(name)
        if current is None or self._priority(icon_file, size) > self._priority(
            Path(current), 0
        ):
            self._names[name] = str(icon_file)

    @staticmethod
    def _priority(icon_file: Path, size: int) -> int:
        score = 0
        if icon_file.suffix.lower() == ".svg":
            score += 100000
        score += size
        if icon_file.parent.name.startswith("apps"):
            score += 50
        return score

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        self.grid.clear()
        shown = 0
        capped = False
        if self.source_combo is not None and self.source_combo.currentData() == "system":
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
