"""หน้าต่างหลัก: จัดการรายการกลุ่ม (Phase 2 MVP)."""

from __future__ import annotations

import sys

from PySide6.QtCore import QPointF, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QListView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core import icons as core_icons
from taskbargroups.core.desktop import (
    applications_dir,
    desktop_file_name,
    install_launcher,
    launcher_id,
    remove_launcher,
)
from taskbargroups.core.hotkeys import (
    HotkeyError,
    cinnamon_to_display,
    group_hotkeys,
    hotkey_slot,
    is_cinnamon,
    unregister_cinnamon_hotkey,
)

from taskbargroups.core.i18n import setup, tr
from taskbargroups.core.panel import (
    PinError,
    pin_to_panel,
    pinned_desktop_ids,
    reload_grouped_window_applet,
    unpin_from_panel,
)
from taskbargroups.core.paths import app_icon_path
from taskbargroups.core.settings import Settings
from taskbargroups.core.storage import ConfigStore, StorageError, safe_dir_name

from .about_dialog import AboutDialog
from .flyout import FlyoutController, FlyoutWindow
from .group_editor import GroupEditor
from .hotkey_dialog import HotkeyDialog
from .icons import group_icon
from .settings_dialog import SettingsDialog
from .theme import apply_theme, resolve_theme

ICON_SIZE = QSize(32, 32)

PINNED_ROLE = Qt.UserRole + 1


def _style_menu(menu: QMenu) -> QMenu:
    """เมนูร่วม: ให้ padding แนวตั้งพอดี ไม่ติดขอบ (เฟือง + คลิกขวากลุ่ม)."""
    menu.setStyleSheet(
        "QMenu { padding: 6px 4px; }"
        "QMenu::item { padding: 8px 22px; }"
    )
    return menu


