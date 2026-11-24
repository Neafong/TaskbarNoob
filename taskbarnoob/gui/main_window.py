"""หน้าต่างหลัก: จัดการรายการกลุ่ม (Phase 2 MVP)."""

from __future__ import annotations

import os
import sys

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from taskbarnoob.core import icons as core_icons
from taskbarnoob.core.i18n import tr
from taskbarnoob.core.platform import (
    HotkeyError,
    PinError,
    desktop_file_name,
    get_backend,
    install_launcher,
    is_cinnamon,
    launcher_id,
    pin_to_panel,
    pinned_desktop_ids,
    remove_launcher,
    stale_pin_label,
    unpin_from_panel,
)
from taskbarnoob.core.platform.linux.hotkeys import (
    cinnamon_to_display,
    group_hotkeys,
    hotkey_slot,
    unregister_cinnamon_hotkey,
)
from taskbarnoob.core.platform.linux.panel import reload_grouped_window_applet
from taskbarnoob.core.platform.win32.hotkey import unregister_hotkey
from taskbarnoob.core.settings import Settings
from taskbarnoob.core.storage import ConfigStore, StorageError, safe_dir_name
from taskbarnoob.gui.win32_hotkey import registry as win_registry

from .about_dialog import AboutDialog
from .app import _register_saved_win_hotkeys, _run_flyout, run
from .button_icons import themed_icon
from .dialogs import show_information, show_question, show_warning
from .flyout import FlyoutWindow
from .group_editor import GroupEditor
from .group_list import (
    PINNED_ROLE,
    GroupListWidget,
    _RowDropHighlightDelegate,
    _style_menu,
)
from .hotkey_dialog import HotkeyDialog
from .icons import app_window_icon, cache_provider_icon, group_icon
from .settings_dialog import SettingsDialog
from .theme import app_text_color

ICON_SIZE = QSize(32, 32)

_NAV_BUTTON_ICONS = {
    "main.add_group": "plus-fill.svg",
    "main.edit": "pencil-simple-fill.svg",
    "main.delete": "trash-fill.svg",
}
_SETUP_ICON = "gear-six-fill.svg"


def _apply_nav_icon(button: QPushButton, kind: str) -> None:
    """ติดไอคอน SVG ของเราให้ปุ่มหน้าหลัก (tint ด้วย app text ตรงๆ — ไม่รอ palette event)."""
    icon = themed_icon(kind, app_text_color())
    if not icon.isNull():
        button.setIcon(icon)


def _pin_tooltip(group, pinned: bool, dir_name: str = "", stale: bool | None = None) -> str:
    """ข้อความช่วยเหลือของปุ่มสถานะ (ต่างกันตาม OS).

    - Linux: ปัก/ถอนได้จริง → บอกสถานะตรงๆสั้นๆ
    - Windows: ปุ่มเปิดโฟลเดอร์ให้ลากวาง → ต้องบอกขั้นตอนให้ครบ

    `stale` = ผลตรวจป้ายชื่อเก่า (คำนวณครั้งเดียวต่อ refresh ได้) — ไม่ส่ง/None
    จะเรียก `stale_pin_label` เอง (พฤติกรรมเดิม)
    """
    if not get_backend().supports_direct_pin:
        if pinned:
            text = tr("main.win_pinned_tip")
            if stale is None:
                stale = bool(dir_name) and stale_pin_label(dir_name)
            if stale:
                text += tr("main.win_pin_label_stale")
            return text
        return tr("main.win_not_pinned_tip", file=desktop_file_name(dir_name or ""))
    return tr("main.pinned_tip") if pinned else tr("main.not_pinned_tip")


