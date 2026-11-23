"""Windows 11 platform backend implementation."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Callable, Sequence

from ...models import Group
from ...paths import app_dir
from ...storage import ConfigStore
from ..base import PlatformBackend
from ..linux.panel import PinError
from .aumid import aumid as _group_aumid
from .aumid import set_app_aumid, set_process_aumid
from . import ico as _ico
from . import lnk as _lnk
from . import pin as _pin


def _open_target(python: str | None = None) -> tuple[str, str, str]:
    if getattr(sys, "frozen", False):
        return sys.executable, "", str(app_dir())
    if python:
        return python, "", str(app_dir())
    return sys.executable, "", str(app_dir())


class Win32Backend(PlatformBackend):
    name = "win32"
    supports_direct_pin = False
    supports_cinnamon_hotkeys = False
    supports_win_hotkeys = True

    def set_app_process_id(self) -> None:
        set_app_aumid()

    def set_group_process_id(self, dir_name: str) -> None:
        set_process_aumid(dir_name)

    def launcher_file_name(self, dir_name: str) -> str:
        return _lnk.lnk_name(dir_name)

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
        exe, _args, workdir = _open_target(python)
        directory = (
            Path(target_dir) if target_dir is not None else _lnk.shortcuts_dir()
        )
        icon = store.resolve_relative(dir_name, group.icon)
        icon_location = ""
        if icon is not None and icon.is_file():
            if icon.suffix.lower() == ".ico":
                icon_location = str(icon)
            elif icon.suffix.lower() == ".png":
                ico = _ico.png_to_ico(icon)
                icon_location = str(ico) if ico is not None else ""
        if not icon_location and default_icon is not None:
            fallback = Path(default_icon)
            if fallback.is_file():
                ico = (
                    fallback
                    if fallback.suffix.lower() == ".ico"
                    else _ico.png_to_ico(fallback)
                )
                icon_location = str(ico) if ico is not None else ""
        return _lnk.create_lnk(
            directory / _lnk.lnk_name(dir_name),
            exe,
            arguments=f'--open "{dir_name}"',
            workdir=workdir,
            icon_location=icon_location,
            aumid_value=_group_aumid(dir_name),
            description=group.name or dir_name,
        )

    def remove_launcher(
        self,
        dir_name: str,
        target_dir: Path | str | None = None,
        icons_root: Path | str | None = None,
    ) -> bool:
        directory = (
            Path(target_dir) if target_dir is not None else _lnk.shortcuts_dir()
        )
        path = directory / _lnk.lnk_name(dir_name)
        if not path.is_file():
            return False
        try:
            path.unlink()
        except OSError as exc:
            raise _lnk.WindowsError(str(exc)) from exc
        return True

    def read_launcher_name(self, path: str | os.PathLike[str]) -> str | None:
        if Path(path).suffix.lower() == ".lnk":
            target = _lnk.read_lnk_target(path)
            return Path(target).stem if target else None
        from ..linux.desktop import read_desktop_name

        return read_desktop_name(path)

    def pinned_desktop_ids(
        self, config_dir: Path | None = None, runner: Callable | None = None
    ) -> set[str]:
        pinned = set(_pin.pinned_aumid_files())
        if not pinned:
            return set()
        try:
            names = ConfigStore(config_dir).list_groups()
        except OSError:
            return set()
        return {
            _lnk.lnk_name(name) for name in names if _group_aumid(name) in pinned
        }

    def pin_to_panel(
        self,
        desktop_id: str,
        runner: Callable | None = None,
        config_dir: Path | None = None,
        refresh: bool = True,
    ) -> str:
        source = _lnk.shortcuts_dir() / desktop_id
        if not source.is_file():
            raise PinError(f"หาไฟล์ {desktop_id} ใน Start Menu ไม่เจอ (ติดตั้ง launcher ก่อน)")
        try:
            _pin.pin_to_taskbar(
                source,
                runner=runner if runner is not None else _lnk._run_lenient,
            )
        except _lnk.WindowsError as exc:
            raise PinError(str(exc)) from exc
        return "taskbar-manual"

    def unpin_from_panel(
        self,
        desktop_id: str,
        runner: Callable | None = None,
        config_dir: Path | None = None,
        refresh: bool = True,
    ) -> bool:
        try:
            return _pin.unpin_from_taskbar(desktop_id)
        except _lnk.WindowsError as exc:
            raise PinError(str(exc)) from exc

    def stale_pin_label(
        self,
        dir_name: str,
        env: dict | None = None,
        home: Path | str | None = None,
        pinned: dict[str, str] | None = None,
    ) -> bool:
        return _pin.stale_pin_label(dir_name, env, home, pinned)

    def available_actions(self) -> Sequence[str]:
        return ("taskbar-manual",)
