"""Grid widget สำหรับจัดลำดับ shortcut และรับไฟล์ลากวางในหน้าต่างแก้ไขกลุ่ม."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QListView,
    QListWidget,
    QStyledItemDelegate,
    QWidget,
)


class _DropHighlightDelegate(QStyledItemDelegate):
    """วาดไฮไลท์ทับช่องกริดเป้าหมายตอนลาก (ให้ตรงกับตำแหน่งที่จะวางจริง)."""

    def __init__(self, grid: "ShortcutGrid") -> None:
        super().__init__(grid)
        self._grid = grid

    def paint(self, painter, option, index) -> None:
        if index.row() == self._grid.drop_highlight_row:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            color = option.palette.highlight().color()
            fill = QColor(color)
            fill.setAlpha(50)
            pen = QPen(color)
            pen.setWidth(2)
            painter.setBrush(fill)
            painter.setPen(pen)
            cell = QRect(QPoint(0, 0), self._grid.gridSize())
            cell.moveCenter(option.rect.center())
            cell = cell.intersected(self._grid.viewport().rect())
            painter.drawRoundedRect(cell.adjusted(2, 2, -2, -2), 10, 10)
            painter.restore()
        super().paint(painter, option, index)


class ShortcutGrid(QListWidget):
    """QListWidget โหมด grid: ลากสลับลำดับได้ + รับไฟล์ที่ลากมาจากข้างนอก."""

    urlsDropped = Signal(list)
    orderChanged = Signal()
    contextMenuRequested = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setViewMode(QListView.IconMode)
        self.setIconSize(QSize(64, 64))
        self.setGridSize(QSize(112, 108))
        self.setResizeMode(QListView.Adjust)
        self.setMovement(QListView.Snap)
        self.setWordWrap(True)
        self.setSpacing(2)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(False)
        self.setMouseTracking(True)
        self.setItemDelegate(_DropHighlightDelegate(self))
        self._drag_source_row: int | None = None
        self._drop_row: int | None = None
        self._hover_row: int = -1

    @property
    def drop_highlight_row(self) -> int:
        """ช่องคู่สลับที่จะโชว์ไฮไลท์ (ไอเทมที่ลากจะลงช่องนี้พอดี)."""
        if self._drop_row is None or self.count() == 0:
            return -1
        return min(self._drop_row, self.count() - 1)

    def startDrag(self, supported_actions) -> None:
        self._drag_source_row = self.currentRow()
        self._set_drop_row(None)
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
        event.acceptProposedAction()

    def dragMoveEvent(self, event) -> None:
        if event.source() is self:
            partner = self._partner_row(event.position().toPoint())
            self._set_drop_row(partner if partner is not None else self.count())
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
        self._set_drop_row(self.count())
        event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._set_drop_row(None)
        super().dragLeaveEvent(event)

    def clear(self) -> None:
        self._hover_row = -1
        super().clear()

    def mouseMoveEvent(self, event) -> None:
        hovered = self.itemAt(event.position().toPoint())
        row = self.row(hovered) if hovered is not None else -1
        if row != self._hover_row:
            self._hover_row = row
            self.viewport().update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        if self._hover_row != -1:
            self._hover_row = -1
            self.viewport().update()
        super().leaveEvent(event)

    def contextMenuEvent(self, event) -> None:
        item = self.itemAt(event.pos())
        if item is None:
            return
        self.setCurrentItem(item)
        self.contextMenuRequested.emit(event.globalPos())

    def _hover_cell(self, row: int) -> QRect:
        """กรอบไฮไลท์ hover: ขนาดคงที่จาก gridSize (เท่ากันทุกช่อง)."""
        item_rect = self.visualRect(self.model().index(row, 0))
        cell = QRect(QPoint(0, 0), self.gridSize())
        cell.moveCenter(item_rect.center())
        area = self.viewport().rect()
        if cell.width() <= area.width():
            if cell.left() < area.left():
                cell.moveLeft(area.left())
            elif cell.right() > area.right():
                cell.moveRight(area.right())
        else:
            cell = cell.intersected(area)
        if cell.height() <= area.height():
            if cell.top() < area.top():
                cell.moveTop(area.top())
            elif cell.bottom() > area.bottom():
                cell.moveBottom(area.bottom())
        else:
            cell = cell.intersected(area)
        return cell

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        if 0 <= self._hover_row < self.count():
            painter = QPainter(self.viewport())
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(Qt.NoPen)
            color = self.palette().color(QPalette.ColorRole.Highlight)
            color.setAlpha(45)
            painter.setBrush(color)
            cell = self._hover_cell(self._hover_row)
            painter.drawRoundedRect(cell.adjusted(2, 2, -2, -2), 10, 10)
            painter.end()

    def dropEvent(self, event) -> None:
        partner = self._partner_row(event.position().toPoint())
        self._set_drop_row(None)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.urlsDropped.emit(list(event.mimeData().urls()))
            return
        source = self._drag_source_row
        if source is None:
            source = self.currentRow()
        if source is None or source < 0:
            event.ignore()
            return
        self._move_item(source, partner if partner is not None else self.count())
        self.clearSelection()
        event.acceptProposedAction()
        self.orderChanged.emit()

    def _set_drop_row(self, row: int | None) -> None:
        if row != self._drop_row:
            self._drop_row = row
            self.viewport().update()

    def _partner_row(self, pos: QPoint) -> int | None:
        """แถวไอเทมใต้เมาส์ (คู่สลับ) — None ถ้าปล่อยที่ว่างท้ายสุด."""
        count = self.count()
        if count == 0:
            return None
        index = self.indexAt(pos)
        if index.isValid():
            return index.row()
        last = self.visualRect(self.model().index(count - 1, 0))
        last_cell = QRect(QPoint(0, 0), self.gridSize())
        last_cell.moveCenter(last.center())
        if pos.y() > last_cell.bottom() or (
            last_cell.top() <= pos.y() <= last_cell.bottom()
            and pos.x() > last_cell.right()
        ):
            return None
        best_row = 0
        best_dist = None
        for row in range(count):
            center = self.visualRect(self.model().index(row, 0)).center()
            dist = abs(center.x() - pos.x()) + abs(center.y() - pos.y())
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_row = row
        return best_row

    def _move_item(self, source: int, target: int) -> None:
        """สลับไอเทมช่อง source กับช่อง target (target == count คือย้ายไปท้ายสุด)."""
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
