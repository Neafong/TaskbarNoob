"""หน้าต่างแก้ไข/สร้างกลุ่ม (Phase 2 MVP)."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QFileInfo, QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFileIconProvider,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QListView,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core import icons as core_icons
from taskbargroups.core.desktop import shortcut_from_path
from taskbargroups.core.i18n import tr
from taskbargroups.core.models import (
    MAX_ICON_SIZE,
    MIN_ICON_SIZE,
    ColorMode,
    Group,
    Shortcut,
    is_hex_color,
)
from taskbargroups.core.storage import ConfigStore
from .button_icons import themed_icon
from .dialogs import show_information, show_warning
from .theme import app_color, app_text_color

_FALLBACK_GRID_ICON = "application-x-executable"
_file_icon_provider = QFileIconProvider()

# ขนาดพรีวิวไอคอนกลุ่ม (คงที่ — ไม่ตามสไลเดอร์ขนาดไอคอน)
_GROUP_ICON_PREVIEW = 48


def _normalize_hex(value: str) -> str:
    """ปรับ hex เป็นรูปเต็ม #rrggbb ตัวพิมพ์เล็ก (ย่อ #rgb → #rrggbb)."""
    value = value.strip()
    if len(value) == 4:
        return "#" + "".join(ch * 2 for ch in value[1:].lower())
    return value.lower()

_ICON_SUFFIXES = {".png", ".svg", ".xpm", ".jpg", ".jpeg"}
_ICON_SCAN_LIMIT = 4000
_ICON_DISPLAY_LIMIT = 1000

_ITEM_BUTTON_ICONS = {
    "add": ("plus-fill.svg",),
    "edit": ("pencil-simple-fill.svg",),
    "delete": ("trash-fill.svg",),
}


def _apply_button_icon(button: QPushButton, kind: str, fallback: str) -> None:
    names = _ITEM_BUTTON_ICONS.get(kind)
    icon = themed_icon(names[0], app_text_color()) if names else QIcon()
    if icon.isNull():
        button.setText(f"{fallback} {button.text()}")
    else:
        button.setIcon(icon)


def _style_dialog_buttons(box: QDialogButtonBox) -> None:
    """ปุ่ม OK/Cancel ของ dialog: ใช้ข้อความตามภาษา + ไอคอน SVG ของเรา."""
    ok_button = box.button(QDialogButtonBox.Ok)
    if ok_button is not None:
        ok_button.setText(tr("dialog.ok"))
        icon = themed_icon("check-fill.svg", app_text_color())
        if not icon.isNull():
            ok_button.setIcon(icon)
    cancel_button = box.button(QDialogButtonBox.Cancel)
    if cancel_button is not None:
        cancel_button.setText(tr("dialog.cancel"))
        icon = themed_icon("x-fill.svg", app_text_color())
        if not icon.isNull():
            cancel_button.setIcon(icon)



