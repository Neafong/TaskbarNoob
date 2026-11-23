import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from taskbarnoob.core.models import ColorMode, Group, Shortcut
from taskbarnoob.core.storage import ConfigStore


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
        from taskbarnoob.gui.main_window import MainWindow

        window = MainWindow(store=self.store)
        self.assertEqual(window.list.count(), 0)

    def test_main_window_lists_groups(self) -> None:
        from taskbarnoob.gui.main_window import MainWindow

        self.store.save_group(
            Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        )
        window = MainWindow(store=self.store)
        self.assertEqual(window.list.count(), 1)

    def test_editor_result_group(self) -> None:
        from taskbarnoob.gui.group_editor import GroupEditor

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

    def test_editor_hex_field_syncs_custom_color(self) -> None:
        from taskbarnoob.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store)
        editor.color_combo.setCurrentIndex(
            editor.color_combo.findData(ColorMode.CUSTOM.value)
        )
        editor.color_hex.setText("#abc")
        editor._on_hex_finished()
        self.assertEqual(editor._custom_color, "#aabbcc")
        self.assertEqual(editor.color_hex.text(), "#aabbcc")
        editor.color_hex.setText("not-a-color")
        editor._on_hex_finished()
        self.assertEqual(editor.color_hex.text(), "#aabbcc")

    def test_editor_swatch_toggles_with_color_mode(self) -> None:
        from taskbarnoob.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store)
        editor.color_combo.setCurrentIndex(
            editor.color_combo.findData(ColorMode.DARK.value)
        )
        self.assertFalse(editor.color_swatch.isEnabled())
        self.assertFalse(editor.color_hex.isEnabled())
        editor.color_combo.setCurrentIndex(
            editor.color_combo.findData(ColorMode.CUSTOM.value)
        )
        self.assertTrue(editor.color_swatch.isEnabled())
        self.assertTrue(editor.color_hex.isEnabled())

    def test_flyout_builds_buttons(self) -> None:
        from taskbarnoob.gui.flyout import FlyoutWindow

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

        from taskbarnoob.gui.flyout import FlyoutWindow

        group = Group(name="G", allow_open_all=True)
        flyout = FlyoutWindow(group, self.store, "G")
        self.assertIsNone(flyout.findChild(QPushButton, "openAllButton"))

    def test_shortcut_dialog_keeps_icon_and_source(self) -> None:
        from taskbarnoob.gui.group_editor import ShortcutDialog

        dialog = ShortcutDialog(
            shortcut=Shortcut(name="a", target="/bin/true", icon="icons/a.png")
        )
        self.assertEqual(dialog.result_shortcut().icon, "icons/a.png")
        self.assertIsNone(dialog.icon_source())
        dialog._icon_source = "/tmp/new.png"
        self.assertEqual(dialog.icon_source(), "/tmp/new.png")
        self.assertEqual(dialog.result_shortcut().icon, "icons/a.png")

    def test_hotkey_dialog_saves_focus_scale(self) -> None:
        from taskbarnoob.gui.hotkey_dialog import HotkeyDialog

        group = Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        self.store.save_group(group)
        dialog = HotkeyDialog(group, self.store, "G")
        from taskbarnoob.core.models import DEFAULT_FOCUS_SCALE, MIN_FOCUS_SCALE

        expected_default = int(round(DEFAULT_FOCUS_SCALE * 10))
        expected_min = int(round(MIN_FOCUS_SCALE * 10))
        self.assertEqual(dialog.scale_slider.value(), expected_default)
        self.assertEqual(dialog.scale_label.text(), f"{DEFAULT_FOCUS_SCALE:.1f}x")
        dialog.scale_slider.setValue(expected_min)
        self.assertEqual(dialog.scale_label.text(), f"{MIN_FOCUS_SCALE:.1f}x")
        dialog._save_focus_scale()
        self.assertEqual(self.store.load_group("G").focus_scale, MIN_FOCUS_SCALE)
        dialog.deleteLater()
        self.app.processEvents()

    def test_editor_pending_icons_tracks_live_items(self) -> None:
        from taskbarnoob.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store, group=Group(name="G"))
        shortcut = Shortcut(name="a", target="/bin/true")
        editor._group.items.append(shortcut)
        editor._pending_icons[id(shortcut)] = "/tmp/x.png"
        self.assertEqual(editor.pending_icons(), {id(shortcut): "/tmp/x.png"})
        editor._group.items.clear()
        self.assertEqual(editor.pending_icons(), {})

    def test_cache_shortcut_icons_caches_resolvable_target(self) -> None:
        from taskbarnoob.gui.main_window import MainWindow

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

        from taskbarnoob.gui.group_editor import GroupEditor

        editor = GroupEditor(self.store, group=Group(name="G"))
        target = Path(self._tmp.name) / "tool.bin"
        target.write_bytes(b"x")
        editor._on_urls_dropped([QUrl.fromLocalFile(str(target))])
        self.assertEqual(len(editor._group.items), 1)
        self.assertEqual(editor._group.items[0].name, "tool")

    @unittest.skipUnless(sys.platform == "linux", "Linux-only")
    def test_main_window_marks_pinned_rows(self) -> None:
        from unittest import mock

        from taskbarnoob.core.platform.linux.desktop import desktop_file_name
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import PINNED_ROLE, MainWindow

        self.store.save_group(Group(name="G", items=[]))
        pinned = {desktop_file_name("G")}
        with mock.patch.object(main_window, "pinned_desktop_ids", return_value=pinned):
            window = MainWindow(store=self.store)
        self.assertTrue(window.list.item(0).data(PINNED_ROLE))

    @unittest.skipUnless(sys.platform == "linux", "Linux-only")
    def test_refresh_pinned_icon_regenerates_launcher(self) -> None:
        from unittest import mock

        from taskbarnoob.core.platform.linux.desktop import desktop_file_name
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

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
        self.assertIn("Icon=taskbarnoob-g", content)
        self.assertNotIn(str(old_icon), content)
        theme_icon = (
            Path(self._tmp.name)
            / "icons"
            / "hicolor"
            / "scalable"
            / "apps"
            / "taskbarnoob-g.svg"
        )
        self.assertTrue(theme_icon.is_file())
        reload_mock.assert_called_once()

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_folder_button_rewrites_stale_lnk(self) -> None:
        """ปุ่มโฟลเดอร์ต้อง (re)สร้าง `.lnk` แม้มีของอยู่แล้ว — ไม่งั้นไอคอนที่เพิ่ง
        เปลี่ยนไม่อัพเดท จนผู้ใช้ต้องมานั่งลบไฟล์เอง."""
        from unittest import mock

        from taskbarnoob.core.platform import win32 as core_win32
        from taskbarnoob.core.platform.win32 import ico as win32_ico
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        group = self.store.load_group("G")
        window = MainWindow(store=self.store)
        lnk = core_win32.shortcuts_dir() / core_win32.lnk_name("G")

        with mock.patch.object(core_win32, "reveal_in_explorer") as reveal, mock.patch.object(
            main_window, "show_information"
        ), mock.patch.object(
            win32_ico,
            "png_to_ico",
            side_effect=lambda src, **_kw: Path(src).with_suffix(".ico"),
        ):
            window._reveal_launcher_dir(group, "G")
            self.assertTrue(lnk.is_file())
            with mock.patch.object(
                MainWindow, "_install_launcher", wraps=window._install_launcher
            ) as install:
                window._reveal_launcher_dir(group, "G")
                # ของเดิมมีอยู่แล้วแต่ต้องสร้างใหม่ (รอบ #21 เคย fast-path ข้ามไป → ไอคอนค้าง)
                install.assert_called_once()
        reveal.assert_called()

    def test_refresh_pinned_icon_skips_when_not_pinned(self) -> None:
        from unittest import mock

        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

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

    @unittest.skipUnless(sys.platform == "linux", "Linux-only")
    def test_sync_pinned_launchers_heals_absolute_icon(self) -> None:
        from unittest import mock

        from taskbarnoob.core.platform.linux.desktop import desktop_file_name, launcher_id
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

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
        self.assertIn("Icon=taskbarnoob-g", stale.read_text(encoding="utf-8"))
        theme_icon = (
            Path(self._tmp.name)
            / "icons"
            / "hicolor"
            / "scalable"
            / "apps"
            / "taskbarnoob-g.svg"
        )
        self.assertTrue(theme_icon.is_file())
        reload_mock.assert_called_once()

    def test_sync_pinned_launchers_skips_when_already_themed(self) -> None:
        from unittest import mock

        from taskbarnoob.core.platform.linux.desktop import desktop_file_name
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        apps = Path(self._tmp.name) / "applications"
        apps.mkdir()
        fresh = apps / desktop_file_name("G")
        fresh.write_text("Icon=taskbarnoob-g\n", encoding="utf-8")
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

        from taskbarnoob.gui.main_window import GroupListWidget

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

        from taskbarnoob.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        with mock.patch.object(sys, "platform", "linux"):
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

    def test_windows_status_color_distinguishes_states(self) -> None:
        """ฝั่ง Windows ต้องแยกสีให้เห็นชัดตอนเปิดแอป (ไม่ต้อง hover)"""
        from taskbarnoob.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        with mock.patch.object(sys, "platform", "win32"):
            on = widget._status_color(pinned=True)
            off = widget._status_color(pinned=False)
        self.assertGreater(on.lightness(), off.lightness())  # ปักแล้วสว่างกว่า
        self.assertGreater(on.red(), on.blue())  # อุ่น (ส้ม) ไม่ใช่เทา
        self.assertEqual(off.red(), off.green())
        self.assertEqual(off.green(), off.blue())  # ยังไม่ปัก = เทาสะอาด

    def test_status_icon_paints_both_states(self) -> None:
        from PySide6.QtCore import QRect
        from PySide6.QtGui import QPainter, QPixmap

        from taskbarnoob.gui.main_window import GroupListWidget

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

        from taskbarnoob.gui.main_window import GroupListWidget

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

    def _make_group_list(self, names):
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem

        from taskbarnoob.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        for name in names:
            item = QListWidgetItem(name)
            item.setData(Qt.UserRole, name)
            widget.addItem(item)
        widget.resize(320, 200)
        widget.show()
        self.app.processEvents()
        return widget

    def _group_order(self, widget) -> list:
        return [widget.item(i).text() for i in range(widget.count())]

    def test_group_list_swap_rows(self) -> None:
        # หน้าหลักลากสลับต้องสลับที่กัน (แบบเดียวกับกริด) ไม่ใช่เลื่อนทั้งแถว
        widget = self._make_group_list(["g0", "g1", "g2", "g3"])
        try:
            widget._swap_rows(0, 3)
            self.assertEqual(self._group_order(widget), ["g3", "g1", "g2", "g0"])
            widget._swap_rows(3, 0)
            self.assertEqual(self._group_order(widget), ["g0", "g1", "g2", "g3"])
            widget._swap_rows(1, 1)
            self.assertEqual(self._group_order(widget), ["g0", "g1", "g2", "g3"])
        finally:
            widget.hide()
            widget.deleteLater()

    def test_group_list_swap_to_end(self) -> None:
        widget = self._make_group_list(["g0", "g1", "g2", "g3"])
        try:
            widget._swap_rows(0, widget.count())
            self.assertEqual(self._group_order(widget), ["g1", "g2", "g3", "g0"])
            widget._swap_rows(3, widget.count())
            self.assertEqual(self._group_order(widget), ["g1", "g2", "g3", "g0"])
        finally:
            widget.hide()
            widget.deleteLater()

    def test_group_list_drop_swaps_with_partner(self) -> None:
        from PySide6.QtCore import QMimeData, QPointF, Qt
        from PySide6.QtGui import QDropEvent

        widget = self._make_group_list(["g0", "g1", "g2", "g3"])
        try:
            rect = widget.visualItemRect(widget.item(3))
            pos = QPointF(rect.center().x(), rect.center().y())
            event = QDropEvent(
                pos, Qt.MoveAction, QMimeData(), Qt.LeftButton, Qt.NoModifier
            )
            widget._drag_source_row = 0
            changed: list[int] = []
            widget.orderChanged.connect(lambda: changed.append(1))
            widget.dropEvent(event)
            self.assertEqual(self._group_order(widget), ["g3", "g1", "g2", "g0"])
            self.assertEqual(changed, [1])
            self.assertEqual(widget.selectedItems(), [])
            self.assertEqual(widget.count(), 4)
        finally:
            widget.hide()
            widget.deleteLater()

    def test_group_list_drop_highlight(self) -> None:
        widget = self._make_group_list(["g0", "g1", "g2", "g3"])
        try:
            widget._set_drop_row(2)
            self.assertEqual(widget.drop_highlight_row, 2)
            widget._set_drop_row(widget.count())
            self.assertEqual(widget.drop_highlight_row, 3)
            widget._set_drop_row(None)
            self.assertEqual(widget.drop_highlight_row, -1)
        finally:
            widget.hide()
            widget.deleteLater()

    def test_group_list_drop_cell_hugs_row(self) -> None:
        # กรอบ stroke ต้องเกาะขอบแถว (ไม่เล็กจนดูตลก) + มี spacing หายใจ
        # + padding ซ้าย 0 (สไตล์เว้นที่ไอคอนเอง — ร่อง stroke↔ไอคอน ~1px)
        widget = self._make_group_list(["g0", "g1", "g2", "g3"])
        try:
            self.assertEqual(widget.spacing(), 2)
            self.assertIn("padding: 3px 2px 3px 0px", widget.styleSheet())
            item = widget.item(1)
            row_rect = widget.visualItemRect(item)
            cell = widget._drop_cell(item)
            self.assertEqual(cell.width(), row_rect.width() - 2)
            self.assertEqual(cell.height(), row_rect.height() - 2)
        finally:
            widget.hide()
            widget.deleteLater()

    def test_editor_grid_drops_desktop_icon_source(self) -> None:
        from PySide6.QtCore import QUrl

        from taskbarnoob.gui.group_editor import GroupEditor

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

        from taskbarnoob.gui.group_editor import GroupEditor

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

        from taskbarnoob.gui.main_window import GroupListWidget

        widget = GroupListWidget()
        item = QListWidgetItem("G")
        item.setData(Qt.UserRole, "G")
        widget.addItem(item)
        received: list[bool] = []
        widget.orderChanged.connect(lambda: received.append(True))
        widget.setCurrentRow(0)  # จำลองลากจริง (มีแถวต้นทางเสมอ)
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

        from taskbarnoob.gui.main_window import MainWindow

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
        from taskbarnoob.gui.main_window import MainWindow

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

        from taskbarnoob.gui.main_window import GroupListWidget

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

        from taskbarnoob.gui.main_window import GroupListWidget

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
        from taskbarnoob.gui.main_window import MainWindow

        self.store.save_group(
            Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        )
        window = MainWindow(store=self.store)
        window.list.setCurrentRow(0)
        window.on_duplicate()
        self.assertEqual(window.list.count(), 2)

    def test_hotkey_sequence_conversion(self) -> None:
        from PySide6.QtGui import QKeySequence

        from taskbarnoob.gui.hotkey_dialog import qt_sequence_to_cinnamon

        self.assertEqual(
            qt_sequence_to_cinnamon(QKeySequence("Ctrl+Shift+G")),
            "<Control><Shift>g",
        )
        self.assertEqual(qt_sequence_to_cinnamon(QKeySequence()), "")


    def test_about_dialog_credits(self) -> None:
        from PySide6.QtWidgets import QLabel

        from taskbarnoob.core.i18n import setup, tr
        from taskbarnoob.gui.about_dialog import AboutDialog

        setup("th")
        dialog = AboutDialog()
        self.assertEqual(dialog.windowTitle(), tr("about.title"))
        texts = [label.text() for label in dialog.findChildren(QLabel)]
        self.assertTrue(any("นู๊บ" in t and "เจนนี่" in t for t in texts))

    def test_about_donate_button(self) -> None:
        from PySide6.QtWidgets import QPushButton

        from taskbarnoob.gui.about_dialog import AboutDialog

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

    @unittest.skipUnless(sys.platform == "linux", "Linux-only")
    def test_delete_pinned_group_removes_launcher_and_unpins(self) -> None:
        from unittest import mock

        from PySide6.QtWidgets import QMessageBox

        from taskbarnoob.core.platform.linux.desktop import desktop_file_name
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

        group = Group(name="G")
        icon_src = Path(self._tmp.name) / "icon.svg"
        icon_src.write_bytes(b"<svg/>")
        group.icon = self.store.import_group_icon("G", icon_src)
        self.store.save_group(group)
        desktop_id = desktop_file_name("G")
        icon_file = (
            Path(self._tmp.name) / "icons" / "hicolor" / "scalable" / "apps"
            / "taskbarnoob-g.svg"
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
            main_window, "show_question", return_value=QMessageBox.Yes
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

    @unittest.skipUnless(sys.platform == "linux", "Linux-only")
    def test_rename_pinned_group_migrates_launcher(self) -> None:
        from unittest import mock

        from taskbarnoob.core.platform.linux.desktop import desktop_file_name
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

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

        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

        self.store.save_group(Group(name="Work"))

        class FakeDialog:
            dir_name = None

            def result_group(self) -> Group:
                return Group(name="Work")

            def icon_source(self):
                return None

            def pending_icons(self):
                return {}

        with mock.patch.object(main_window, "show_information") as info_mock:
            window = MainWindow(store=self.store)
            window._persist(FakeDialog())

        self.assertEqual(set(self.store.list_groups()), {"Work", "Work 2"})
        info_mock.assert_called_once()

    def test_main_window_retranslate_switches_language(self) -> None:
        from taskbarnoob.core.i18n import setup
        from taskbarnoob.gui.main_window import MainWindow

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

    def test_theme_switch_retints_icons_immediately(self) -> None:
        """regression คลิก 2 รอบ: สลับธีมแล้วไอคอนต้องได้สีใหม่ทันที ไม่รอ event."""
        from PySide6.QtGui import QColor

        from taskbarnoob.gui.main_window import MainWindow
        from taskbarnoob.gui.theme import app_text_color, apply_theme

        app = QApplication.instance() or QApplication([])
        self.addCleanup(apply_theme, app, "light")
        apply_theme(app, "light")
        window = MainWindow(store=self.store)
        window.show()
        app.processEvents()
        apply_theme(app, "dark")
        # ไม่ processEvents — จำลองจังหวะเดียวกับ _on_theme_changed
        # (widget.palette() ยังเป็นสีเก่า แต่ app palette เป็นสีใหม่แล้ว)
        self.assertEqual(app_text_color().name(), QColor("#dddddd").name())
        window.refresh_icons()
        button = window._nav_buttons[0][1]
        pixmap = button.icon().pixmap(32, 32)
        self.assertFalse(pixmap.isNull())
        image = pixmap.toImage()
        expected = QColor("#dddddd").name()
        found = any(
            image.pixelColor(x, y).name() == expected
            for x in range(image.width())
            for y in range(image.height())
        )
        self.assertTrue(found, "ไอคอนต้องถูก tint ด้วยสีธีมใหม่ทันที")

    def test_refresh_shows_hotkey_inline(self) -> None:
        from unittest import mock

        from taskbarnoob.core.platform.linux.hotkeys import hotkey_slot
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import MainWindow

        self.store.save_group(Group(name="G"))
        with mock.patch.object(
            main_window,
            "group_hotkeys",
            return_value={hotkey_slot("G"): "<Control><Alt>g"},
        ), mock.patch.object(main_window, "pinned_desktop_ids", return_value=set()):
            window = MainWindow(store=self.store)
        self.assertIn("Ctrl+Alt+G", window.list.item(0).text())

    def test_group_preview_size_ignores_icon_slider(self) -> None:
        # พรีวิวไอคอนกลุ่มต้องคงที่ 48px — สไลเดอร์คุมแค่ไอคอนในกริด
        from PySide6.QtGui import QColor, QPixmap

        from taskbarnoob.gui.group_editor import _GROUP_ICON_PREVIEW, GroupEditor

        red = QPixmap(64, 64)
        red.fill(QColor("red"))
        source = Path(self._tmp.name) / "group.png"
        self.assertTrue(red.save(str(source)))
        editor = GroupEditor(self.store)
        editor._icon_source = str(source)
        for value in (
            editor.icon_size_slider.minimum(),
            editor.icon_size_slider.maximum(),
        ):
            with self.subTest(size=value):
                editor.icon_size_slider.setValue(value)
                pixmap = editor.icon_preview.pixmap()
                self.assertFalse(pixmap.isNull())
                self.assertEqual(pixmap.width(), _GROUP_ICON_PREVIEW)
                self.assertEqual(pixmap.height(), _GROUP_ICON_PREVIEW)

    def test_button_svg_assets_resolve(self) -> None:
        # กันบั๊กแพ็กเกจ: SVG ปุ่ม (เฟือง/ตา/...) ต้องหาเจอ ไม่ใช่ไอคอนว่าง
        from PySide6.QtGui import QColor

        from taskbarnoob.gui import button_icons
        from taskbarnoob.gui.button_icons import _svg_path, themed_icon

        self.assertTrue(
            button_icons._ASSETS.is_dir(),
            f"หาโฟลเดอร์ไอคอนปุ่มไม่เจอ: {button_icons._ASSETS}",
        )
        for name in ("gear-six-fill.svg", "eye-fill.svg", "plus-fill.svg"):
            with self.subTest(name=name):
                self.assertIsNotNone(_svg_path(name), f"SVG หาย: {name}")
                icon = themed_icon(name, QColor("#dddddd"))
                self.assertFalse(icon.isNull(), f"ไอคอนว่าง: {name}")

    def test_button_assets_prefer_meipass_bundle(self) -> None:
        # โหมด bundle ต้องอ่าน icons จาก sys._MEIPASS (ที่ --add-data วางไว้)
        # ครอบทั้ง layout ใหม่ (_internal/...) ของ PyInstaller 6 และแบบเก่า
        import sys
        from unittest import mock

        import taskbarnoob.gui.button_icons as button_icons

        for sub in ("_internal/taskbarnoob/assets", "taskbarnoob/assets"):
            with self.subTest(layout=sub):
                with tempfile.TemporaryDirectory() as tmp:
                    bundled = Path(tmp) / sub / "icons"
                    bundled.mkdir(parents=True)
                    (bundled / "gear-six-fill.svg").write_text("<svg></svg>")
                    with mock.patch.object(sys, "_MEIPASS", tmp, create=True):
                        self.assertEqual(button_icons._assets_dir(), bundled)


class WindowsPinTooltipTests(unittest.TestCase):
    """Tooltip ปุ่มสถานะบน Windows ต้องบอกชื่อไฟล์ที่ต้องลาก (Linux ใช้ข้อความเดิม)."""

    def _tip(self, platform: str, pinned: bool, dir_name: str = "Game") -> str:
        from taskbarnoob.core.models import Group
        from taskbarnoob.gui.main_window import _pin_tooltip

        group = Group(name="Game", items=[])
        with mock.patch.object(sys, "platform", platform):
            return _pin_tooltip(group, pinned, dir_name)

    def test_windows_not_pinned_names_the_file(self) -> None:
        tip = self._tip("win32", False)
        self.assertIn("Game.lnk", tip)  # บอกชื่อไฟล์ที่ต้องลาก
        self.assertNotEqual(tip, "Game")  # ไม่ใช่ข้อความ toggle

    def test_windows_tips_use_rich_text(self) -> None:
        """tooltip ต้องเป็น HTML ไม่งั้น Qt จะโชว์ <b> เป็นตัวอักษรเปล่าๆ"""
        for pinned in (True, False):
            tip = self._tip("win32", pinned)
            self.assertIn("<b>", tip)
            self.assertIn("<br>", tip)
            self.assertNotIn("\n", tip)  # ใช้ <br> ไม่ใช่ newline

    def test_windows_tips_have_colour_heading(self) -> None:
        """หัวข้อคำแนะนำ/ข้อจำกัดต้องเป็นหนาสีแดง (อ่านออกทั้งธีมสว่างและมืด)"""
        from taskbarnoob.core.models import Group
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import _pin_tooltip

        self.assertIn('<font color="#E5484D">', self._tip("win32", False))

        with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
            main_window, "stale_pin_label", return_value=True
        ):
            stale = _pin_tooltip(Group(name="Game", items=[]), True, "Game")
        self.assertIn('<font color="#E5484D">', stale)
        self.assertIn("<b>", stale)

        # ปักแล้วปกติ (ชื่อตรง) = ไม่ต้องมีหัวข้อเตือน
        self.assertNotIn("#E5484D", self._tip("win32", True))

    def test_windows_tips_drop_emoji(self) -> None:
        """อีโมจิต้องอยู่ในบรรทัดหัวข้อเท่านั้น ไม่ลอยคนละบรรทัด (อ่านทันที)"""
        from taskbarnoob.core.models import Group
        from taskbarnoob.gui import main_window
        from taskbarnoob.gui.main_window import _pin_tooltip

        with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
            main_window, "stale_pin_label", return_value=True
        ):
            tips = [
                self._tip("win32", False),
                _pin_tooltip(Group(name="Game", items=[]), True, "Game"),
            ]
        for tip in tips:
            self.assertLessEqual(tip.count("⚠") + tip.count("💡"), 1)
            start = tip.index("#E5484D")
            head = tip[start : start + 60]  # อีโมจิต้องติดกับหัวข้อสีแดง
            self.assertTrue("⚠" in head or "💡" in head)

    def test_warning_colour_readable_on_both_themes(self) -> None:
        """#E5484D ต้องอ่านออกทั้งพื้นสว่างและพื้นมืด (WCAG AA ขนาดตัวหนา)"""
        def channel(value: int) -> float:
            x = value / 255
            return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4

        r, g, b = (int("#E5484D"[i : i + 2], 16) for i in (1, 3, 5))
        lum = 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

        def ratio(background: tuple[int, int, int]) -> float:
            bg = (
                0.2126 * channel(background[0])
                + 0.7152 * channel(background[1])
                + 0.0722 * channel(background[2])
            )
            hi, lo = max(lum, bg), min(lum, bg)
            return (hi + 0.05) / (lo + 0.05)

        self.assertGreaterEqual(ratio((255, 255, 255)), 3.0)  # พื้นสว่าง
        self.assertGreaterEqual(ratio((43, 43, 43)), 3.0)  # พื้นมืด

    def test_windows_pinned_says_already_on_taskbar(self) -> None:
        self.assertNotEqual(self._tip("win32", True), self._tip("win32", False))

    def test_linux_keeps_toggle_text(self) -> None:
        before, after = self._tip("linux", False), self._tip("linux", True)
        self.assertNotEqual(before, after)
        self.assertNotIn("Game.lnk", before + after)