class MainWindow(QMainWindow):
    def __init__(self, store: ConfigStore | None = None) -> None:
        super().__init__()
        self.store = store or ConfigStore()
        self._flyout: FlyoutWindow | None = None
        self._tray: QSystemTrayIcon | None = None
        self._tray_menu: QMenu | None = None
        self._tray_actions: dict[str, QAction] = {}
        self._force_quit: bool = False

        self.setWindowTitle(tr("app.title"))
        self.resize(660, 420)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        self.list = GroupListWidget()
        self.list.itemDoubleClicked.connect(lambda _item: self.on_edit())
        self.list.orderChanged.connect(self._on_rows_moved)
        self.list.pinClicked.connect(self.on_pin)
        self.list.contextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.list)

        self._nav_buttons: list[tuple[str, QPushButton]] = []
        row = QHBoxLayout()
        for key, slot in (
            ("main.add_group", self.on_add),
            ("main.edit", self.on_edit),
            ("main.delete", self.on_delete),
        ):
            button = QPushButton(tr(key))
            _apply_nav_icon(button, _NAV_BUTTON_ICONS[key])
            button.clicked.connect(slot)
            row.addWidget(button)
            self._nav_buttons.append((key, button))
        row.addStretch(1)
        self.setup_button = QPushButton()
        self.setup_button.setToolTip(tr("main.setup_tooltip"))
        self.setup_button.setIcon(themed_icon(_SETUP_ICON, app_text_color()))
        self.setup_button.setIconSize(QSize(26, 26))
        self.setup_button.setFixedWidth(52)
        self.setup_button.clicked.connect(self._open_setup_menu)
        row.addWidget(self.setup_button)
        layout.addLayout(row)

        self.refresh()
        self._sync_pinned_launchers()
        self.sync_tray()

    def sync_tray(self) -> None:
        """เปิด/ปิด System Tray Icon ตามค่า minimize_to_tray ใน settings."""
        enabled = Settings(self.store.config_dir).get_minimize_to_tray()
        app = QApplication.instance()
        if enabled and QSystemTrayIcon.isSystemTrayAvailable():
            if self._tray is None:
                self._create_tray()
            if self._tray is not None:
                self._retranslate_tray()
                self._tray.show()
            if app is not None:
                app.setQuitOnLastWindowClosed(False)
        else:
            if self._tray is not None:
                self._tray.hide()
            if app is not None:
                app.setQuitOnLastWindowClosed(True)

    def _create_tray(self) -> None:
        icon = app_window_icon()
        if icon.isNull():
            app = QApplication.instance()
            if app is not None:
                icon = app.windowIcon()
        tray = QSystemTrayIcon(icon, self)
        menu = _style_menu(QMenu(self))
        open_act = menu.addAction(tr("tray.open"), self.show_from_tray)
        font = open_act.font()
        font.setBold(True)
        open_act.setFont(font)
        settings_act = menu.addAction(tr("tray.settings"), self.open_settings)
        menu.addSeparator()
        quit_act = menu.addAction(tr("tray.quit"), self.quit_app)
        tray.setContextMenu(menu)
        tray.setToolTip(tr("tray.tooltip"))
        tray.activated.connect(self._on_tray_activated)
        self._tray = tray
        self._tray_menu = menu
        self._tray_actions = {
            "tray.open": open_act,
            "tray.settings": settings_act,
            "tray.quit": quit_act,
        }

    def _retranslate_tray(self) -> None:
        if self._tray is None:
            return
        self._tray.setToolTip(tr("tray.tooltip"))
        for key, action in self._tray_actions.items():
            action.setText(tr(key))

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self.show_from_tray()

    def show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def quit_app(self) -> None:
        self._force_quit = True
        if self._tray is not None:
            self._tray.hide()
        app = QApplication.instance()
        if app is not None:
            app.setQuitOnLastWindowClosed(True)
        self.close()
        if app is not None:
            app.quit()

    def closeEvent(self, event) -> None:
        if (
            not self._force_quit
            and self._tray is not None
            and self._tray.isVisible()
            and Settings(self.store.config_dir).get_minimize_to_tray()
        ):
            event.ignore()
            self.hide()
            return
        if self._tray is not None:
            self._tray.hide()
        super().closeEvent(event)

    def _sync_pinned_launchers(self) -> None:
        """ซ่อม launcher ของกลุ่มที่ปักไว้ที่ยังชี้ไอค่อนเป็น path สัมบูรณ์.

        ไอคอนเดิมชี้ไฟล์บนไดรฟ์ (เช่น /mnt/Backup) ที่ mount หลัง panel เริ่มทำงาน
        → ตอน boot ไอคอนหาย. ติดตั้งไอคอนเข้า icon theme (บนดิสก์ราก) แล้วชี้
        ด้วยชื่อ ให้ panel หาเจอเสมอ. ทำครั้งเดียวต่อ launcher. (Linux เท่านั้น)
        """
        if not get_backend().supports_direct_pin:
            return
        from taskbarnoob.core.platform.linux.desktop import applications_dir
        from taskbarnoob.core.platform.linux.migrate import migrate_legacy_linux_state

        migrate_legacy_linux_state(self.store)
        pinned_ids = pinned_desktop_ids()
        if not pinned_ids:
            return
        changed = False
        for dir_name in self.store.list_groups():
            desktop_id = desktop_file_name(dir_name)
            if desktop_id not in pinned_ids:
                continue
            path = applications_dir() / desktop_id
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                text = ""
            if f"Icon={launcher_id(dir_name)}" in text:
                continue
            try:
                group = self.store.load_group(dir_name)
                self._install_launcher(group, dir_name)
                changed = True
            except (StorageError, OSError):
                continue
        if changed:
            reload_grouped_window_applet()

    def refresh_icons(self) -> None:
        """ทาสีไอคอนปุ่มใหม่ตามธีมปัจจุบัน (เรียกหลังสลับธีม — ใช้ app palette ตรงๆ)."""
        for key, button in self._nav_buttons:
            _apply_nav_icon(button, _NAV_BUTTON_ICONS[key])
        self.setup_button.setIcon(themed_icon(_SETUP_ICON, app_text_color()))
        # บังคับ list + ลูกทุกตัวใช้ palette ใหม่ (QListWidget ไม่ auto-refresh)
        app = QApplication.instance()
        if app is not None:
            palette = app.palette()
            self.setPalette(palette)
            self.list.setPalette(palette)
            self.list.viewport().setPalette(palette)
            for i in range(self.list.count()):
                item = self.list.item(i)
                if item is not None:
                    widget = self.list.itemWidget(item)
                    if widget is not None:
                        widget.setPalette(palette)
            self.list.viewport().update()

    def retranslate(self) -> None:
        """อัปเดตข้อความ UI ตามภาษาที่ active อยู่ (เรียกหลังสลับภาษาแบบทันที)."""
        self.setWindowTitle(tr("app.title"))
        for key, button in self._nav_buttons:
            button.setText(tr(key))
        self.refresh_icons()
        self.setup_button.setToolTip(tr("main.setup_tooltip"))
        self._retranslate_tray()
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        pinned_ids = pinned_desktop_ids()
        stale_files: dict[str, str] | None = None
        if not get_backend().supports_direct_pin:
            # สแกน User Pinned ครั้งเดียว ใช้ทั้งหา stale ต่อกลุ่ม (เลี่ยง COM ซ้ำ)
            from taskbarnoob.core.platform.win32.pin import pinned_aumid_files

            stale_files = pinned_aumid_files()
        dir_names = self.store.list_groups()
        try:
            bindings = group_hotkeys([hotkey_slot(name) for name in dir_names])
        except Exception:
            bindings = {}
        if sys.platform == "win32":
            # Windows ไม่มีที่เก็บ hotkey ของระบบ — อ่านที่แอปจำไว้ใน settings
            from taskbarnoob.core.settings import Settings

            saved = Settings(self.store.config_dir).get_hotkeys()
            for name in dir_names:
                slot = hotkey_slot(name)
                if slot in saved:
                    bindings[slot] = saved[slot]
        for dir_name in dir_names:
            try:
                group = self.store.load_group(dir_name)
            except StorageError:
                continue
            # กลุ่มเดียวที่วาดไม่ขึ้นห้ามทำให้ทั้งรายการหาย
            # (เคยเจออาการเพิ่มกลุ่มแล้วไม่โชว์ เพราะข้อต่อไปพังแล้วลูปหยุด)
            try:
                label = f"{group.name}  ({len(group.items)})"
                binding = bindings.get(hotkey_slot(dir_name))
                if binding:
                    label += tr("main.hotkey_inline", keys=cinnamon_to_display(binding))
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, dir_name)
                is_pinned = desktop_file_name(dir_name) in pinned_ids
                item.setData(PINNED_ROLE, is_pinned)
                stale = None
                if stale_files is not None and is_pinned:
                    from taskbarnoob.core.platform import win32 as _w32

                    filename = stale_files.get(_w32.aumid(dir_name))
                    stale = filename is not None and filename != _w32.lnk_name(dir_name)
                item.setToolTip(
                    f"{group.name} — " + _pin_tooltip(group, is_pinned, dir_name, stale)
                )
                item.setIcon(group_icon(group, self.store, dir_name))
                self.list.addItem(item)
            except Exception:
                continue

    def _on_rows_moved(self, *_args) -> None:
        order = [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]
        try:
            self.store.save_order(order)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))

    def _current_dir_name(self) -> str | None:
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item is not None else None

    def on_add(self) -> None:
        dialog = GroupEditor(self.store, self)
        if dialog.exec() == QDialog.Accepted:
            self._persist(dialog)

    def on_edit(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        dialog = GroupEditor(self.store, self, group=group, dir_name=dir_name)
        if dialog.exec() == QDialog.Accepted:
            self._persist(dialog)

    def _unique_group_name(self, desired: str, old_dir: str | None) -> str:
        return self.store.unique_group_name(desired, old_dir, use_parens=False)

    def _persist(self, dialog: GroupEditor) -> None:
        group = dialog.result_group()
        old_dir = dialog.dir_name
        original_name = group.name
        group.name = self._unique_group_name(group.name, old_dir)
        new_dir = safe_dir_name(group.name)
        # เทียบด้วย normcase — บน Windows/macOS โฟลเดอร์ไม่สนตัวพิมพ์
        # ถ้าเทียบตรงๆ `Test` กับ `test` คือที่เดียวกัน แต่โค้ดจะคิดว่า "เปลี่ยนชื่อ"
        # แล้วไปชนกับตัวเอง → เด้ง "ชื่อซ้ำ" ทั้งที่ผู้ใช้ไม่ได้แตะชื่อเลย
        renamed = bool(old_dir and os.path.normcase(old_dir) != os.path.normcase(new_dir))
        old_desktop_id = desktop_file_name(old_dir) if renamed else ""
        was_pinned = renamed and old_desktop_id in pinned_desktop_ids()
        pending = dialog.pending_icons()
        try:
            # เปลี่ยนชื่อ = ย้ายโฟลเดอร์ ไม่ใช่สร้างใหม่แล้วลบทิ้ง
            # (ถ้าลบ `555/` ทิ้ง ไอค่อนที่แคชไว้ของ shortcut จะหายตามไปด้วย)
            if (
                renamed
                and self.store.group_dir(old_dir).is_dir()
                and not self.store.group_dir(new_dir).is_dir()
            ):
                try:
                    self.store.group_dir(old_dir).rename(
                        self.store.group_dir(new_dir)
                    )
                except OSError:
                    pass
            self.store.save_group(group)
            if dialog.icon_source():
                group.icon = self.store.import_group_icon(new_dir, dialog.icon_source())
                self.store.save_group(group)
            if renamed and self.store.group_dir(old_dir).is_dir():
                self.store.delete_group(old_dir)
            self._cache_shortcut_icons(group, new_dir, pending)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        if group.name != original_name:
            show_information(
                self,
                tr("main.name_taken_title"),
                tr("main.name_taken_body", name=original_name, new_name=group.name),
            )
        try:
            if renamed:
                self._cleanup_launcher(old_dir, old_desktop_id)
                self._migrate_win_hotkey(old_dir, new_dir)
                if was_pinned:
                    self._install_and_pin(group, new_dir)
                    self._repoint_pinned(old_dir, new_dir)
            else:
                self._refresh_pinned_icon(group, new_dir)
            # เปลี่ยนไอคอน = force → ลบ .lnk เก่า+เขียนทับสำเนา taskbar/Desktop
            # ไม่งั้น Windows แคชไอคอนเก่าไว้ ( Explorer/Taskbar ไม่เปลี่ยนตาม )
            self._ensure_launcher(group, new_dir, force=bool(dialog.icon_source()))
        except Exception:
            # งานเสริม (ล้าง launcher / ทำ .lnk) พังไม่ได้ปล่อยให้กลุ่มที่เพิ่ง
            # บันทึกแล้วหายจากรายการ — กันไว้ก่อน แล้วค่อยรีเฟรช
            pass
        finally:
            # เสมอต้องรีเฟรช ไม่งั้นผู้ใช้บันทึกกลุ่มแล้วไม่เห็นในรายการ
            self.refresh()

    def _migrate_win_hotkey(self, old_dir: str | None, new_dir: str) -> None:
        """หลังเปลี่ยนชื่อกลุ่ม — ย้าย hotkey ฝั่ง Windows ตามไปชี้ชื่อใหม่."""
        if sys.platform != "win32" or not old_dir:
            return
        from .win32_hotkey import registry

        old_slot = hotkey_slot(old_dir)
        new_slot = hotkey_slot(new_dir)
        settings = Settings(self.store.config_dir)
        binding = settings.get_hotkeys().get(old_slot)
        if not binding:
            return
        try:
            hwnd = int(self.winId())
        except (TypeError, ValueError):
            hwnd = 0
        registry.unregister_slot(old_slot, hwnd)
        settings.remove_hotkey(old_slot)
        try:
            registry.register_slot(new_slot, new_dir, binding, hwnd)
        except OSError:
            pass
        settings.set_hotkey(new_slot, binding)

    def _repoint_pinned(self, old_dir: str, new_dir: str) -> None:
        """หลังเปลี่ยนชื่อ — ให้ปุ่มบน taskbar ที่ผู้ใช้ลากวางไว้ชี้กลุ่มใหม่

        ไฟล์ใน `User Pinned` เป็นสำเนาที่ Windows ก๊อปไว้ตอนลากวาง มันยังชี้
        `--open "<ชื่อเก่า>"` → กดแล้วเปิดกลุ่มที่ไม่มีแล้ว (flyout ว่างเปล่า)
        เราสร้าง pin ใหม่ไม่ได้ แต่เขียนทับไฟล์ของเดิมได้
        """
        if get_backend().supports_direct_pin:
            return
        from taskbarnoob.core.platform.win32 import repoint_pinned, shortcuts_dir

        new_lnk = shortcuts_dir() / desktop_file_name(new_dir)
        if not new_lnk.is_file():
            return
        try:
            repoint_pinned(old_dir, new_lnk)
        except OSError:
            pass

    def _install_launcher(self, group, dir_name: str):
        """สร้าง launcher พร้อมไอคอนสำรองจากระบบ (Windows เท่านั้น)."""
        from .icons import default_group_icon_file

        default_icon = (
            default_group_icon_file(self.store) if sys.platform == "win32" else None
        )
        return install_launcher(
            group, self.store, dir_name, default_icon=default_icon
        )

    def _ensure_launcher(self, group, dir_name: str, force: bool = False) -> None:
        """สร้าง/รีเฟรช `.lnk` อัตโนมัติหลังบันทึกกลุ่ม (Windows เท่านั้น).

        ฝั่ง Linux ปักลง panel ได้จริงจึงยังคงพฤติกรรมเดิม (ค่อยกดปุ่มปักเอง)
        ส่วน Windows ปุ่มปักคือ "เปิดโฟลเดอร์ให้ลาก" — ถ้ายังไม่มีไฟล์ให้ลาก
        ผู้ใช้จะงง จึงต้องมีไฟล์อยู่เสมอหลังสร้างกลุ่ม

        `force=True` (ตอนเปลี่ยนไอคอน) = ลบ `.lnk` เก่าแล้วสร้างใหม่ + เขียนทับ
        สำเนาบน taskbar/Desktop — ถ้าใช้ของเดิม Windows แคชไอคอนไว้ ไม่อัพเดท.
        """
        if get_backend().supports_direct_pin:
            return
        from taskbarnoob.core.platform.win32 import shortcuts_dir

        path = shortcuts_dir() / desktop_file_name(dir_name)
        pinned = desktop_file_name(dir_name) in pinned_desktop_ids()
        if path.is_file() and not pinned and not force:
            return  # มีอยู่แล้ว ไม่ปัก ไม่ได้เปลี่ยนไอคอน — ไม่ต้องเขียนใหม่
        try:
            if force and path.is_file():
                path.unlink()  # ลบของเก่าก่อน — ไม่งั้น Windows แคชไอคอนไว้
            self._install_launcher(group, dir_name)
        except OSError:
            pass  # เงียบไว้ ผู้ใช้ยังกดปุ่มเปิดโฟลเดอร์เพื่อสร้างเองได้
        if force and path.is_file():
            # อัปเดตสำเนาบน taskbar/Desktop ถ้ามี (Windows ก๊อปไฟล์ตอนลากวาง →
            # สำเนาเก่าชี้ไอคอนเก่า · ต้องเขียนทับถึงจะเห็นไอคอนใหม่)
            try:
                from taskbarnoob.core.platform.win32 import (
                    repoint_desktop_copies,
                    repoint_pinned,
                )

                repoint_pinned(dir_name, path)
                repoint_desktop_copies(dir_name, path)
            except OSError:
                pass
            # แจ้ง Windows ให้รีเฟรช icon cache (ไม่งั้นยังโชว์ไอคอนเก่าตาม path)
            try:
                from taskbarnoob.core.platform.win32 import notify_icon_changed

                icon_path = group.icon and self.store.resolve_relative(dir_name, group.icon)
                if icon_path is not None:
                    notify_icon_changed(icon_path)
                notify_icon_changed(path)
            except Exception:
                pass

    def _cleanup_launcher(self, dir_name: str, desktop_id: str) -> None:
        """ลบ launcher/ไอคอนของกลุ่ม + ถอนหมุดออกจาก panel ถ้าปักอยู่."""
        removed = False
        try:
            if desktop_id in pinned_desktop_ids():
                removed = unpin_from_panel(desktop_id)
        except PinError:
            pass
        try:
            remove_launcher(dir_name)
        except OSError:
            pass
        if removed:
            reload_grouped_window_applet()

    def _install_and_pin(self, group, dir_name: str) -> None:
        """ติดตั้ง launcher ใหม่แล้วปักลง panel (ไม่ขึ้นข้อความ — ใช้ตอน rename)."""
        try:
            self._install_launcher(group, dir_name)
        except OSError:
            return
        try:
            pin_to_panel(desktop_file_name(dir_name))
        except PinError:
            return
        reload_grouped_window_applet()

    def _refresh_pinned_icon(self, group, dir_name: str) -> None:
        """ถ้ากลุ่มนี้ถูกปักบน panel อยู่ → รีเจน launcher + โหลด applet ใหม่
        ให้ไอค่อน (ที่พึ่งเปลี่ยนไป) สดขึ้นมาบน Taskbar ทันที (ไม่งั้นค้างรูปเก่า)."""
        if desktop_file_name(dir_name) not in pinned_desktop_ids():
            return
        try:
            self._install_launcher(group, dir_name)
        except OSError:
            return
        reload_grouped_window_applet()

    def _cache_shortcut_icons(
        self, group, dir_name: str, pending: dict[int, str]
    ) -> None:
        icons_dir = self.store.icons_dir(dir_name)
        changed = False
        for item in group.items:
            source = pending.get(id(item))
            try:
                relative = core_icons.cache_shortcut_icon(
                    icons_dir, item.target, item.name or item.target, source=source
                )
            except core_icons.IconError:
                continue
            if not relative:
                # ไฟล์ที่ core แคชให้ไม่ได้ (เช่น .exe/.lnk บน Windows) → ใช้ไอคอน OS
                relative = cache_provider_icon(
                    self.store, dir_name, item.target, item.name or item.target
                )
            if relative and relative != item.icon:
                item.icon = relative
                changed = True
        if changed:
            self.store.save_group(group)

    def on_delete(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        answer = show_question(
            self,
            tr("main.confirm_delete_title"),
            tr("main.confirm_delete_body", dir_name=dir_name),
            QMessageBox.Yes | QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            self.store.delete_group(dir_name)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        self._cleanup_launcher(dir_name, desktop_file_name(dir_name))
        if is_cinnamon():
            try:
                unregister_cinnamon_hotkey(hotkey_slot(dir_name))
            except HotkeyError:
                pass
        elif sys.platform == "win32":
            from taskbarnoob.core.settings import Settings

            from .win32_hotkey import registry

            try:
                hwnd = int(self.winId())
            except (TypeError, ValueError):
                hwnd = 0
            registry.unregister_slot(hotkey_slot(dir_name), hwnd)
            Settings(self.store.config_dir).remove_hotkey(hotkey_slot(dir_name))
        self.refresh()

    def on_open(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        show_labels = Settings().get_flyout_labels()
        self._flyout = FlyoutWindow(
            group, self.store, dir_name, default_show_labels=show_labels
        )
        self._flyout.show_at_cursor()

    def _on_context_menu(self, pos) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        menu = self._group_context_menu(dir_name)
        menu.exec(pos)
        menu.deleteLater()

    def _group_context_menu(self, dir_name: str) -> QMenu:
        pinned = desktop_file_name(dir_name) in pinned_desktop_ids()
        menu = _style_menu(QMenu(self))
        menu.addAction(tr("ctx.open"), self.on_open)
        menu.addAction(tr("ctx.edit"), self.on_edit)
        menu.addSeparator()
        if sys.platform == "win32":
            # Windows ปักเองไม่ได้ (Win11 ปิด API) → เมนูนี้พาผู้ใช้ไปลากวางแทน
            menu.addAction(tr("ctx.open_launcher_dir"), self.on_pin)
        else:
            menu.addAction(tr("ctx.unpin") if pinned else tr("ctx.pin"), self.on_pin)
        menu.addAction(tr("ctx.set_hotkey"), self.on_set_hotkey)
        menu.addSeparator()
        menu.addAction(tr("ctx.duplicate"), self.on_duplicate)
        menu.addAction(tr("ctx.delete"), self.on_delete)
        return menu

    def on_duplicate(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
            new_name = tr("ctx.copy_suffix", name=group.name)
            new_dir = self.store.duplicate_group(dir_name, new_name)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        # สำเนาต้องมี .lnk ของตัวเองด้วย (Windows) — ชื่อไฟล์ผูกกับชื่อกลุ่ม
        try:
            copy_group = self.store.load_group(new_dir)
        except StorageError:
            copy_group = None
        if copy_group is not None:
            self._ensure_launcher(copy_group, new_dir)
        self.refresh()

    def _open_setup_menu(self) -> None:
        menu = _style_menu(QMenu(self))
        menu.addAction(tr("menu.settings"), self.open_settings)
        menu.addAction(tr("menu.about"), self.open_about)
        menu.exec(self.setup_button.mapToGlobal(self.setup_button.rect().bottomLeft()))
        menu.deleteLater()

    def open_settings(self) -> None:
        SettingsDialog(self).exec()

    def open_about(self) -> None:
        AboutDialog(self).exec()

    def on_pin(self, dir_name: str | None = None) -> None:
        """ปุ่มสถานะของกลุ่ม — ความหมายต่างกันตาม OS.

        - Linux: toggle ปัก/ถอนหมุดจริง
        - Windows: เปิดโฟลเดอร์ที่มี `.lnk` ให้ผู้ใช้ลากไปวางบน taskbar
          (Win11 ปิด API ปักอัตโนมัติ — ทำแทนไม่ได้)
        """
        dir_name = dir_name or self._current_dir_name()
        if dir_name is None:
            return
        desktop_id = desktop_file_name(dir_name)
        try:
            group = self.store.load_group(dir_name)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        if not get_backend().supports_direct_pin:
            self._reveal_launcher_dir(group, dir_name)
            return
        if desktop_id in pinned_desktop_ids():
            self._unpin(dir_name, desktop_id)
        else:
            self._pin(group, dir_name, desktop_id)

    def _reveal_launcher_dir(self, group, dir_name: str) -> None:
        """(re)สร้าง `.lnk` ให้ตรงกลุ่มปัจจุบัน แล้วเปิด Explorer เลือกไฟล์ให้ลากวาง.

        เขียนใหม่ทุกครั้ง (ลบไฟล์เก่าก่อนสร้าง) — ถ้าใช้ของเดิม ไอคอนที่เพิ่งเปลี่ยน
        จะไม่อัพเดทบน .lnk (Explorer cache ไฟล์เดิม) จนผู้ใช้ต้องมานั่งลบเอง
        """
        from taskbarnoob.core.platform import win32 as _win32

        desktop_id = desktop_file_name(dir_name)
        existing = _win32.shortcuts_dir() / desktop_id
        try:
            if existing.is_file():
                existing.unlink()
            path = self._install_launcher(group, dir_name)
            _win32.reveal_in_explorer(path)
        except OSError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        self.refresh()
        # compose เป็น HTML ทั้งก้อน (launcher_installed ใช้ \n → แปลงเป็น <br> ให้ตรง RichText)
        html = (
            tr("main.launcher_installed", path=path).replace("\n", "<br>")
            + "<br><br>"
            + tr("main.win_not_pinned_tip", file=desktop_id)
        )
        show_information(self, tr("main.pin_title"), html, rich=True)

    def _pin(self, group, dir_name: str, desktop_id: str) -> None:
        """ปักหมุดจริง — ฝั่ง Linux/macOS เท่านั้น (Windows ไปที่ `_reveal_launcher_dir`)."""
        try:
            path = self._install_launcher(group, dir_name)
        except OSError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        lines = [tr("main.launcher_installed", path=path), ""]
        try:
            method = pin_to_panel(desktop_id)
        except PinError as exc:
            lines.append(tr("main.pin_fallback", exc=exc))
        else:
            if method == "grouped-window-list":
                QTimer.singleShot(2500, reload_grouped_window_applet)
            lines.append(tr("main.pin_ok"))
        self.refresh()
        show_information(self, tr("main.pin_title"), "\n".join(lines))

    def _unpin(self, dir_name: str, desktop_id: str) -> None:
        try:
            removed = unpin_from_panel(desktop_id)
        except PinError as exc:
            show_warning(self, tr("main.unpin_failed"), str(exc))
            return
        self.refresh()
        message = (
            tr("main.unpin_ok")
            if removed
            else tr("main.unpin_not_found")
        )
        show_information(self, tr("main.unpin_title"), message)

    def on_install_launcher(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
            path = self._install_launcher(group, dir_name)
        except (StorageError, OSError) as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        show_information(
            self,
            tr("main.launcher_installed_title"),
            tr("main.launcher_installed_body", path=path),
        )

    def on_set_hotkey(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
        except StorageError as exc:
            show_warning(self, tr("err.generic"), str(exc))
            return
        HotkeyDialog(group, self.store, dir_name, self).exec()
        self.refresh()


__all__ = [
    "GroupListWidget",
    "ICON_SIZE",
    "MainWindow",
    "PINNED_ROLE",
    "_RowDropHighlightDelegate",
    "_pin_tooltip",
    "_register_saved_win_hotkeys",
    "_run_flyout",
    "_style_menu",
    "run",
]