class _SystemIconDialog(QDialog):
    """สังเกรายชื่อไอคอนจากชุดธีมของระบบ แล้วให้เลือก/ค้นหาไอคอนได้."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("system_icon.title"))
        self.resize(560, 480)
        self._path: str | None = None
        self._names: dict[str, str] = {}

        layout = QVBoxLayout(self)
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

    def done(self, result: int) -> None:
        if result == QDialog.Accepted and self.grid.currentItem() is not None:
            self._path = self.grid.currentItem().data(Qt.UserRole)
        super().done(result)

    def _scan(self) -> None:
        bases = dict.fromkeys(
            [Path(p) for p in QIcon.themeSearchPaths()]
            + [Path("/usr/share/icons")]
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
            fill.setAlpha(50)  # โปร่งแสงขึ้น นุ่มกว่า
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
    """QListWidget โหมด grid: ลากสลับลำดับได้ + รับไฟล์ที่ลากมาจากข้างนอก.

    Qt ไม่รองรับ drop indicator ของ InternalMove ใน IconMode อย่างถูกต้อง
    (มี FIXME ในซอร์ส Qt) จึงคำนวณตำแหน่งวางเองจากพิกัดเมาส์ และวาดไฮไลท์ช่อง
    เป้าหมายเองให้ตรงกับตำแหน่งที่จะวางจริง.
    """

    urlsDropped = Signal(list)
    orderChanged = Signal()

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
        self._set_drop_row(self._target_row(event.position().toPoint()))
        if event.source() is self:
            event.setDropAction(Qt.MoveAction)
            event.accept()
            return
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

    def _hover_cell(self, row: int) -> QRect:
        """กรอบไฮไลท์ hover: ขนาดคงที่จาก gridSize (เท่ากันทุกช่อง).

        ห้ามใช้ visualRect ตรง ๆ — ความกว้างมันยืดหดตามความยาวข้อความใต้ไอคอน.
        ชิดขอบ viewport ให้เลื่อนกรอบหนี (ไม่ตัดทิ้ง) กรอบจะได้เต็มเท่ากันทุกแถว.
        """
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
            color.setAlpha(45)  # ไฮไลท์ช่องโปร่งแสง (accent เดียวกับหน้าหลัก)
            painter.setBrush(color)
            cell = self._hover_cell(self._hover_row)
            painter.drawRoundedRect(cell.adjusted(2, 2, -2, -2), 10, 10)
            painter.end()

    def dropEvent(self, event) -> None:
        target = self._target_row(event.position().toPoint())
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
        self._move_item(source, target)
        self.clearSelection()
        event.acceptProposedAction()
        self.orderChanged.emit()

    def _set_drop_row(self, row: int | None) -> None:
        if row != self._drop_row:
            self._drop_row = row
            self.viewport().update()

    def _target_row(self, pos: QPoint) -> int:
        """ดัชนีแทรก (0..count) จากพิกัดที่ปล่อย."""
        count = self.count()
        if count == 0:
            return 0
        index = self.indexAt(pos)
        if index.isValid():
            rect = self.visualRect(index)
            if pos.x() > rect.center().x():
                return index.row() + 1
            return index.row()
        last = self.visualRect(self.model().index(count - 1, 0))
        last_cell = QRect(QPoint(0, 0), self.gridSize())
        last_cell.moveCenter(last.center())
        if pos.y() > last_cell.bottom() or (
            last_cell.top() <= pos.y() <= last_cell.bottom()
            and pos.x() > last_cell.center().x()
        ):
            return count
        best_row = 0
        best_dist = None
        for row in range(count):
            rect = self.visualRect(self.model().index(row, 0))
            center = rect.center()
            dist = abs(center.x() - pos.x()) + abs(center.y() - pos.y())
            if best_dist is None or dist < best_dist:
                best_dist = dist
                best_row = row
        rect = self.visualRect(self.model().index(best_row, 0))
        if pos.x() > rect.center().x() or pos.y() > rect.center().y():
            return best_row + 1
        return best_row

    def _move_item(self, source: int, target: int) -> None:
        if target == source or target == source + 1:
            return
        item = self.takeItem(source)
        if item is None:
            return
        if target > source:
            target -= 1
        self.insertItem(target, item)
        self.setCurrentItem(item)

DEFAULT_CUSTOM_COLOR = "#3a3a3a"
_ICON_FILTER = "รูปภาพ (*.png *.svg *.jpg *.jpeg *.ico *.bmp *.xpm);;ทุกไฟล์ (*)"


class ShortcutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, shortcut: Shortcut | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("shortcut.title"))
        self.resize(460, 260)
        self._shortcut = shortcut or Shortcut(name="", target="")
        self._icon_source: str | None = None

        form = QFormLayout(self)

        self.name_edit = QLineEdit(self._shortcut.name)
        self.name_edit.setMaxLength(27)
        form.addRow(tr("shortcut.display_name"), self.name_edit)

        target_row = QHBoxLayout()
        self.target_edit = QLineEdit(self._shortcut.target)
        self.target_edit.textChanged.connect(self._on_target_changed)
        target_browse = QPushButton(tr("shortcut.browse"))
        target_browse.clicked.connect(self._browse_target)
        target_row.addWidget(self.target_edit)
        target_row.addWidget(target_browse)
        target_widget = QWidget()
        target_widget.setLayout(target_row)
        form.addRow(tr("shortcut.target"), target_widget)

        cwd_row = QHBoxLayout()
        self.cwd_edit = QLineEdit(self._shortcut.working_dir or "")
        cwd_browse = QPushButton(tr("shortcut.browse"))
        cwd_browse.clicked.connect(self._browse_cwd)
        cwd_row.addWidget(self.cwd_edit)
        cwd_row.addWidget(cwd_browse)
        cwd_widget = QWidget()
        cwd_widget.setLayout(cwd_row)
        form.addRow(tr("shortcut.working_dir"), cwd_widget)

        self.args_edit = QLineEdit(self._shortcut.arguments)
        form.addRow(tr("shortcut.arguments"), self.args_edit)

        icon_row = QHBoxLayout()
        self.icon_preview = QLabel()
        self.icon_preview.setFixedSize(48, 48)
        self.icon_preview.setAlignment(Qt.AlignCenter)
        pick_icon = QPushButton(tr("shortcut.pick_file"))
        pick_icon.clicked.connect(self._pick_icon)
        auto_icon = QPushButton(tr("shortcut.auto_icon"))
        auto_icon.setToolTip(core_icons.platform_note())
        auto_icon.clicked.connect(self._auto_icon)
        icon_row.addWidget(self.icon_preview)
        icon_row.addWidget(pick_icon)
        icon_row.addWidget(auto_icon)
        icon_widget = QWidget()
        icon_widget.setLayout(icon_row)
        # ไม่มีคำว่า "ไอคอน" — โชว์รูปไอคอนแทน
        form.addRow(icon_widget)
        self._update_icon_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self
        )
        _style_dialog_buttons(buttons)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def _browse_target(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("shortcut.pick_target_dialog"))
        if path:
            self.target_edit.setText(path)
            if not self.name_edit.text().strip():
                self.name_edit.setText(Path(path).stem)

    def _browse_cwd(self) -> None:
        path = QFileDialog.getExistingDirectory(self, tr("shortcut.pick_cwd_dialog"))
        if path:
            self.cwd_edit.setText(path)

    def _on_target_changed(self) -> None:
        if self._icon_source is None:
            self._update_icon_preview()

    def _update_icon_preview(self) -> None:
        """โชว์รูปไอคอนปัจจุบัน (48px) แทนข้อความ."""
        pixmap: QPixmap | None = None
        for candidate in (
            Path(self._icon_source) if self._icon_source else None,
            Path(self._shortcut.icon) if self._shortcut.icon else None,
        ):
            if candidate is not None and candidate.is_file():
                loaded = QPixmap(str(candidate))
                if not loaded.isNull():
                    pixmap = loaded
                    break
        if pixmap is None:
            auto = core_icons.resolve_icon_source(self.target_edit.text().strip() or None)
            if auto is not None and auto.is_file():
                loaded = QPixmap(str(auto))
                if not loaded.isNull():
                    pixmap = loaded
        if pixmap is None:
            pixmap = QIcon.fromTheme(_FALLBACK_GRID_ICON).pixmap(48, 48)
        if pixmap is not None and not pixmap.isNull():
            self.icon_preview.setPixmap(
                pixmap.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.icon_preview.clear()

    def _pick_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, tr("shortcut.pick_icon_dialog"), "", _ICON_FILTER
        )
        if path:
            self._icon_source = path
            self._update_icon_preview()

    def _auto_icon(self) -> None:
        target = self.target_edit.text().strip()
        source = core_icons.resolve_icon_source(target)
        if source is None and target and os.access(target, os.X_OK):
            source = core_icons.icon_from_executable(target)
        if source is None:
            show_information(
                self,
                tr("shortcut.no_icon_title"),
                tr("shortcut.no_icon_body"),
            )
            return
        self._icon_source = str(source)
        self._update_icon_preview()

    def _on_accept(self) -> None:
        if not self.target_edit.text().strip():
            show_warning(
                self, tr("err.generic"), tr("shortcut.missing_target")
            )
            return
        self.accept()

    def result_shortcut(self) -> Shortcut:
        return Shortcut(
            name=self.name_edit.text().strip(),
            target=self.target_edit.text().strip(),
            working_dir=self.cwd_edit.text().strip() or None,
            arguments=self.args_edit.text(),
            icon=self._shortcut.icon,
        )

    def icon_source(self) -> str | None:
        return self._icon_source


class GroupEditor(QDialog):
    def __init__(
        self,
        store: ConfigStore,
        parent: QWidget | None = None,
        group: Group | None = None,
        dir_name: str | None = None,
    ) -> None:
        super().__init__(parent)
        self.store = store
        self.dir_name = dir_name
        self._group = group or Group(name="")
        self._custom_color = self._group.custom_color or DEFAULT_CUSTOM_COLOR
        self._icon_source: str | None = None
        self._pending_icons: dict[int, str] = {}

        self.setWindowTitle(
            tr("editor.edit_title") if group else tr("editor.new_title")
        )
        self.resize(520, 560)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit(self._group.name)
        self.name_edit.setMaxLength(49)
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 50)
        self.width_spin.setValue(self._group.width)

        top_row = QHBoxLayout()
        top_row.addWidget(self.name_edit, 1)
        top_row.addSpacing(16)
        top_row.addWidget(QLabel(tr("editor.cols")))
        top_row.addWidget(self.width_spin)
        top_widget = QWidget()
        top_widget.setLayout(top_row)
        form.addRow(tr("editor.group_name"), top_widget)

        color_row = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItem(tr("editor.bg_dark"), ColorMode.DARK.value)
        self.color_combo.addItem(tr("editor.bg_light"), ColorMode.LIGHT.value)
        self.color_combo.addItem(tr("editor.bg_custom"), ColorMode.CUSTOM.value)
        self.color_combo.setCurrentIndex(
            max(0, self.color_combo.findData(self._group.color_mode.value))
        )
        self.color_combo.currentIndexChanged.connect(self._refresh_color_button)
        self.color_swatch = QPushButton()
        self.color_swatch.setFixedSize(32, 32)
        self.color_swatch.setCursor(Qt.PointingHandCursor)
        self.color_swatch.setToolTip(tr("editor.pick_color"))
        self.color_swatch.clicked.connect(self._pick_color)
        self.color_hex = QLineEdit(self._custom_color)
        self.color_hex.setMaxLength(7)
        self.color_hex.setPlaceholderText("#RRGGBB")
        self.color_hex.setToolTip(tr("editor.hex_tip"))
        self.color_hex.textEdited.connect(self._on_hex_edited)
        self.color_hex.editingFinished.connect(self._on_hex_finished)
        color_row.addWidget(self.color_combo, 1)
        color_row.addWidget(self.color_swatch)
        color_row.addWidget(self.color_hex, 1)
        color_widget = QWidget()
        color_widget.setLayout(color_row)
        form.addRow(tr("editor.bg_color"), color_widget)

        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(max(0, min(100, self._group.opacity)))
        self.opacity_spin = QSpinBox()
        self.opacity_spin.setRange(0, 100)
        self.opacity_spin.setSuffix(" %")
        self.opacity_spin.setValue(self.opacity_slider.value())
        self._link_slider_spin(self.opacity_slider, self.opacity_spin)
        form.addRow(tr("editor.opacity"), self._slider_spin_row(self.opacity_slider, self.opacity_spin))

        self.icon_size_slider = QSlider(Qt.Horizontal)
        self.icon_size_slider.setRange(MIN_ICON_SIZE, MAX_ICON_SIZE)
        self.icon_size_slider.setValue(
            max(MIN_ICON_SIZE, min(MAX_ICON_SIZE, self._group.icon_size))
        )
        self.icon_size_spin = QSpinBox()
        self.icon_size_spin.setRange(MIN_ICON_SIZE, MAX_ICON_SIZE)
        self.icon_size_spin.setSuffix(" px")
        self.icon_size_spin.setValue(self.icon_size_slider.value())
        self._link_slider_spin(self.icon_size_slider, self.icon_size_spin)
        self.icon_size_slider.valueChanged.connect(self._refresh_icon_ui)
        form.addRow(
            tr("editor.icon_size"), self._slider_spin_row(self.icon_size_slider, self.icon_size_spin)
        )

        icon_row = QHBoxLayout()
        self.icon_preview = QLabel()
        # พรีวิวไอคอนกลุ่มขนาดคงที่ — ไม่ขยายตามสไลเดอร์ขนาดไอคอน
        # (สไลเดอร์คุมแค่ไอคอนในกริดด้านล่างเพื่อบอกขนาด Layout)
        self.icon_preview.setFixedSize(
            _GROUP_ICON_PREVIEW, _GROUP_ICON_PREVIEW
        )
        self.icon_preview.setAlignment(Qt.AlignCenter)
        icon_button = QPushButton(tr("editor.pick_icon"))
        icon_button.setToolTip(tr("editor.pick_icon_tip"))
        icon_button.clicked.connect(self._pick_icon)
        system_button = QPushButton(tr("editor.choose_system"))
        system_button.setToolTip(tr("editor.choose_system_tip"))
        system_button.clicked.connect(self._pick_system_icon)
        icon_row.addWidget(self.icon_preview)
        icon_row.addWidget(icon_button)
        icon_row.addWidget(system_button)
        icon_row.addStretch(1)
        icon_widget = QWidget()
        icon_widget.setLayout(icon_row)
        form.addRow(tr("editor.group_icon"), icon_widget)

        layout.addLayout(form)

        layout.addWidget(QLabel(tr("editor.shortcut_list_hint")))
        self.items_list = ShortcutGrid()
        self.items_list.setMinimumHeight(200)
        self.items_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.items_list.urlsDropped.connect(self._on_urls_dropped)
        self.items_list.orderChanged.connect(self._sync_order)
        layout.addWidget(self.items_list)

        item_buttons = QHBoxLayout()
        add_button = QPushButton(tr("editor.add"))
        edit_button = QPushButton(tr("main.edit"))
        remove_button = QPushButton(tr("main.delete"))
        _apply_button_icon(add_button, "add", "➕")
        _apply_button_icon(edit_button, "edit", "📝")
        _apply_button_icon(remove_button, "delete", "🗑️")
        add_button.clicked.connect(self._add_item)
        edit_button.clicked.connect(self._edit_item)
        remove_button.clicked.connect(self._remove_item)
        item_buttons.addWidget(add_button)
        item_buttons.addWidget(edit_button)
        item_buttons.addWidget(remove_button)
        item_buttons.addStretch(1)
        layout.addLayout(item_buttons)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        _style_dialog_buttons(buttons)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._reload_items()
        self._refresh_color_button()
        self._refresh_icon_ui()

    @staticmethod
    def _link_slider_spin(slider: QSlider, spin: QSpinBox) -> None:
        def on_slider(v: int) -> None:
            if spin.value() != v:
                spin.blockSignals(True)
                spin.setValue(v)
                spin.blockSignals(False)

        def on_spin(v: int) -> None:
            slider.setValue(v)

        slider.valueChanged.connect(on_slider)
        spin.valueChanged.connect(on_spin)

    @staticmethod
    def _slider_spin_row(slider: QSlider, spin: QSpinBox) -> QWidget:
        row = QHBoxLayout()
        row.addWidget(slider, 1)
        row.addWidget(spin)
        container = QWidget()
        container.setLayout(row)
        return container

    def _preview_icon(self) -> QIcon:
        if self._icon_source:
            icon = QIcon(self._icon_source)
            if not icon.isNull():
                return icon
        if self._group.icon and self.dir_name:
            cached = self.store.resolve_relative(self.dir_name, self._group.icon)
            if cached is not None:
                icon = QIcon(str(cached))
                if not icon.isNull():
                    return icon
        return QIcon.fromTheme("folder")

    def _refresh_icon_ui(self) -> None:
        size = self.icon_size_slider.value()
        self.icon_preview.setPixmap(
            self._preview_icon().pixmap(_GROUP_ICON_PREVIEW, _GROUP_ICON_PREVIEW)
        )
        self.items_list.setIconSize(QSize(size, size))
        self.items_list.setGridSize(QSize(max(72, size + 52), max(72, size + 44)))

    def _refresh_color_button(self) -> None:
        is_custom = self.color_combo.currentData() == ColorMode.CUSTOM.value
        self.color_swatch.setEnabled(is_custom)
        self.color_hex.setEnabled(is_custom)
        self._update_color_ui(from_swatch=True)

    def _update_color_ui(self, from_swatch: bool = True) -> None:
        border = app_color(QPalette.ColorRole.Mid).name()
        color = QColor(self._custom_color)
        if color.isValid() and is_hex_color(self._custom_color):
            self.color_swatch.setStyleSheet(
                f"background: {color.name()}; border: 1px solid {border}; border-radius: 4px;"
            )
            if from_swatch:
                self.color_hex.setText(color.name())
        else:
            self.color_swatch.setStyleSheet(
                f"background: transparent; border: 1px solid {border}; border-radius: 4px;"
            )

    def _on_hex_edited(self, text: str) -> None:
        if is_hex_color(text):
            self._custom_color = _normalize_hex(text)
            self._update_color_ui(from_swatch=False)

    def _on_hex_finished(self) -> None:
        text = self.color_hex.text()
        if is_hex_color(text):
            self._custom_color = _normalize_hex(text)
            self._update_color_ui(from_swatch=True)
        else:
            self.color_hex.setText(self._custom_color)

    def _pick_color(self) -> None:
        color = QColorDialog.getColor(QColor(self._custom_color), self, tr("editor.pick_color"))
        if color.isValid():
            self._custom_color = color.name()
            self._update_color_ui(from_swatch=True)

    def _pick_icon(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("editor.pick_icon_dialog"),
            "",
            "Images (*.png *.jpg *.jpeg *.svg *.ico *.bmp);;All files (*)",
        )
        if path:
            self._icon_source = path
            self._refresh_icon_ui()

    def _pick_system_icon(self) -> None:
        dialog = _SystemIconDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_path():
            self._icon_source = dialog.selected_path()
            self._refresh_icon_ui()

    def _reload_items(self) -> None:
        self.items_list.clear()
        for item in self._group.items:
            entry = QListWidgetItem()
            entry.setIcon(self._icon_for(item))
            entry.setText(item.name or item.target)
            entry.setTextAlignment(Qt.AlignHCenter | Qt.AlignTop)
            entry.setToolTip(item.target)
            entry.setData(Qt.UserRole, item)
            self.items_list.addItem(entry)

    def _icon_for(self, item: Shortcut) -> QIcon:
        source = self._pending_icons.get(id(item))
        if source:
            icon = QIcon(source)
            if not icon.isNull():
                return icon
        if item.icon and self.dir_name:
            cached = self.store.resolve_relative(self.dir_name, item.icon)
            if cached is not None:
                icon = QIcon(str(cached))
                if not icon.isNull():
                    return icon
        if item.target and core_icons.is_appimage(item.target):
            embedded = core_icons.icon_from_appimage(item.target)
            if embedded is not None:
                icon = QIcon(str(embedded))
                if not icon.isNull():
                    return icon
        if item.target and Path(item.target).is_file():
            provider = QFileIconProvider()
            return provider.icon(QFileInfo(item.target))
        theme = core_icons.find_theme_icon(Path(item.target).stem) if item.target else None
        if theme:
            icon = QIcon(str(theme))
            if not icon.isNull():
                return icon
        return QIcon.fromTheme(_FALLBACK_GRID_ICON)

    def _on_urls_dropped(self, urls) -> None:
        added = False
        for url in urls:
            if not url.isLocalFile():
                continue
            path = url.toLocalFile()
            shortcut = shortcut_from_path(path)
            if shortcut is None:
                continue
            self._group.items.append(shortcut)
            source = core_icons.resolve_icon_source(path)
            if source is None and os.access(path, os.X_OK):
                source = core_icons.icon_from_executable(path)
            if source is not None:
                self._pending_icons[id(shortcut)] = str(source)
            added = True
        if added:
            QTimer.singleShot(0, self._reload_items)

    def _sync_order(self) -> None:
        ordered = [
            self.items_list.item(row).data(Qt.UserRole)
            for row in range(self.items_list.count())
        ]
        if len(ordered) == len(self._group.items):
            self._group.items = ordered

    def _on_item_double_clicked(self, entry: QListWidgetItem) -> None:
        self.items_list.setCurrentItem(entry)
        self._edit_item()

    def _selected_item(self) -> QListWidgetItem | None:
        return self.items_list.currentItem()

    def _add_item(self) -> None:
        dialog = ShortcutDialog(self)
        if dialog.exec() == QDialog.Accepted:
            shortcut = dialog.result_shortcut()
            self._group.items.append(shortcut)
            if dialog.icon_source():
                self._pending_icons[id(shortcut)] = dialog.icon_source()
            self._reload_items()

    def _edit_item(self) -> None:
        selected = self._selected_item()
        if selected is None:
            return
        index = self.items_list.row(selected)
        old = self._group.items[index]
        dialog = ShortcutDialog(self, shortcut=old)
        if dialog.exec() == QDialog.Accepted:
            shortcut = dialog.result_shortcut()
            self._group.items[index] = shortcut
            self._pending_icons.pop(id(old), None)
            if dialog.icon_source():
                self._pending_icons[id(shortcut)] = dialog.icon_source()
            self._reload_items()

    def _remove_item(self) -> None:
        selected = self._selected_item()
        if selected is None:
            return
        row = self.items_list.row(selected)
        removed = self._group.items.pop(row)
        self._pending_icons.pop(id(removed), None)
        self._reload_items()

    def _on_accept(self) -> None:
        errors = self.result_group().validate()
        if errors:
            show_warning(self, tr("err.invalid_data"), "\n".join(errors))
            return
        self.accept()

    def result_group(self) -> Group:
        return Group(
            name=self.name_edit.text().strip(),
            icon=self._group.icon,
            width=self.width_spin.value(),
            color_mode=ColorMode.from_value(self.color_combo.currentData()),
            custom_color=(
                self._custom_color
                if self.color_combo.currentData() == ColorMode.CUSTOM.value
                else None
            ),
            opacity=self.opacity_slider.value(),
            icon_size=self.icon_size_slider.value(),
            allow_open_all=self._group.allow_open_all,
            items=list(self._group.items),
        )

    def icon_source(self) -> str | None:
        return self._icon_source

    def pending_icons(self) -> dict[int, str]:
        live = {id(item) for item in self._group.items}
        return {key: value for key, value in self._pending_icons.items() if key in live}
