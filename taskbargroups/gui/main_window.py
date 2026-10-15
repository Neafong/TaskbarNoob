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
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core import icons as core_icons
from taskbargroups.core.hotkeys import (
    HotkeyError,
    cinnamon_to_display,
    group_hotkeys,
    hotkey_slot,
    is_cinnamon,
    unregister_cinnamon_hotkey,
)
from taskbargroups.core.launchers import (
    desktop_file_name,
    install_launcher,
    launcher_id,
    remove_launcher,
)

from taskbargroups.core.i18n import setup, tr
from taskbargroups.core.panel import (
    PinError,
    reload_grouped_window_applet,
)
from taskbargroups.core.taskbar import (
    pin_to_panel,
    pinned_desktop_ids,
    unpin_from_panel,
)
from taskbargroups.core.paths import app_icon_path
from taskbargroups.core.settings import Settings
from taskbargroups.core.storage import ConfigStore, StorageError, safe_dir_name

from .about_dialog import AboutDialog
from .button_icons import themed_icon, tinted_icon_pixmap
from .dialogs import show_information, show_question, show_warning
from .flyout import FlyoutController, FlyoutWindow
from .group_editor import GroupEditor
from .hotkey_dialog import HotkeyDialog
from .icons import cache_provider_icon, group_icon
from .settings_dialog import SettingsDialog
from .theme import app_text_color, apply_theme, resolve_theme

ICON_SIZE = QSize(32, 32)

PINNED_ROLE = Qt.UserRole + 1


def _style_menu(menu: QMenu) -> QMenu:
    """เมนูร่วม: ให้ padding แนวตั้งพอดี ไม่ติดขอบ (เฟือง + คลิกขวากลุ่ม)."""
    menu.setStyleSheet(
        "QMenu { padding: 6px 4px; }"
        "QMenu::item { padding: 8px 22px; }"
    )
    return menu


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


