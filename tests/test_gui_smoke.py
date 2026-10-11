import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from taskbargroups.core.models import ColorMode, Group, Shortcut
from taskbargroups.core.storage import ConfigStore


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class GuiSmokeTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConfigStore(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_main_window_first_run_empty(self) -> None:
        from taskbargroups.gui.main_window import MainWindow

        window = MainWindow(store=self.store)
        self.assertEqual(window.list.count(), 0)

    def test_main_window_lists_groups(self) -> None:
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(
            Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        )
        window = MainWindow(store=self.store)
        self.assertEqual(window.list.count(), 1)

    def test_editor_result_group(self) -> None:
        from taskbargroups.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store)
        editor.name_edit.setText("My Group")
        editor.width_spin.setValue(4)
        editor.color_combo.setCurrentIndex(
            editor.color_combo.findData(ColorMode.CUSTOM.value)
        )
        editor._custom_color = "#123456"
        editor.opacity_slider.setValue(30)
        editor.icon_size_slider.setValue(48)
        group = editor.result_group()
        self.assertEqual(group.name, "My Group")
        self.assertEqual(group.width, 4)
        self.assertEqual(group.color_mode, ColorMode.CUSTOM)
        self.assertEqual(group.custom_color, "#123456")
        self.assertEqual(group.opacity, 30)
        self.assertEqual(group.icon_size, 48)
        self.assertEqual(group.validate(), [])

    def test_flyout_builds_buttons(self) -> None:
        from taskbargroups.gui.flyout import FlyoutWindow

        group = Group(
            name="G",
            items=[
                Shortcut(name="a", target="/bin/true"),
                Shortcut(name="b", target="/bin/false"),
            ],
        )
        flyout = FlyoutWindow(group, self.store, "G")
        self.assertEqual(len(flyout.buttons), 2)

    def test_flyout_has_no_open_all_button(self) -> None:
        from PySide6.QtWidgets import QPushButton

        from taskbargroups.gui.flyout import FlyoutWindow

        group = Group(name="G", allow_open_all=True)
        flyout = FlyoutWindow(group, self.store, "G")
        self.assertIsNone(flyout.findChild(QPushButton, "openAllButton"))

    def test_shortcut_dialog_keeps_icon_and_source(self) -> None:
        from taskbargroups.gui.group_editor import ShortcutDialog

        dialog = ShortcutDialog(
            shortcut=Shortcut(name="a", target="/bin/true", icon="icons/a.png")
        )
        self.assertEqual(dialog.result_shortcut().icon, "icons/a.png")
        self.assertIsNone(dialog.icon_source())
        dialog._icon_source = "/tmp/new.png"
        self.assertEqual(dialog.icon_source(), "/tmp/new.png")
        self.assertEqual(dialog.result_shortcut().icon, "icons/a.png")

    def test_editor_pending_icons_tracks_live_items(self) -> None:
        from taskbargroups.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store, group=Group(name="G"))
        shortcut = Shortcut(name="a", target="/bin/true")
        editor._group.items.append(shortcut)
        editor._pending_icons[id(shortcut)] = "/tmp/x.png"
        self.assertEqual(editor.pending_icons(), {id(shortcut): "/tmp/x.png"})
        editor._group.items.clear()
        self.assertEqual(editor.pending_icons(), {})

    def test_cache_shortcut_icons_caches_resolvable_target(self) -> None:
        from taskbargroups.gui.main_window import MainWindow

        image = Path(self._tmp.name) / "logo.png"
        image.write_bytes(b"png")
        desktop = Path(self._tmp.name) / "app.desktop"
        desktop.write_text(
            f"[Desktop Entry]\nType=Application\nName=App\nIcon={image}\nExec=app\n",
            encoding="utf-8",
        )
        group = Group(name="G", items=[Shortcut(name="App", target=str(desktop))])
        self.store.save_group(group)
        window = MainWindow(store=self.store)
        window._cache_shortcut_icons(group, "G", {})
        self.assertTrue(group.items[0].icon.startswith("icons/"))
        self.assertTrue(
            self.store.resolve_relative("G", group.items[0].icon).is_file()
        )

    def test_editor_grid_accepts_dropped_file(self) -> None:
        from PySide6.QtCore import QUrl

        from taskbargroups.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store, group=Group(name="G"))
        target = Path(self._tmp.name) / "tool.bin"
        target.write_bytes(b"x")
        editor._on_urls_dropped([QUrl.fromLocalFile(str(target))])
        self.assertEqual(len(editor._group.items), 1)
        self.assertEqual(editor._group.items[0].name, "tool")

    def test_main_window_marks_pinned_rows(self) -> None:
        from unittest import mock

        from taskbargroups.core.desktop import desktop_file_name
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import PINNED_ROLE, MainWindow

        self.store.save_group(Group(name="G", items=[]))
        pinned = {desktop_file_name("G")}
        with mock.patch.object(main_window, "pinned_desktop_ids", return_value=pinned):
            window = MainWindow(store=self.store)
        self.assertTrue(window.list.item(0).data(PINNED_ROLE))

    def test_refresh_pinned_icon_regenerates_launcher(self) -> None:
        from unittest import mock

        from taskbargroups.core.desktop import desktop_file_name
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        old_png = Path(self._tmp.name) / "old.png"
        new_svg = Path(self._tmp.name) / "new.svg"
        old_png.write_bytes(b"png-bytes")
        new_svg.write_bytes(b"svg-bytes")

        group = Group(name="G")
        group.icon = self.store.import_group_icon("G", old_png)
        old_icon = self.store.resolve_relative("G", group.icon)

        with mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self._tmp.name}, clear=False
        ):
            window = MainWindow(store=self.store)
            group.icon = self.store.import_group_icon("G", new_svg)
            new_icon = self.store.resolve_relative("G", group.icon)
            self.assertNotEqual(old_icon, new_icon)
            with mock.patch.object(
                main_window,
                "pinned_desktop_ids",
                return_value={desktop_file_name("G")},
            ), mock.patch.object(
                main_window, "reload_grouped_window_applet", return_value=True
            ) as reload_mock:
                window._refresh_pinned_icon(group, "G")

        desktop_path = (
            Path(self._tmp.name) / "applications" / desktop_file_name("G")
        )
        self.assertTrue(desktop_path.is_file())
        content = desktop_path.read_text(encoding="utf-8")
        self.assertIn("Icon=taskbargroups-g", content)
        self.assertNotIn(str(old_icon), content)
        theme_icon = (
            Path(self._tmp.name)
            / "icons"
            / "hicolor"
            / "scalable"
            / "apps"
            / "taskbargroups-g.svg"
        )
        self.assertTrue(theme_icon.is_file())
        reload_mock.assert_called_once()

    def test_refresh_pinned_icon_skips_when_not_pinned(self) -> None:
        from unittest import mock

        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        group = Group(name="G")
        with mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self._tmp.name}, clear=False
        ):
            window = MainWindow(store=self.store)
            with mock.patch.object(
                main_window, "pinned_desktop_ids", return_value=set()
            ), mock.patch.object(
                main_window, "reload_grouped_window_applet", return_value=True
            ) as reload_mock:
                window._refresh_pinned_icon(group, "G")
        self.assertEqual(reload_mock.call_count, 0)

        self.assertEqual(reload_mock.call_count, 0)

    def test_sync_pinned_launchers_heals_absolute_icon(self) -> None:
        from unittest import mock

        from taskbargroups.core.desktop import desktop_file_name, launcher_id
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        group = Group(name="G")
        icon_src = Path(self._tmp.name) / "icon.svg"
        icon_src.write_bytes(b"<svg/>")
        group.icon = self.store.import_group_icon("G", icon_src)
        self.store.save_group(group)
        apps = Path(self._tmp.name) / "applications"
        apps.mkdir()
        stale = apps / desktop_file_name("G")
        stale.write_text("Icon=/mnt/Backup/old.svg\n", encoding="utf-8")
        with mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self._tmp.name}, clear=False
        ), mock.patch.object(
            main_window,
            "pinned_desktop_ids",
            return_value={desktop_file_name("G")},
        ), mock.patch.object(
            main_window, "reload_grouped_window_applet", return_value=True
        ) as reload_mock:
            MainWindow(store=self.store)
        self.assertIn("Icon=taskbargroups-g", stale.read_text(encoding="utf-8"))
        theme_icon = (
            Path(self._tmp.name)
            / "icons"
            / "hicolor"
            / "scalable"
            / "apps"
            / "taskbargroups-g.svg"
        )
        self.assertTrue(theme_icon.is_file())
        reload_mock.assert_called_once()

    def test_sync_pinned_launchers_skips_when_already_themed(self) -> None:
        from unittest import mock

        from taskbargroups.core.desktop import desktop_file_name
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        apps = Path(self._tmp.name) / "applications"
        apps.mkdir()
        fresh = apps / desktop_file_name("G")
        fresh.write_text("Icon=taskbargroups-g\n", encoding="utf-8")
        with mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self._tmp.name}, clear=False
        ), mock.patch.object(
            main_window,
            "pinned_desktop_ids",
            return_value={desktop_file_name("G")},
        ), mock.patch.object(
            main_window, "reload_grouped_window_applet", return_value=True
        ) as reload_mock:
            MainWindow(store=self.store)
        reload_mock.assert_not_called()

    def test_group_list_pin_click_emits(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QListWidgetItem

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        widget.resize(320, 140)
        item = QListWidgetItem("G")
        item.setData(Qt.UserRole, "G")
        widget.addItem(item)
        widget.show()
        received: list[str] = []
        widget.pinClicked.connect(received.append)
        rect = widget.pin_rect(item)
        QTest.mouseClick(
            widget.viewport(), Qt.LeftButton, Qt.NoModifier, rect.center()
        )
        widget.hide()
        self.assertEqual(received, ["G"])

    def test_status_color_is_theme_aware(self) -> None:
        from PySide6.QtGui import QColor, QPalette

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        dark = widget.palette()
        dark.setColor(QPalette.ColorRole.Base, QColor(0, 0, 0))
        widget.setPalette(dark)
        pinned_dark = widget._status_color(pinned=True)
        self.assertGreater(pinned_dark.lightness(), 200)
        self.assertEqual(pinned_dark.alpha(), 255)
        unpinned_dark = widget._status_color(pinned=False)
        self.assertEqual(unpinned_dark.alpha(), 150)

        light = widget.palette()
        light.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        widget.setPalette(light)
        pinned_light = widget._status_color(pinned=True)
        self.assertLess(pinned_light.lightness(), 128)

    def test_status_icon_paints_both_states(self) -> None:
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QPainter, QPixmap

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        pixmap = QPixmap(40, 30)
        pixmap.fill()
        painter = QPainter(pixmap)
        widget._paint_pin_shape(painter, QRect(6, 4, 28, 22), True)
        widget._paint_pin_shape(painter, QRect(6, 4, 28, 22), False)
        painter.end()

    def test_group_list_pin_click_ignores_body(self) -> None:
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtTest import QTest
        from PySide6.QtWidgets import QListWidgetItem

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        widget.resize(320, 140)
        item = QListWidgetItem("G")
        item.setData(Qt.UserRole, "G")
        widget.addItem(item)
        widget.show()
        received: list[str] = []
        widget.pinClicked.connect(received.append)
        rect = widget.visualItemRect(item)
        QTest.mouseClick(
            widget.viewport(),
            Qt.LeftButton,
            Qt.NoModifier,
            QPoint(rect.left() + 8, rect.center().y()),
        )
        widget.hide()
        self.assertEqual(received, [])

    def test_editor_grid_drops_desktop_icon_source(self) -> None:
        from PySide6.QtCore import QUrl

        from taskbargroups.gui.group_editor import GroupEditor

        image = Path(self._tmp.name) / "logo.png"
        image.write_bytes(b"png")
        desktop = Path(self._tmp.name) / "app.desktop"
        desktop.write_text(
            f"[Desktop Entry]\nType=Application\nName=App\nIcon={image}\nExec=app\n",
            encoding="utf-8",
        )
        editor = GroupEditor(self.store, group=Group(name="G"))
        editor._on_urls_dropped([QUrl.fromLocalFile(str(desktop))])
        self.assertEqual(len(editor._group.items), 1)
        self.assertEqual(list(editor.pending_icons().values()), [str(image)])

    def test_editor_grid_reorders_model(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem

        from taskbargroups.gui.group_editor import GroupEditor

        first = Shortcut(name="a", target="/bin/true")
        second = Shortcut(name="b", target="/bin/false")
        editor = GroupEditor(
            self.store, group=Group(name="G", items=[first, second])
        )
        editor.items_list.clear()
        for item in (second, first):
            entry = QListWidgetItem(item.name)
            entry.setData(Qt.UserRole, item)
            editor.items_list.addItem(entry)
        editor._sync_order()
        self.assertEqual([s.name for s in editor._group.items], ["b", "a"])

    def test_group_list_emits_order_changed_on_drop(self) -> None:
        from PySide6.QtCore import QMimeData, QPointF, Qt
        from PySide6.QtGui import QDropEvent
        from PySide6.QtWidgets import QListWidgetItem

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        item = QListWidgetItem("G")
        item.setData(Qt.UserRole, "G")
        widget.addItem(item)
        received: list[bool] = []
        widget.orderChanged.connect(lambda: received.append(True))
        event = QDropEvent(
            QPointF(5, 5),
            Qt.MoveAction,
            QMimeData(),
            Qt.LeftButton,
            Qt.NoModifier,
        )
        widget.dropEvent(event)
        self.assertEqual(received, [True])

    def test_main_window_saves_group_order_on_change(self) -> None:
        from PySide6.QtCore import Qt

        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="Alpha", items=[]))
        self.store.save_group(Group(name="Beta", items=[]))
        window = MainWindow(store=self.store)
        order = [
            window.list.item(i).data(Qt.UserRole) for i in range(window.list.count())
        ]
        self.assertEqual(order, ["Alpha", "Beta"])
        window.list.addItem(window.list.takeItem(0))
        window.list.orderChanged.emit()
        self.assertEqual(self.store.load_order(), ["Beta", "Alpha"])

    def test_group_context_menu_lists_actions(self) -> None:
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        window = MainWindow(store=self.store)
        window.list.setCurrentRow(0)
        menu = window._group_context_menu("G")
        actions = [a for a in menu.actions() if not a.isSeparator()]
        self.assertEqual(len(actions), 6)
        self.assertTrue(all(a.isEnabled() for a in actions))
        menu.deleteLater()

    def test_group_list_right_click_emits_context_menu(self) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QContextMenuEvent
        from PySide6.QtWidgets import QListWidgetItem

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        widget.resize(320, 140)
        item = QListWidgetItem("G")
        item.setData(Qt.UserRole, "G")
        widget.addItem(item)
        widget.show()
        received: list[object] = []
        widget.contextMenuRequested.connect(received.append)
        rect = widget.visualItemRect(item)
        event = QContextMenuEvent(
            QContextMenuEvent.Mouse, rect.center(), widget.mapToGlobal(rect.center())
        )
        widget.contextMenuEvent(event)
        widget.hide()
        self.assertEqual(len(received), 1)
        self.assertIs(widget.currentItem(), item)

    def test_group_list_right_click_empty_does_nothing(self) -> None:
        from PySide6.QtCore import QPoint, Qt
        from PySide6.QtGui import QContextMenuEvent

        from taskbargroups.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        widget.resize(320, 140)
        widget.show()
        received: list[object] = []
        widget.contextMenuRequested.connect(received.append)
        empty = QPoint(widget.viewport().width() - 4, widget.viewport().height() - 4)
        event = QContextMenuEvent(
            QContextMenuEvent.Mouse, empty, widget.mapToGlobal(empty)
        )
        widget.contextMenuEvent(event)
        widget.hide()
        self.assertEqual(received, [])

    def test_main_window_duplicate_adds_row(self) -> None:
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(
            Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        )
        window = MainWindow(store=self.store)
        window.list.setCurrentRow(0)
        window.on_duplicate()
        self.assertEqual(window.list.count(), 2)

    def test_hotkey_sequence_conversion(self) -> None:
        from PySide6.QtGui import QKeySequence

        from taskbargroups.gui.hotkey_dialog import qt_sequence_to_cinnamon

        self.assertEqual(
            qt_sequence_to_cinnamon(QKeySequence("Ctrl+Shift+G")),
            "<Control><Shift>g",
        )
        self.assertEqual(qt_sequence_to_cinnamon(QKeySequence()), "")


    def test_about_dialog_credits(self) -> None:
        from PySide6.QtWidgets import QLabel

        from taskbargroups.core.i18n import setup, tr
        from taskbargroups.gui.about_dialog import AboutDialog

        setup("th")
        dialog = AboutDialog()
        self.assertEqual(dialog.windowTitle(), tr("about.title"))
        texts = [label.text() for label in dialog.findChildren(QLabel)]
        self.assertTrue(any("นู๊บ" in t and "น้องพริก" in t for t in texts))

    def test_about_donate_button(self) -> None:
        from PySide6.QtWidgets import QPushButton

        from taskbargroups.gui.about_dialog import AboutDialog

        with_donate = AboutDialog(donate_url="https://ko-fi.com/neafong")
        labels = [b.text() for b in with_donate.findChildren(QPushButton)]
        self.assertTrue(any("สนับสนุน" in t or "Support" in t for t in labels))

        without = AboutDialog(donate_url="")
        self.assertFalse(
            any(
                "สนับสนุน" in b.text() or "Support me" in b.text()
                for b in without.findChildren(QPushButton)
            )
        )

    def test_delete_pinned_group_removes_launcher_and_unpins(self) -> None:
        from unittest import mock

        from PySide6.QtWidgets import QMessageBox

        from taskbargroups.core.desktop import desktop_file_name
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        group = Group(name="G")
        icon_src = Path(self._tmp.name) / "icon.svg"
        icon_src.write_bytes(b"<svg/>")
        group.icon = self.store.import_group_icon("G", icon_src)
        self.store.save_group(group)
        desktop_id = desktop_file_name("G")
        icon_file = (
            Path(self._tmp.name) / "icons" / "hicolor" / "scalable" / "apps"
            / "taskbargroups-g.svg"
        )

        with mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self._tmp.name}, clear=False
        ), mock.patch.object(
            main_window, "pinned_desktop_ids", return_value={desktop_id}
        ), mock.patch.object(
            main_window, "unpin_from_panel", return_value=True
        ) as unpin_mock, mock.patch.object(
            main_window, "reload_grouped_window_applet", return_value=True
        ) as reload_mock, mock.patch.object(
            QMessageBox, "question", return_value=QMessageBox.Yes
        ):
            window = MainWindow(store=self.store)
            window.list.setCurrentRow(0)
            window.on_delete()

        launcher = Path(self._tmp.name) / "applications" / desktop_id
        self.assertFalse(launcher.exists())
        self.assertFalse(icon_file.exists())
        unpin_mock.assert_called_once_with(desktop_id)
        self.assertTrue(reload_mock.called)
        self.assertEqual(self.store.list_groups(), [])

    def test_rename_pinned_group_migrates_launcher(self) -> None:
        from unittest import mock

        from taskbargroups.core.desktop import desktop_file_name
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="Old"))
        old_id = desktop_file_name("Old")
        new_id = desktop_file_name("New")

        class FakeDialog:
            dir_name = "Old"

            def result_group(self) -> Group:
                return Group(name="New")

            def icon_source(self):
                return None

            def pending_icons(self):
                return {}

        with mock.patch.dict(
            os.environ, {"XDG_DATA_HOME": self._tmp.name}, clear=False
        ), mock.patch.object(
            main_window, "pinned_desktop_ids", return_value={old_id}
        ), mock.patch.object(
            main_window, "unpin_from_panel", return_value=True
        ) as unpin_mock, mock.patch.object(
            main_window, "pin_to_panel", return_value="grouped-window-list"
        ) as pin_mock, mock.patch.object(
            main_window, "reload_grouped_window_applet", return_value=True
        ):
            window = MainWindow(store=self.store)
            window._persist(FakeDialog())

        apps = Path(self._tmp.name) / "applications"
        self.assertTrue((apps / new_id).is_file())
        self.assertFalse((apps / old_id).exists())
        unpin_mock.assert_called_once_with(old_id)
        pin_mock.assert_called_once_with(new_id)
        self.assertEqual(self.store.list_groups(), ["New"])

    def test_duplicate_group_name_gets_suffix(self) -> None:
        from unittest import mock

        from PySide6.QtWidgets import QMessageBox

        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="Work"))

        class FakeDialog:
            dir_name = None

            def result_group(self) -> Group:
                return Group(name="Work")

            def icon_source(self):
                return None

            def pending_icons(self):
                return {}

        with mock.patch.object(QMessageBox, "information") as info_mock:
            window = MainWindow(store=self.store)
            window._persist(FakeDialog())

        self.assertEqual(set(self.store.list_groups()), {"Work", "Work 2"})
        info_mock.assert_called_once()

    def test_main_window_retranslate_switches_language(self) -> None:
        from taskbargroups.core.i18n import setup
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        setup("th")
        window = MainWindow(store=self.store)
        th_text = window._nav_buttons[0][1].text()
        setup("en")
        window.retranslate()
        en_text = window._nav_buttons[0][1].text()
        self.assertNotEqual(th_text, en_text)
        self.assertEqual(en_text, "Add group")
        setup("th")

    def test_refresh_shows_hotkey_inline(self) -> None:
        from unittest import mock

        from taskbargroups.core.hotkeys import hotkey_slot
        from taskbargroups.gui import main_window
        from taskbargroups.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        with mock.patch.object(
            main_window,
            "group_hotkeys",
            return_value={hotkey_slot("G"): "<Control><Alt>g"},
        ), mock.patch.object(main_window, "pinned_desktop_ids", return_value=set()):
            window = MainWindow(store=self.store)
        self.assertIn("Ctrl+Alt+G", window.list.item(0).text())


if __name__ == "__main__":
    unittest.main()
