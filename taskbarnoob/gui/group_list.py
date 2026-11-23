"""ลิสต์กลุ่มในหน้าต่างหลัก: ลากสลับลำดับได้ + ปุ่มสถานะ (ตา/โฟลเดอร์) ท้ายแถว."""

from __future__ import annotations

import sys

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QStyledItemDelegate,
    QWidget,
)

from .button_icons import tinted_icon_pixmap

PINNED_ROLE = Qt.UserRole + 1


def _style_menu(menu: QMenu) -> QMenu:
    """เมนูร่วม: ให้ padding แนวตั้งพอดี ไม่ติดขอบ (เฟือง + คลิกขวากลุ่ม)."""
    menu.setStyleSheet(
        "QMenu { padding: 6px 4px; }"
        "QMenu::item { padding: 8px 22px; }"
    )
    return menu


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
    """ลิสต์กลุ่ม: ลากสลับลำดับได้ + ปุ่มสถานะ (รูปตา เปิด/ปิด หรือโฟลเดอร์) ท้ายแถว."""

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
        self.setDropIndicatorShown(False)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setMovement(QListView.Snap)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setMouseTracking(True)
        self.setSpacing(2)
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
        self._swap_rows(source, partner if partner is not None else self.count())
        self.clearSelection()
        event.acceptProposedAction()
        self.orderChanged.emit()

    def _set_drop_row(self, row: int | None) -> None:
        if row != self._drop_row:
            self._drop_row = row
            self.viewport().update()

    def _drop_cell(self, item: QListWidgetItem) -> QRect:
        return self.visualItemRect(item).adjusted(1, 1, -1, -1)

    def _partner_row(self, pos) -> int | None:
        item = self.itemAt(pos)
        return self.row(item) if item is not None else None

    def _swap_rows(self, source: int, target: int) -> None:
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
                color.setAlpha(45)
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

    def _draw_pin(
        self, painter: QPainter, rect: QRect, hovered: bool, pinned: bool
    ) -> None:
        if hovered:
            painter.save()
            painter.setPen(Qt.NoPen)
            color = self.palette().color(QPalette.ColorRole.Highlight)
            color.setAlpha(45)
            painter.setBrush(color)
            painter.drawRoundedRect(rect.adjusted(1, 5, -1, -5), 6, 6)
            painter.restore()
        self._paint_pin_shape(painter, rect, pinned)

    def _status_color(self, pinned: bool) -> QColor:
        base = self.palette().color(QPalette.ColorRole.Base)
        dark = base.lightness() < 128
        if sys.platform == "win32":
            return QColor(240, 168, 58) if pinned else QColor(128, 128, 128, 120)
        color = QColor(255, 255, 255) if dark else QColor(82, 82, 92)
        if not pinned:
            color.setAlpha(150)
        return color

    def _paint_pin_shape(self, painter: QPainter, rect: QRect, pinned: bool) -> None:
        color = self._status_color(pinned)
        if sys.platform == "win32":
            name = "folder-fill.svg"
        else:
            name = "eye-fill.svg" if pinned else "eye-slash-fill.svg"
        side = max(16, min(rect.width(), rect.height()) - 6)
        pixmap = tinted_icon_pixmap(name, side, color)
        if pixmap is not None and not pixmap.isNull():
            target = QRect(0, 0, side, side)
            target.moveCenter(rect.center())
            painter.drawPixmap(target, pixmap)
            return
        if sys.platform == "win32":
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            size = min(rect.width(), rect.height()) * 0.8
            folder = QRectF(0, 0, size, size * 0.78)
            folder.moveCenter(rect.center())
            path = QPainterPath()
            path.addRoundedRect(folder, 3, 3)
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawPath(path)
            painter.restore()
            return
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