class DefaultGroupIconTests(unittest.TestCase):
    """ไอคอนสำรองของกลุ่มต้องเป็นไฟล์จริง (`.lnk` รับได้แค่พาธ)."""

    def test_falls_back_to_cached_system_icon(self) -> None:
        from taskbarnoob.core.models import Group
        from taskbarnoob.core.storage import ConfigStore
        from taskbarnoob.gui import icons as gui_icons

        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(tmp)
            icon = gui_icons.group_icon(Group(name="G", items=[]), store, "G")
            self.assertFalse(icon.isNull(), "ไอคอนสำรองห้ามว่าง")

    def test_cache_file_is_reused(self) -> None:
        from taskbarnoob.core.storage import ConfigStore
        from taskbarnoob.gui.icons import default_group_icon_file

        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(tmp)
            first = default_group_icon_file(store)
            if first is None or not first.is_file():
                self.skipTest("ระบบไม่คืนไอคอนโฟลเดอร์")
            stamp = first.stat().st_mtime_ns
            second = default_group_icon_file(store)
            self.assertEqual(first, second)
            self.assertEqual(stamp, second.stat().st_mtime_ns)  # ไม่เขียนซ้ำ


class FolderIconAssetTests(unittest.TestCase):
    def test_folder_svg_shipped(self) -> None:
        """Windows ใช้โฟลเดอร์แทนตา — asset ต้องอยู่ในชุด (มิฉะนั้น fallback ทำงาน)."""
        from taskbarnoob.gui import button_icons

        path = button_icons._assets_dir() / "folder-fill.svg"
        self.assertTrue(path.is_file(), f"ไม่พบ {path}")
        self.assertIn("viewBox", path.read_text(encoding="utf-8"))

    def test_rename_group_migrates_win_hotkey(self) -> None:
        """เปลี่ยนชื่อกลุ่มบน Windows → hotkey ต้องย้ายตามไปชื่อใหม่."""
        from taskbarnoob.core.platform.linux.hotkeys import hotkey_slot
        from taskbarnoob.core.settings import Settings
        from taskbarnoob.gui import win32_hotkey
        from taskbarnoob.gui.main_window import MainWindow

        with tempfile.TemporaryDirectory() as tmp:
            store = ConfigStore(tmp)
            store.save_group(Group(name="Old"))
            settings = Settings(store.config_dir)
            settings.set_hotkey(hotkey_slot("Old"), "<Control><Alt>g")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_hotkey, "register_hotkey"
            ), mock.patch.object(win32_hotkey, "unregister_hotkey"):
                win32_hotkey.registry.register_slot(
                    hotkey_slot("Old"), "Old", "<Control><Alt>g", 1
                )
                window = MainWindow(store=store)
                window._migrate_win_hotkey("Old", "New")
            self.assertNotIn(hotkey_slot("Old"), settings.get_hotkeys())
            self.assertEqual(
                settings.get_hotkeys().get(hotkey_slot("New")), "<Control><Alt>g"
            )
            self.assertEqual(
                win32_hotkey.registry.slots().get(hotkey_slot("New")), "New"
            )


if __name__ == "__main__":
    unittest.main()
