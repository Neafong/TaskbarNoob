import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from taskbargroups.core.models import Group

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication, QLabel

    HAVE_QT = True
except ImportError:
    HAVE_QT = False


def _all_texts(widget) -> list[str]:
    texts: list[str] = []
    for label in widget.findChildren(QLabel):
        texts.append(label.text())
    return texts


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class GroupEditorUiTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        from taskbargroups.core.i18n import setup
        from taskbargroups.gui.group_editor import GroupEditor

        setup("th")
        self.editor = GroupEditor(None, None)
        self.editor.name_edit.setText("Test")

    def test_editor_builds(self) -> None:
        self.assertEqual(self.editor.name_edit.text(), "Test")

    def test_width_row_has_แถว(self) -> None:
        texts = " ".join(_all_texts(self.editor))
        self.assertIn("แถว", texts)
        self.assertIn("ชื่อกลุ่ม", texts)

    def test_labels_opened_removed(self) -> None:
        texts = "\n".join(_all_texts(self.editor))
        self.assertNotIn("ตัวอย่าง", texts)
        self.assertNotIn("ยังไม่ตั้ง", texts)

    def test_system_button_present(self) -> None:
        from PySide6.QtWidgets import QPushButton

        buttons = [b.text() for b in self.editor.findChildren(QPushButton)]
        self.assertIn("เลือกจากระบบ...", buttons)
        self.assertIn("เลือกไอคอน...", buttons)

    def test_slider_resizes_grid(self) -> None:
        before = self.editor.items_list.iconSize().width()
        self.editor.icon_size_slider.setValue(48)
        self.assertEqual(self.editor.items_list.iconSize().width(), 48)
        self.assertGreater(self.editor.items_list.gridSize().width(), before)

    def test_slider_resizes_grid_at_init(self) -> None:
        self.editor.icon_size_slider.setValue(64)
        self.assertEqual(self.editor.items_list.iconSize().width(), 64)


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class SystemIconDialogTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_scans_some_icons(self) -> None:
        from taskbargroups.gui.group_editor import _SystemIconDialog

        dialog = _SystemIconDialog()
        self.assertGreater(len(dialog._names), 0)
        self.assertLessEqual(len(dialog._names), 4000)
        dialog.close()

    def test_search_filters(self) -> None:
        from taskbargroups.gui.group_editor import _SystemIconDialog

        dialog = _SystemIconDialog()
        dialog.search.setText("firefox")
        for i in range(dialog.grid.count()):
            self.assertIn("firefox", dialog.grid.item(i).text().lower())
        dialog.close()

    def test_names_lowercased_filter_works(self) -> None:
        from taskbargroups.gui.group_editor import _SystemIconDialog

        dialog = _SystemIconDialog()
        dialog.search.setText("FIREFOX")
        self.assertGreater(dialog.grid.count(), 0)
        dialog.close()


if __name__ == "__main__":
    unittest.main()