"""Linux (Cinnamon) backend implementation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Sequence

from ...models import Group
from ...storage import ConfigStore
from ..base import PlatformBackend
from . import desktop as _desktop
from . import hotkeys as _hotkeys
from . import panel as _panel


class LinuxCinnamonBackend(PlatformBackend):
    name = "linux"
    supports_direct_pin = True
    supports_cinnamon_hotkeys = True
    supports_win_hotkeys = False

    def launcher_file_name(self, dir_name: str) -> str:
        return _desktop.desktop_file_name(dir_name)

    def install_launcher(
        self,
        group: Group,
        store: ConfigStore,
        dir_name: str,
        target_dir: Path | str | None = None,
        python: str | None = None,
        icons_root: Path | str | None = None,
        default_icon: Path | str | None = None,
    ) -> Path:
        return _desktop.install_launcher(
            group, store, dir_name, target_dir, python, icons_root
        )

    def remove_launcher(
        self,
        dir_name: str,
        target_dir: Path | str | None = None,
        icons_root: Path | str | None = None,
    ) -> bool:
        return _desktop.remove_launcher(dir_name, target_dir, icons_root)

    def read_launcher_name(self, path: str | os.PathLike[str]) -> str | None:
        return _desktop.read_desktop_name(path)

    def pinned_desktop_ids(
        self, config_dir: Path | None = None, runner: Callable | None = None
    ) -> set[str]:
        return _panel.pinned_desktop_ids(
            config_dir, runner if runner is not None else _panel._run
        )

    def pin_to_panel(
        self,
        desktop_id: str,
        runner: Callable | None = None,
        config_dir: Path | None = None,
        refresh: bool = True,
    ) -> str:
        if not _hotkeys.is_cinnamon():
            raise _panel.PinError("เดสก์ท็อปไม่ใช่ Cinnamon")
        if os.environ.get("TASKBARGROUPS_NO_PIN"):
            raise _panel.PinError("ปิดการปักหมุดอัตโนมัติ (TASKBARGROUPS_NO_PIN)")
        return _panel.pin_to_panel(
            desktop_id,
            runner if runner is not None else _panel._run,
            config_dir,
            refresh,
        )

    def unpin_from_panel(
        self,
        desktop_id: str,
        runner: Callable | None = None,
        config_dir: Path | None = None,
        refresh: bool = True,
    ) -> bool:
        if not _hotkeys.is_cinnamon():
            raise _panel.PinError("เดสก์ท็อปไม่ใช่ Cinnamon")
        if os.environ.get("TASKBARGROUPS_NO_PIN"):
            raise _panel.PinError("ปิดการปักหมุดอัตโนมัติ (TASKBARGROUPS_NO_PIN)")
        return _panel.unpin_from_panel(
            desktop_id,
            runner if runner is not None else _panel._run,
            config_dir,
            refresh,
        )

    def available_actions(self) -> Sequence[str]:
        return ("grouped-window-list", "panel-launchers")
