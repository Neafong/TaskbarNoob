import os
import sys
import tempfile
import unittest
from pathlib import Path

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
        self._tmp = tempfile.TemporaryDirectory()
        self._old_cfg = os.environ.get("TASKBARGROUPS_CONFIG")
        os.environ["TASKBARGROUPS_CONFIG"] = self._tmp.name
        self.editor = GroupEditor(None, None)
        self.editor.name_edit.setText("Test")

    def tearDown(self) -> None:
        if self._old_cfg is None:
            os.environ.pop("TASKBARGROUPS_CONFIG", None)
        else:
            os.environ["TASKBARGROUPS_CONFIG"] = self._old_cfg
        self._tmp.cleanup()

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

    def test_labels_checkbox_default_off(self) -> None:
        # ค่าเริ่มต้นของแอป = ปิด → checkbox ไม่ติ๊ก
        self.assertFalse(self.editor.labels_check.isChecked())
        self.assertIs(self.editor.result_group().show_labels, False)

    def test_labels_checkbox_override(self) -> None:
        self.editor.labels_check.setChecked(True)
        self.assertIs(self.editor.result_group().show_labels, True)

    def test_labels_checkbox_prefills_group_value(self) -> None:
        from taskbargroups.gui.group_editor import GroupEditor

        editor = GroupEditor(None, None, group=Group(name="G", show_labels=True))
        self.assertTrue(editor.labels_check.isChecked())

    def test_labels_checkbox_prefills_app_default(self) -> None:
        from taskbargroups.core.settings import Settings
        from taskbargroups.gui.group_editor import GroupEditor

        Settings(self._tmp.name).set_flyout_labels(True)
        editor = GroupEditor(None, None)
        self.assertTrue(editor.labels_check.isChecked())


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
@unittest.skipUnless(sys.platform == "linux", "Linux-only")
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


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class WindowsProviderIconTests(unittest.TestCase):
    """ตรรกะดึงไอคอนจาก OS (Windows) — mock provider ให้ deterministic ทุก OS."""

    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _display_dialog(self):
        from unittest import mock

        from taskbargroups.gui import group_editor

        with mock.patch.object(group_editor._SystemIconDialog, "_scan"):
            return group_editor._SystemIconDialog()

    def test_scan_windows_populates_from_start_menu(self) -> None:
        from unittest import mock

        from taskbargroups.gui import group_editor

        menu = os.path.join(self._tmp.name, "menu")
        sub = os.path.join(menu, "sub")
        os.makedirs(sub)
        for name in ("Firefox.lnk", "Editor.lnk"):
            open(os.path.join(menu, name), "w").close()
        open(os.path.join(sub, "Terminal.lnk"), "w").close()
        png = os.path.join(self._tmp.name, "icon.png")
        open(png, "w").close()

        dialog = self._display_dialog()
        with mock.patch.object(
            group_editor, "_windows_shortcut_dirs", return_value=[Path(menu)]
        ), mock.patch.object(
            group_editor, "_cached_provider_png", return_value=Path(png)
        ):
            dialog._scan_windows()
        self.assertEqual(
            sorted(dialog._names), ["Editor", "Firefox", "Terminal"]
        )
        dialog.close()

    def test_scan_windows_filters_noise_shortcuts(self) -> None:
        from unittest import mock

        from taskbargroups.gui import group_editor

        menu = os.path.join(self._tmp.name, "menu")
        os.makedirs(menu)
        for name in (
            "Chrome.lnk",
            "Uninstall Chrome.lnk",
            "Python 3.12 Manuals.lnk",
            "App Readme.lnk",
            "Affinity.lnk",
        ):
            open(os.path.join(menu, name), "w").close()
        png = os.path.join(self._tmp.name, "icon.png")
        open(png, "w").close()

        dialog = self._display_dialog()
        with mock.patch.object(
            group_editor, "_windows_shortcut_dirs", return_value=[Path(menu)]
        ), mock.patch.object(
            group_editor, "_cached_provider_png", return_value=Path(png)
        ):
            dialog._scan_windows()
        self.assertEqual(sorted(dialog._names), ["Affinity", "Chrome"])
        dialog.close()

    def test_windows_dll_source_extracts_png_on_accept(self) -> None:
        from unittest import mock

        from PySide6.QtGui import QIcon, QPixmap

        from taskbargroups.gui import group_editor

        fake_dll = Path(self._tmp.name) / "imageres.dll"
        fake_dll.write_bytes(b"")
        out_png = Path(self._tmp.name) / "imageres_3.png"
        out_png.write_bytes(b"png")

        with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
            group_editor, "_windows_system_icon_dlls", return_value=[fake_dll]
        ), mock.patch.object(
            group_editor, "list_dll_icons", return_value=[(3, QIcon(QPixmap(16, 16)))]
        ), mock.patch.object(
            group_editor, "extract_dll_icon_png", return_value=out_png
        ) as extract_fn:
            dialog = group_editor._SystemIconDialog(cache_dir=Path(self._tmp.name))
            self.assertIsNotNone(dialog.source_combo)
            self.assertEqual(dialog.source_combo.currentData(), "system")
            self.assertEqual(dialog.grid.count(), 1)
            dialog.grid.setCurrentRow(0)
            dialog.accept()
        self.assertEqual(dialog.selected_path(), str(out_png))
        extract_fn.assert_called_once()
        dialog.close()

    def test_windows_shortcut_dirs_uses_env(self) -> None:
        from unittest import mock

        from taskbargroups.gui import group_editor

        root = os.path.join(self._tmp.name, "appdata")
        menu = os.path.join(root, "Microsoft", "Windows", "Start Menu", "Programs")
        os.makedirs(menu)
        with mock.patch.dict(
            os.environ, {"APPDATA": root}, clear=False
        ), mock.patch.dict(os.environ, {"ProgramData": ""}, clear=False):
            dirs = group_editor._windows_shortcut_dirs()
        self.assertIn(Path(menu), dirs)

    def test_iter_windows_shortcuts_dedups_by_name(self) -> None:
        from taskbargroups.gui import group_editor

        a = os.path.join(self._tmp.name, "a")
        b = os.path.join(self._tmp.name, "b")
        os.makedirs(a)
        os.makedirs(b)
        open(os.path.join(a, "Game.lnk"), "w").close()
        open(os.path.join(b, "Game.lnk"), "w").close()
        open(os.path.join(a, "Tool.lnk"), "w").close()
        found = list(group_editor._iter_windows_shortcuts([Path(a), Path(b)]))
        self.assertEqual([p.name for p in found].count("Game.lnk"), 1)
        self.assertEqual(len(found), 2)

    def test_cached_provider_png_reuses_fresh_cache(self) -> None:
        from unittest import mock

        from taskbargroups.gui import group_editor

        source = Path(self._tmp.name) / "app.exe"
        source.write_bytes(b"x")
        base = Path(self._tmp.name) / "cache"
        calls: list[tuple] = []

        def fake_png(src, dest, size=256):
            calls.append((src, dest))
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"png")
            return dest

        with mock.patch.object(group_editor, "_provider_png", side_effect=fake_png):
            first = group_editor._cached_provider_png(source, base)
            second = group_editor._cached_provider_png(source, base)
        self.assertEqual(first, second)
        self.assertEqual(len(calls), 1)

    def test_auto_icon_uses_provider_for_exe(self) -> None:
        from unittest import mock

        from taskbargroups.gui import group_editor

        target = Path(self._tmp.name) / "app.exe"
        target.write_bytes(b"x")
        png = Path(self._tmp.name) / "icon.png"
        png.write_bytes(b"png")

        dialog = group_editor.ShortcutDialog()
        dialog.target_edit.setText(str(target))
        with mock.patch.object(
            group_editor.core_icons, "resolve_icon_source", return_value=None
        ), mock.patch.object(
            group_editor, "_cached_provider_png", return_value=png
        ) as provider, mock.patch.object(
            group_editor, "show_information"
        ) as info:
            dialog._auto_icon()
        provider.assert_called_once()
        info.assert_not_called()
        self.assertEqual(dialog.icon_source(), str(png))
        dialog.close()

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_extract_os_icon_png_real_exe_is_high_res(self) -> None:
        """shell API ต้องได้ความละเอียดสูง (>=128px) — QFileIconProvider เดิมได้แค่ 128 แล้ว."""
        from PySide6.QtGui import QImage

        from taskbargroups.gui.icons import extract_os_icon_png

        dest = Path(self._tmp.name) / "icon.png"
        result = extract_os_icon_png(Path(sys.executable), dest)
        self.assertIsNotNone(result)
        image = QImage(str(dest))
        self.assertFalse(image.isNull())
        self.assertGreaterEqual(image.width(), 128)

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_extract_from_lnk_resolves_target_no_overlay(self) -> None:
        """.lnk ต้อง resolve ไปดึงจาก target — ได้ภาพเดียวกับดึงจาก exe ตรงๆ
        (ไม่มี overlay ลูกศร shortcut ปนมา)."""
        from PySide6.QtGui import QImage

        from taskbargroups.core import win32_com
        from taskbargroups.gui.icons import extract_os_icon_png

        with tempfile.TemporaryDirectory() as tmp:
            lnk = Path(tmp) / "Py.lnk"
            win32_com.write_lnk(lnk, sys.executable)
            p_lnk = extract_os_icon_png(lnk, Path(self._tmp.name) / "a.png")
            p_exe = extract_os_icon_png(
                Path(sys.executable), Path(self._tmp.name) / "b.png"
            )
            self.assertIsNotNone(p_lnk)
            self.assertIsNotNone(p_exe)
            self.assertEqual(QImage(str(p_lnk)), QImage(str(p_exe)))

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_extract_missing_returns_none(self) -> None:
        from taskbargroups.gui.icons import extract_os_icon_png

        result = extract_os_icon_png(
            Path(self._tmp.name) / "ghost.exe", Path(self._tmp.name) / "x.png"
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()