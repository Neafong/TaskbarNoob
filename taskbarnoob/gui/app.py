"""Application bootstrap (`run`, `_run_flyout`, Windows hotkey registration)."""

from __future__ import annotations

import sys

from PySide6.QtGui import QCursor, QIcon
from PySide6.QtWidgets import QApplication

from taskbarnoob.core.i18n import setup
from taskbarnoob.core.paths import app_icon_path
from taskbarnoob.core.platform import get_backend
from taskbarnoob.core.platform.linux.hotkeys import hotkey_slot
from taskbarnoob.core.settings import Settings
from taskbarnoob.core.storage import ConfigStore

from .flyout import FlyoutController
from .theme import apply_theme, resolve_theme


def run(
    argv: list[str] | None = None,
    open_group: str | None = None,
    center: bool = False,
) -> int:
    backend = get_backend()
    if open_group:
        backend.set_group_process_id(open_group)
    else:
        backend.set_app_process_id()
    app = QApplication.instance() or QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("TaskbarNoob")
    app.setApplicationDisplayName("TaskbarNoob")
    app.setDesktopFileName("taskbarnoob")
    icon_path = app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    settings = Settings()
    setup(settings.get_language())
    apply_theme(app, resolve_theme(settings.get_theme(), app))
    if open_group:
        return _run_flyout(app, open_group, center)
    from .main_window import MainWindow

    window = MainWindow()
    if backend.supports_win_hotkeys:
        _register_saved_win_hotkeys(app, window, settings)
    window.show()
    return app.exec()


def _register_saved_win_hotkeys(app, window, settings) -> None:
    """ลงทะเบียน hotkey ที่จำไว้ใน settings ใหม่ทุกครั้งที่เปิดแอป (Windows)."""
    from .win32_hotkey import WinHotkeyFilter, registry

    try:
        if getattr(sys, "frozen", False):
            exe_args = [sys.executable]
        else:
            exe_args = [sys.executable, "-m", "taskbarnoob"]
        hwnd = int(window.winId())
    except (TypeError, ValueError):
        return
    hotkey_filter = WinHotkeyFilter(registry, exe_args, window)
    app.installNativeEventFilter(hotkey_filter)
    app._win_hotkey_filter = hotkey_filter
    store = ConfigStore()
    try:
        dir_names = store.list_groups()
    except Exception:
        return
    saved = settings.get_hotkeys()
    for dir_name in dir_names:
        slot = hotkey_slot(dir_name)
        binding = saved.get(slot)
        if not binding:
            continue
        try:
            registry.register_slot(slot, dir_name, binding, hwnd)
        except OSError:
            continue


def _run_flyout(app: QApplication, dir_name: str, center: bool = False) -> int:
    point = QCursor.pos()
    store = ConfigStore()
    controller = FlyoutController(app, store)
    if controller.try_delegate(dir_name, point, center):
        return 0
    controller.start_primary(dir_name, point, center)
    code = app.exec()
    controller.shutdown()
    return code
