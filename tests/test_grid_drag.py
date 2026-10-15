import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QMimeData, QPoint, QPointF, Qt
    from PySide6.QtGui import QDropEvent
    from PySide6.QtWidgets import QAbstractItemView, QApplication, QListWidgetItem

    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def _make_grid(app, count: int):
    from taskbargroups.gui.group_editor import ShortcutGrid

    grid = ShortcutGrid()
    for i in range(count):
        grid.addItem(QListWidgetItem(f"i{i}"))
    grid.resize(360, 300)
    grid.show()
    app.processEvents()
    return grid


def _texts(grid):
    return [grid.item(r).text() for r in range(grid.count())]


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class MoveItemTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_move_forward(self) -> None:
        grid = _make_grid(self.app, 6)
        grid._move_item(0, 4)
        self.assertEqual(_texts(grid), ["i1", "i2", "i3", "i0", "i4", "i5"])

    def test_move_backward(self) -> None:
        grid = _make_grid(self.app, 6)
        grid._move_item(5, 0)
        self.assertEqual(_texts(grid), ["i5", "i0", "i1", "i2", "i3", "i4"])

    def test_noop_when_same_or_adjacent(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(2, 2)
        grid._move_item(2, 3)
        self.assertEqual(_texts(grid), ["i0", "i1", "i2", "i3"])

    def test_move_to_end(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(0, 4)
        self.assertEqual(_texts(grid), ["i1", "i2", "i3", "i0"])


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class DropEventTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_drop_reorders_to_target(self) -> None:
        grid = _make_grid(self.app, 4)
        rect = grid.visualRect(grid.model().index(3, 0))
        pos = QPointF(rect.center().x() + 8, rect.center().y() + 8)
        mime = QMimeData()
        event = QDropEvent(pos, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        grid._drag_source_row = 0
        changed: list[int] = []
        grid.orderChanged.connect(lambda: changed.append(1))
        grid.dropEvent(event)
        self.assertEqual(_texts(grid), ["i1", "i2", "i3", "i0"])
        self.assertEqual(changed, [1])

    def test_internal_drop_leaves_selection_empty(self) -> None:
        grid = _make_grid(self.app, 4)
        grid.setDragDropMode(QAbstractItemView.InternalMove)
        grid.setDefaultDropAction(Qt.MoveAction)
        rect = grid.visualRect(grid.model().index(3, 0))
        pos = QPointF(rect.center().x() + 8, rect.center().y() + 8)
        mime = QMimeData()
        event = QDropEvent(pos, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        grid._drag_source_row = 0
        grid.dropEvent(event)
        self.assertEqual(_texts(grid), ["i1", "i2", "i3", "i0"])
        self.assertEqual(grid.selectedItems(), [])

    def test_drop_onto_empty_area_moves_to_end(self) -> None:
        grid = _make_grid(self.app, 4)
        pos = QPointF(grid.viewport().width() - 2, grid.viewport().height() - 2)
        mime = QMimeData()
        event = QDropEvent(pos, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        grid._drag_source_row = 0
        grid.dropEvent(event)
        self.assertEqual(_texts(grid), ["i1", "i2", "i3", "i0"])

    def test_url_drop_emits_signal(self) -> None:
        grid = _make_grid(self.app, 2)
        mime = QMimeData()
        from PySide6.QtCore import QUrl

        mime.setUrls([QUrl.fromLocalFile("/tmp/example.desktop")])
        event = QDropEvent(
            QPointF(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier
        )
        received: list[int] = []
        grid.urlsDropped.connect(lambda urls: received.append(len(urls)))
        grid.dropEvent(event)
        self.assertEqual(received, [1])

    def test_target_row_clamps_and_finds_cell(self) -> None:
        grid = _make_grid(self.app, 4)
        rect = grid.visualRect(grid.model().index(0, 0))
        left = grid._target_row(QPoint(rect.left() + 1, rect.center().y()))
        self.assertEqual(left, 0)
        right = grid._target_row(QPoint(rect.right() + 1, rect.center().y()))
        self.assertEqual(right, 1)

    def test_hover_cell_same_size_for_all_items(self) -> None:
        # ไฮไลท์ hover ต้องเท่ากันทุกช่อง — ห้ามยืดหดตามความยาวข้อความ
        from PySide6.QtGui import QColor, QIcon, QPixmap
        from PySide6.QtWidgets import QListWidgetItem

        from taskbargroups.gui.group_editor import ShortcutGrid

        def icon() -> QIcon:
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor("red"))
            return QIcon(pixmap)

        grid = ShortcutGrid()
        grid.addItem(QListWidgetItem(icon(), "A"))
        grid.addItem(QListWidgetItem(icon(), "Tahoma2D ชื่อยาว ๆ ตัดหลายบรรทัด"))
        grid.resize(600, 600)
        grid.show()
        self.app.processEvents()
        try:
            rects = [grid.visualRect(grid.model().index(r, 0)) for r in range(2)]
            self.assertNotEqual(
                rects[0].width(), rects[1].width(), "visualRect ต้องต่างกัน (เทสต์ถึงมีความหมาย)"
            )
            cells = [grid._hover_cell(r) for r in range(2)]
            self.assertEqual(cells[0].size(), cells[1].size())
            self.assertEqual(cells[0].size(), grid.gridSize())
        finally:
            grid.hide()
            grid.deleteLater()


if __name__ == "__main__":
    unittest.main()
