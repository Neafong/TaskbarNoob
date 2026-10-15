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

    def test_swap_distant(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(0, 3)
        self.assertEqual(_texts(grid), ["i3", "i1", "i2", "i0"])

    def test_swap_backward(self) -> None:
        grid = _make_grid(self.app, 6)
        grid._move_item(5, 0)
        self.assertEqual(_texts(grid), ["i5", "i1", "i2", "i3", "i4", "i0"])

    def test_swap_adjacent(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(0, 1)
        self.assertEqual(_texts(grid), ["i1", "i0", "i2", "i3"])

    def test_noop_when_same(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(2, 2)
        self.assertEqual(_texts(grid), ["i0", "i1", "i2", "i3"])

    def test_move_to_end(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(0, 4)
        self.assertEqual(_texts(grid), ["i1", "i2", "i3", "i0"])

    def test_move_to_end_noop_when_already_last(self) -> None:
        grid = _make_grid(self.app, 4)
        grid._move_item(3, 4)
        self.assertEqual(_texts(grid), ["i0", "i1", "i2", "i3"])


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class DropEventTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_drop_swaps_with_target(self) -> None:
        grid = _make_grid(self.app, 4)
        rect = grid.visualRect(grid.model().index(3, 0))
        pos = QPointF(rect.center().x() + 8, rect.center().y() + 8)
        mime = QMimeData()
        event = QDropEvent(pos, Qt.MoveAction, mime, Qt.LeftButton, Qt.NoModifier)
        grid._drag_source_row = 0
        changed: list[int] = []
        grid.orderChanged.connect(lambda: changed.append(1))
        grid.dropEvent(event)
        self.assertEqual(_texts(grid), ["i3", "i1", "i2", "i0"])
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
        self.assertEqual(_texts(grid), ["i3", "i1", "i2", "i0"])
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

    def test_partner_row_finds_cell_or_none(self) -> None:
        grid = _make_grid(self.app, 4)
        rect = grid.visualRect(grid.model().index(0, 0))
        inside = grid._partner_row(QPoint(rect.center().x(), rect.center().y()))
        self.assertEqual(inside, 0)
        outside = grid._partner_row(
            QPoint(grid.viewport().width() - 2, grid.viewport().height() - 2)
        )
        self.assertIsNone(outside)

    def test_partner_row_in_gap_uses_nearest_cell(self) -> None:
        # ช่องว่างระหว่างเซลล์ต้องได้เซลล์ใกล้สุด — ห้ามตีเป็นท้ายสุด
        grid = _make_grid(self.app, 4)
        left = grid.visualRect(grid.model().index(0, 0))
        right = grid.visualRect(grid.model().index(1, 0))
        quarter = QPoint(
            (left.center().x() * 3 + right.center().x()) // 4,
            (left.center().y() * 3 + right.center().y()) // 4,
        )
        three_quarter = QPoint(
            (left.center().x() + right.center().x() * 3) // 4,
            (left.center().y() + right.center().y() * 3) // 4,
        )
        self.assertEqual(grid._partner_row(quarter), 0)
        self.assertEqual(grid._partner_row(three_quarter), 1)

    def test_drop_highlight_shows_swap_partner(self) -> None:
        # ไฮไลท์ต้องโชว์ช่องคู่สลับ (ไอเทมที่ลากจะลงช่องนี้พอดี)
        grid = _make_grid(self.app, 4)
        for partner in (0, 1, 2, 3):
            with self.subTest(partner=partner):
                grid._set_drop_row(partner)
                self.assertEqual(grid.drop_highlight_row, partner)
        grid._set_drop_row(4)  # ปล่อยที่ว่าง = ไปท้ายสุด → โชว์ช่องสุดท้าย
        self.assertEqual(grid.drop_highlight_row, 3)
        grid._set_drop_row(None)
        self.assertEqual(grid.drop_highlight_row, -1)

    def test_drop_highlight_matches_swap_result(self) -> None:
        # ไฮไลท์ต้องตรงกับผล _move_item จริง (กันไฮไลท์หลอกอีก)
        for source, target in [(0, 1), (0, 3), (3, 0), (1, 4), (2, 2)]:
            with self.subTest(source=source, target=target):
                grid = _make_grid(self.app, 4)
                item = grid.item(source)
                grid._drag_source_row = source
                grid._set_drop_row(target)
                shown = grid.drop_highlight_row
                grid._move_item(source, target)
                self.assertEqual(grid.row(item), shown)
                grid.hide()
                grid.deleteLater()

    def test_drop_highlight_external_shows_last_row(self) -> None:
        # ลากไฟล์จากข้างนอก (ต่อท้ายเสมอ) — โชว์ช่องสุดท้ายให้ตรงกับผลลัพธ์
        grid = _make_grid(self.app, 4)
        grid.clearSelection()
        grid._drag_source_row = None
        grid._set_drop_row(grid.count())
        try:
            self.assertEqual(grid.drop_highlight_row, 3)
        finally:
            grid.hide()
            grid.deleteLater()

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