class GroupListWidget(QListWidget):
    """ลิสต์กลุ่ม: ลากสลับลำดับได้ + ปุ่มสถานะ (รูปตา เปิด/ปิด) ท้ายสุดของแต่ละแถว."""

    pinClicked = Signal(str)
    orderChanged = Signal()
    contextMenuRequested = Signal(object)

    PIN_WIDTH = 28
    PIN_RIGHT_MARGIN = 8

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMovement(QListView.Snap)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setMouseTracking(True)
        self._hover: tuple[QListWidgetItem | None, bool] = (None, False)
        self._press_pin: QListWidgetItem | None = None

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        self.orderChanged.emit()

    def startDrag(self, supported_actions) -> None:
        QApplication.setOverrideCursor(Qt.SizeAllCursor)
        try:
            super().startDrag(supported_actions)
        finally:
            QApplication.restoreOverrideCursor()

    def dragEnterEvent(self, event) -> None:
        if event.source() is self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.source() is self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
        super().dragMoveEvent(event)

    def pin_rect(self, item: QListWidgetItem) -> QRect:
        rect = self.visualItemRect(item)
        left = rect.right() - self.PIN_WIDTH - self.PIN_RIGHT_MARGIN
        return QRect(left, rect.top(), self.PIN_WIDTH, rect.height())

    def _pin_under(self, pos) -> QListWidgetItem | None:
        item = self.itemAt(pos)
        if item is not None and self.pin_rect(item).contains(pos):
            return item
        return None

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            item = self._pin_under(pos)
            if item is not None:
                self._press_pin = item
                event.accept()
                return
        self._press_pin = None
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if self._press_pin is not None and event.button() == Qt.LeftButton:
            pos = event.position().toPoint()
            item = self._pin_under(pos)
            pressed, self._press_pin = self._press_pin, None
            if item is pressed:
                self.pinClicked.emit(item.data(Qt.UserRole))
                return
        self._press_pin = None
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event) -> None:
        item = self._pin_under(event.position().toPoint())
        state = (item, item is not None)
        if state != self._hover:
            self._hover = state
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hover != (None, False):
            self._hover = (None, False)
            self.viewport().update()
        super().leaveEvent(event)

    def contextMenuEvent(self, event) -> None:
        item = self.itemAt(event.pos())
        if item is None:
            return
        self.setCurrentItem(item)
        self.contextMenuRequested.emit(event.globalPos())
        event.accept()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.Antialiasing, True)
        hovered_item = self._hover[0]
        for row in range(self.count()):
            item = self.item(row)
            pinned = bool(item.data(PINNED_ROLE))
            self._draw_pin(painter, self.pin_rect(item), item is hovered_item, pinned)
        painter.end()

    def _draw_pin(self, painter: QPainter, rect: QRect, hovered: bool, pinned: bool) -> None:
        if hovered:
            painter.save()
            painter.setPen(Qt.NoPen)
            color = self.palette().color(QPalette.ColorRole.Highlight)
            color.setAlpha(45)  # โปร่งแสงขึ้น ดูนุ่มกว่า
            painter.setBrush(color)
            painter.drawRoundedRect(rect.adjusted(1, 5, -1, -5), 6, 6)
            painter.restore()
        self._paint_pin_shape(painter, rect, pinned)

    def _status_color(self, pinned: bool) -> QColor:
        """สีไอค่อนสถานะ (ตา) แบบธีม-aware: พื้นสว่าง→เทาเข้ม · พื้นมืด→ขาว
        (ไม่ใช้ Highlight เพื่อไม่ให้กลืนกับแถวที่ถูกเลือก)."""
        base = self.palette().color(QPalette.ColorRole.Base)
        color = QColor(255, 255, 255) if base.lightness() < 128 else QColor(82, 82, 92)
        if not pinned:
            color.setAlpha(150)
        return color

    def _paint_pin_shape(self, painter: QPainter, rect: QRect, pinned: bool) -> None:
        """วาดไอค่อนสถานะ: ตาเปิด (ปัก/โชว์) · ตามิด (ซ่อน)."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        color = self._status_color(pinned)
        size = min(rect.width(), rect.height())
        center = rect.center()
        cx, cy = center.x(), center.y()
        eye_w = size * 0.68
        eye_h = eye_w * 0.6
        left = cx - eye_w / 2
        right = cx + eye_w / 2
        pen = QPen(color)
        pen.setWidthF(max(1.4, size * 0.08))
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        path = QPainterPath()
        if pinned:
            path.moveTo(left, cy)
            path.quadTo(cx, cy - eye_h, right, cy)
            path.quadTo(cx, cy + eye_h, left, cy)
            painter.drawPath(path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            pupil = size * 0.15
            painter.drawEllipse(QPointF(cx, cy), pupil, pupil)
        else:
            path.moveTo(left, cy - eye_h * 0.35)
            path.quadTo(cx, cy + eye_h * 0.95, right, cy - eye_h * 0.35)
            painter.drawPath(path)
        painter.restore()


class MainWindow(QMainWindow):
    def __init__(self, store: ConfigStore | None = None) -> None:
        super().__init__()
        self.store = store or ConfigStore()
        self._flyout: FlyoutWindow | None = None

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
            button.clicked.connect(slot)
            row.addWidget(button)
            self._nav_buttons.append((key, button))
        row.addStretch(1)
        self.setup_button = QPushButton("⚙")
        self.setup_button.setToolTip(tr("main.setup_tooltip"))
        gear_font = self.setup_button.font()
        gear_font.setPixelSize(28)
        self.setup_button.setFont(gear_font)
        self.setup_button.setFixedWidth(52)
        self.setup_button.clicked.connect(self._open_setup_menu)
        row.addWidget(self.setup_button)
        layout.addLayout(row)

        self.refresh()
        self._sync_pinned_launchers()

    def _sync_pinned_launchers(self) -> None:
        """ซ่อม launcher ของกลุ่มที่ปักไว้ที่ยังชี้ไอค่อนเป็น path สัมบูรณ์.

        ไอคอนเดิมชี้ไฟล์บนไดรฟ์ (เช่น /mnt/Backup) ที่ mount หลัง panel เริ่มทำงาน
        → ตอน boot ไอคอนหาย. ติดตั้งไอคอนเข้า icon theme (บนดิสก์ราก) แล้วชี้
        ด้วยชื่อ ให้ panel หาเจอเสมอ. ทำครั้งเดียวต่อ launcher.
        """
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
                install_launcher(group, self.store, dir_name)
                changed = True
            except (StorageError, OSError):
                continue
        if changed:
            reload_grouped_window_applet()

    def retranslate(self) -> None:
        """อัปเดตข้อความ UI ตามภาษาที่ active อยู่ (เรียกหลังสลับภาษาแบบทันที)."""
        self.setWindowTitle(tr("app.title"))
        for key, button in self._nav_buttons:
            button.setText(tr(key))
        self.setup_button.setToolTip(tr("main.setup_tooltip"))
        self.refresh()

    def refresh(self) -> None:
        self.list.clear()
        pinned_ids = pinned_desktop_ids()
        dir_names = self.store.list_groups()
        try:
            bindings = group_hotkeys([hotkey_slot(name) for name in dir_names])
        except Exception:
            bindings = {}
        for dir_name in dir_names:
            try:
                group = self.store.load_group(dir_name)
            except StorageError:
                continue
            label = f"{group.name}  ({len(group.items)})"
            binding = bindings.get(hotkey_slot(dir_name))
            if binding:
                label += tr("main.hotkey_inline", keys=cinnamon_to_display(binding))
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, dir_name)
            is_pinned = desktop_file_name(dir_name) in pinned_ids
            item.setData(PINNED_ROLE, is_pinned)
            item.setToolTip(
                f"{group.name} — "
                + (tr("main.pinned_tip") if is_pinned else tr("main.not_pinned_tip"))
            )
            item.setIcon(group_icon(group, self.store, dir_name))
            self.list.addItem(item)

    def _on_rows_moved(self, *_args) -> None:
        order = [self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())]
        try:
            self.store.save_order(order)
        except StorageError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))

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
            QMessageBox.warning(self, tr("err.generic"), str(exc))
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
        renamed = bool(old_dir and old_dir != new_dir)
        old_desktop_id = desktop_file_name(old_dir) if renamed else ""
        was_pinned = renamed and old_desktop_id in pinned_desktop_ids()
        pending = dialog.pending_icons()
        try:
            self.store.save_group(group)
            if dialog.icon_source():
                group.icon = self.store.import_group_icon(new_dir, dialog.icon_source())
                self.store.save_group(group)
            if renamed and self.store.group_dir(old_dir).is_dir():
                self.store.delete_group(old_dir)
            self._cache_shortcut_icons(group, new_dir, pending)
        except StorageError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        if group.name != original_name:
            QMessageBox.information(
                self,
                tr("main.name_taken_title"),
                tr("main.name_taken_body", name=original_name, new_name=group.name),
            )
        if renamed:
            self._cleanup_launcher(old_dir, old_desktop_id)
            if was_pinned:
                self._install_and_pin(group, new_dir)
        else:
            self._refresh_pinned_icon(group, new_dir)
        self.refresh()

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
            install_launcher(group, self.store, dir_name)
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
            install_launcher(group, self.store, dir_name)
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
            if relative and relative != item.icon:
                item.icon = relative
                changed = True
        if changed:
            self.store.save_group(group)

    def on_delete(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        answer = QMessageBox.question(
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
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        self._cleanup_launcher(dir_name, desktop_file_name(dir_name))
        if is_cinnamon():
            try:
                unregister_cinnamon_hotkey(hotkey_slot(dir_name))
            except HotkeyError:
                pass
        self.refresh()

    def on_open(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
        except StorageError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        self._flyout = FlyoutWindow(group, self.store, dir_name)
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
            self.store.duplicate_group(dir_name, new_name)
        except StorageError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
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
        """คลิกไอคอนเข็มหมุด: ปักหมุดถ้ายังไม่ปัก / ถอนหมุดถ้าปักอยู่แล้ว."""
        dir_name = dir_name or self._current_dir_name()
        if dir_name is None:
            return
        desktop_id = desktop_file_name(dir_name)
        try:
            group = self.store.load_group(dir_name)
        except StorageError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        if desktop_id in pinned_desktop_ids():
            self._unpin(dir_name, desktop_id)
        else:
            self._pin(group, dir_name, desktop_id)

    def _pin(self, group, dir_name: str, desktop_id: str) -> None:
        try:
            path = install_launcher(group, self.store, dir_name)
        except OSError as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
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
        QMessageBox.information(self, tr("main.pin_title"), "\n".join(lines))

    def _unpin(self, dir_name: str, desktop_id: str) -> None:
        try:
            removed = unpin_from_panel(desktop_id)
        except PinError as exc:
            QMessageBox.warning(self, tr("main.unpin_failed"), str(exc))
            return
        self.refresh()
        message = (
            tr("main.unpin_ok")
            if removed
            else tr("main.unpin_not_found")
        )
        QMessageBox.information(self, tr("main.unpin_title"), message)

    def on_install_launcher(self) -> None:
        dir_name = self._current_dir_name()
        if dir_name is None:
            return
        try:
            group = self.store.load_group(dir_name)
            path = install_launcher(group, self.store, dir_name)
        except (StorageError, OSError) as exc:
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        QMessageBox.information(
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
            QMessageBox.warning(self, tr("err.generic"), str(exc))
            return
        HotkeyDialog(group, self.store, dir_name, self).exec()
        self.refresh()


def run(argv: list[str] | None = None, open_group: str | None = None) -> int:
    app = QApplication.instance() or QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("TaskbarNoob")
    app.setApplicationDisplayName("TaskbarNoob")
    app.setDesktopFileName("taskbargroups")
    icon_path = app_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))
    settings = Settings()
    setup(settings.get_language())
    apply_theme(app, resolve_theme(settings.get_theme(), app))
    if open_group:
        return _run_flyout(app, open_group)
    window = MainWindow()
    window.show()
    return app.exec()


def _run_flyout(app: QApplication, dir_name: str) -> int:
    store = ConfigStore()
    controller = FlyoutController(app, store)
    if controller.try_delegate(dir_name):
        return 0
    controller.start_primary(dir_name)
    code = app.exec()
    controller.shutdown()
    return code
