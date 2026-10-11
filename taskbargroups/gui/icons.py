"""ตัวช่วยแปลง shortcut/กลุ่ม เป็น QIcon."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFileInfo
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileIconProvider

from taskbargroups.core.models import Group, Shortcut
from taskbargroups.core.storage import ConfigStore

_provider = QFileIconProvider()
_FALLBACK = "application-x-executable"


def _from_file(path: Path) -> QIcon | None:
    if path.is_file():
        return QIcon(str(path))
    return None


def shortcut_icon(shortcut: Shortcut, store: ConfigStore, dir_name: str) -> QIcon:
    cached = store.resolve_relative(dir_name, shortcut.icon)
    if cached is not None:
        icon = _from_file(cached)
        if icon is not None:
            return icon
    target = shortcut.target.strip()
    if target:
        icon = _from_file(Path(target))
        if icon is not None:
            return icon
    return QIcon.fromTheme(_FALLBACK)


def group_icon(group: Group, store: ConfigStore, dir_name: str) -> QIcon:
    cached = store.resolve_relative(dir_name, group.icon)
    if cached is not None:
        icon = _from_file(cached)
        if icon is not None:
            return icon
    return QIcon.fromTheme("folder")