class _RowDropHighlightDelegate(QStyledItemDelegate):
    """วาดไฮไลท์คู่สลับตอนลาก — วาดรองพื้นก่อนเนื้อหา (stroke จะได้ไม่ทับไอคอน)."""

    def __init__(self, rows: "GroupListWidget") -> None:
        super().__init__(rows)
        self._rows = rows

    def paint(self, painter, option, index) -> None:
        if index.row() == self._rows.drop_highlight_row:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            color = option.palette.highlight().color()
            fill = QColor(color)
            fill.setAlpha(50)
            pen = QPen(color)
            pen.setWidth(2)
            painter.setBrush(fill)
            painter.setPen(pen)
            item = self._rows.item(index.row())
            if item is not None:
                painter.drawRoundedRect(self._rows._drop_cell(item), 6, 6)
            painter.restore()
        super().paint(painter, option, index)


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
        # วาดไฮไลท์คู่สลับเอง (แบบเดียวกับกริด) — ไม่ใช้เส้นแทรกของ Qt
        self.setDropIndicatorShown(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMovement(QListView.Snap)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setMouseTracking(True)
        # ระยะห่างระหว่างแถว 2px — stroke คู่สลับจะได้มีที่หายใจ ไม่เบียดแถวข้าง ๆ
        self.setSpacing(2)
        # padding รอบเนื้อหาแถว — ไอคอนมีที่หายใจ เหลือร่อง ~1px จาก stroke
        self.setStyleSheet("QListWidget::item { padding: 3px 2px 3px 0px; }")
        self.setItemDelegate(_RowDropHighlightDelegate(self))
        self._hover: tuple[QListWidgetItem | None, bool] = (None, False)
        self._press_pin: QListWidgetItem | None = None
        self._row_hover: int = -1
        self._drag_source_row: int | None = None
        self._drop_row: int | None = None

    def clear(self) -> None:
        self._hover = (None, False)
        self._press_pin = None
        self._row_hover = -1
        self._drop_row = None
        super().clear()

    @property
    def drop_highlight_row(self) -> int:
        """แถวคู่สลับที่จะโชว์ไฮไลท์ (ไอเทมที่ลากจะลงแถวนี้พอดี)."""
        if self._drop_row is None or self.count() == 0:
            return -1
        return min(self._drop_row, self.count() - 1)

    def dropEvent(self, event) -> None:
        partner = self._partner_row(event.position().toPoint())
        self._set_drop_row(None)
        if event.source() is not None and event.source() is not self:
            event.ignore()
            return
        source = self._drag_source_row
        if source is None:
            source = self.currentRow()
        if source is None or source < 0:
            event.ignore()
            return
        # ปล่อยที่ว่าง = ย้ายไปท้ายสุด · ปล่อยบนแถว = สลับที่กัน (แบบเดียวกับกริด)
        self._swap_rows(source, partner if partner is not None else self.count())
        self.clearSelection()
        event.acceptProposedAction()
        self.orderChanged.emit()

    def _set_drop_row(self, row: int | None) -> None:
        if row != self._drop_row:
            self._drop_row = row
            self.viewport().update()

    def _drop_cell(self, item: QListWidgetItem) -> QRect:
        """กรอบ stroke คู่สลับ: เกาะขอบแถว (วาดใต้เนื้อหาผ่าน delegate)."""
        return self.visualItemRect(item).adjusted(1, 1, -1, -1)

    def _partner_row(self, pos) -> int | None:
        """แถวใต้เมาส์ (คู่สลับ) — None ถ้าปล่อยที่ว่างท้ายสุด."""
        item = self.itemAt(pos)
        return self.row(item) if item is not None else None

    def _swap_rows(self, source: int, target: int) -> None:
        """สลับแถว source กับ target (target == count คือย้ายไปท้ายสุด)."""
        count = self.count()
        if count == 0 or source < 0 or source >= count:
            return
        if target >= count:
            if source == count - 1:
                return
            item = self.takeItem(source)
            if item is None:
                return
            self.insertItem(self.count(), item)
            self.setCurrentItem(item)
            return
        if target == source or target < 0:
            return
        moving = self.takeItem(source)
        if moving is None:
            return
        # ถอดทั้งคู่ออกก่อน แล้วเสียบกลับคนละแถว — เสียบแถวเล็กก่อน (ทิศเดียวกับกริด)
        if source < target:
            other = self.takeItem(target - 1)
            self.insertItem(source, other)
            self.insertItem(target, moving)
        else:
            other = self.takeItem(target)
            self.insertItem(target, moving)
            self.insertItem(source, other)
        self.setCurrentItem(moving)

    def startDrag(self, supported_actions) -> None:
        self._drag_source_row = self.currentRow()
        self._set_drop_row(None)
        # รีเซ็ต hover ค้าง (วาดอย่างเดียว ไม่แตะ selection — Qt สร้าง drag จาก
        # selection ถ้าเคลียร์ก่อนลากจะไม่เริ่ม)
        self._hover = (None, False)
        self._row_hover = -1
        QApplication.setOverrideCursor(Qt.SizeAllCursor)
        try:
            super().startDrag(supported_actions)
        finally:
            QApplication.restoreOverrideCursor()
            self._drag_source_row = None
            self._set_drop_row(None)

    def dragEnterEvent(self, event) -> None:
        if event.source() is self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
        super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if event.source() is self:
            partner = self._partner_row(event.position().toPoint())
            self._set_drop_row(partner if partner is not None else self.count())
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
        super().dragMoveEvent(event)

    def dragLeaveEvent(self, event) -> None:
        self._set_drop_row(None)
        super().dragLeaveEvent(event)

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
        hovered = self.itemAt(event.position().toPoint())
        row = self.row(hovered) if hovered is not None else -1
        if row != self._row_hover:
            self._row_hover = row
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hover != (None, False):
            self._hover = (None, False)
            self.viewport().update()
        if self._row_hover != -1:
            self._row_hover = -1
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
        if 0 <= self._row_hover < self.count():
            row_item = self.item(self._row_hover)
            if row_item is not None:
                painter.save()
                painter.setPen(Qt.NoPen)
                color = self.palette().color(QPalette.ColorRole.Highlight)
                color.setAlpha(45)  # ไฮไลท์แถวโปร่งแสง (accent)
                painter.setBrush(color)
                rect = self.visualItemRect(row_item)
                painter.drawRoundedRect(rect.adjusted(1, 3, -1, -3), 6, 6)
                painter.restore()
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
        (ไม่ใช้ Highlight เพื่อไม่ให้กลืนกับแถวที่ถูกเลือก · อ่านตอน paint ซึ่ง palette สดเสมอ)."""
        base = self.palette().color(QPalette.ColorRole.Base)
        color = QColor(255, 255, 255) if base.lightness() < 128 else QColor(82, 82, 92)
        if not pinned:
            color.setAlpha(150)
        return color

    def _paint_pin_shape(self, painter: QPainter, rect: QRect, pinned: bool) -> None:
        """วาดไอค่อนสถานะ: ตาเปิด (ปัก/โชว์) · ตามิด (ซ่อน) — SVG ของเรา tint ตามธีม."""
        color = self._status_color(pinned)
        name = "eye-fill.svg" if pinned else "eye-slash-fill.svg"
        side = max(16, min(rect.width(), rect.height()) - 6)
        pixmap = tinted_icon_pixmap(name, side, color)
        if pixmap is not None and not pixmap.isNull():
            target = QRect(0, 0, side, side)
            target.moveCenter(rect.center())
            painter.drawPixmap(target, pixmap)
            return
        # fallback: วาดเส้นเอง (กรณีหา asset ไม่เจอ เช่น ใน bundle)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
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

    def _sync_pinned_launchers(self) -> None:
        """ซ่อม launcher ของกลุ่มที่ปักไว้ที่ยังชี้ไอค่อนเป็น path สัมบูรณ์.

        ไอคอนเดิมชี้ไฟล์บนไดรฟ์ (เช่น /mnt/Backup) ที่ mount หลัง panel เริ่มทำงาน
        → ตอน boot ไอคอนหาย. ติดตั้งไอคอนเข้า icon theme (บนดิสก์ราก) แล้วชี้
        ด้วยชื่อ ให้ panel หาเจอเสมอ. ทำครั้งเดียวต่อ launcher. (Linux เท่านั้น)
        """
        if sys.platform != "linux":
            return
        from taskbargroups.core.desktop import applications_dir

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

    def refresh_icons(self) -> None:
        """ทาสีไอคอนปุ่มใหม่ตามธีมปัจจุบัน (เรียกหลังสลับธีม — ใช้ app palette ตรงๆ)."""
        for key, button in self._nav_buttons:
            _apply_nav_icon(button, _NAV_BUTTON_ICONS[key])
        self.setup_button.setIcon(themed_icon(_SETUP_ICON, app_text_color()))
        self.list.viewport().update()

    def retranslate(self) -> None:
        """อัปเดตข้อความ UI ตามภาษาที่ active อยู่ (เรียกหลังสลับภาษาแบบทันที)."""
        self.setWindowTitle(tr("app.title"))
        for key, button in self._nav_buttons:
            button.setText(tr(key))
        self.refresh_icons()
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
        if sys.platform == "win32":
            # Windows ไม่มีที่เก็บ hotkey ของระบบ — อ่านที่แอปจำไว้ใน settings
            from taskbargroups.core.settings import Settings

            saved = Settings().get_hotkeys()
            for name in dir_names:
                slot = hotkey_slot(name)
                if slot in saved:
                    bindings[slot] = saved[slot]
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
            show_warning(self, tr("err.generic"), str(exc))
            return
        if group.name != original_name:
            show_information(
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
            from taskbargroups.core.settings import Settings

            from .win32_hotkey import registry

            try:
                hwnd = int(self.winId())
            except (TypeError, ValueError):
                hwnd = 0
            registry.unregister_slot(hotkey_slot(dir_name), hwnd)
            Settings().remove_hotkey(hotkey_slot(dir_name))
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
            show_warning(self, tr("err.generic"), str(exc))
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
            show_warning(self, tr("err.generic"), str(exc))
            return
        if desktop_id in pinned_desktop_ids():
            self._unpin(dir_name, desktop_id)
        else:
            self._pin(group, dir_name, desktop_id)

    def _pin(self, group, dir_name: str, desktop_id: str) -> None:
        try:
            path = install_launcher(group, self.store, dir_name)
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
            path = install_launcher(group, self.store, dir_name)
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
    if sys.platform == "win32":
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
            exe_args = [sys.executable, "-m", "taskbargroups"]
        hwnd = int(window.winId())
    except (TypeError, ValueError):
        return
    app.installNativeEventFilter(WinHotkeyFilter(registry, exe_args, window))
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


def _run_flyout(app: QApplication, dir_name: str) -> int:
    store = ConfigStore()
    controller = FlyoutController(app, store)
    if controller.try_delegate(dir_name):
        return 0
    controller.start_primary(dir_name)
    code = app.exec()
    controller.shutdown()
    return code
