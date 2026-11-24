"""เทสต์ .url Resilience (parse_url_file, แตก URL=, แคชไอคอน .url→.exe, Linux URI launch)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from taskbarnoob.core.icons import parse_url_file
from taskbarnoob.core.launcher import _launch_linux, is_uri_target
from taskbarnoob.core.platform.linux.desktop import shortcut_from_path


class ParseUrlFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_parses_epic_url_with_exe_icon(self) -> None:
        exe = self.root / "RCG2.exe"
        exe.write_bytes(b"MZ")
        url_file = self.root / "River City Girls 2.url"
        url_file.write_text(
            "[InternetShortcut]\n"
            "URL=com.epicgames.launcher://apps/abc?action=launch\n"
            f"IconFile={exe}\n"
            "IconIndex=0\n",
            encoding="utf-8",
        )
        url, icon = parse_url_file(url_file)
        self.assertEqual(url, "com.epicgames.launcher://apps/abc?action=launch")
        self.assertEqual(icon, exe)

    def test_parses_steam_url_without_icon(self) -> None:
        url_file = self.root / "River City Melee.url"
        url_file.write_text(
            "[InternetShortcut]\n"
            "URL=steam://rungameid/544630\n",
            encoding="utf-8",
        )
        url, icon = parse_url_file(url_file)
        self.assertEqual(url, "steam://rungameid/544630")
        self.assertIsNone(icon)

    def test_missing_file_returns_none_tuple(self) -> None:
        self.assertEqual(parse_url_file(self.root / "nope.url"), (None, None))

    def test_shortcut_from_url_extracts_target_directly(self) -> None:
        url_file = self.root / "My Game.url"
        url_file.write_text(
            "[InternetShortcut]\nURL=steam://rungameid/544630\n",
            encoding="utf-8",
        )
        sc = shortcut_from_path(url_file)
        self.assertIsNotNone(sc)
        self.assertEqual(sc.name, "My Game")
        self.assertEqual(sc.target, "steam://rungameid/544630")

    def test_shortcut_from_url_without_url_key_falls_back_to_path(self) -> None:
        url_file = self.root / "Broken.url"
        url_file.write_text("[InternetShortcut]\nIconIndex=0\n", encoding="utf-8")
        sc = shortcut_from_path(url_file)
        self.assertIsNotNone(sc)
        self.assertEqual(sc.target, str(url_file))


class LinuxUriLaunchTests(unittest.TestCase):
    def test_is_uri_target(self) -> None:
        self.assertTrue(is_uri_target("steam://rungameid/544630"))
        self.assertTrue(is_uri_target("com.epicgames.launcher://apps/abc"))
        self.assertTrue(is_uri_target("https://example.com"))
        self.assertFalse(is_uri_target("C:\\Games\\game.exe"))
        self.assertFalse(is_uri_target("/usr/bin/firefox"))
        self.assertFalse(is_uri_target("firefox"))

    def test_launch_linux_uses_gio_open_for_uri(self) -> None:
        with patch("taskbarnoob.core.launcher.subprocess.Popen") as popen:
            _launch_linux("steam://rungameid/544630", [], None)
            popen.assert_called_once()
            cmd = popen.call_args[0][0]
            self.assertEqual(cmd, ["gio", "open", "steam://rungameid/544630"])

    def test_launch_linux_falls_back_to_xdg_open_for_uri(self) -> None:
        calls = []

        def fake_popen(cmd, **_kwargs):
            calls.append(cmd)
            if cmd[0] == "gio":
                raise FileNotFoundError("no gio")

        with patch("taskbarnoob.core.launcher.subprocess.Popen", side_effect=fake_popen):
            _launch_linux("https://example.com", [], None)
        self.assertEqual(
            calls,
            [
                ["gio", "open", "https://example.com"],
                ["xdg-open", "https://example.com"],
            ],
        )


try:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QImage
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class UrlDropResilienceTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_dropped_url_survives_deleting_original_url_file(self) -> None:
        from taskbarnoob.core.models import Group
        from taskbarnoob.core.storage import ConfigStore
        from taskbarnoob.gui.group_editor import GroupEditor
        from taskbarnoob.gui.main_window import MainWindow

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            icon_png = root / "game.png"
            img = QImage(32, 32, QImage.Format_ARGB32)
            img.fill(0xFF00AAFF)
            img.save(str(icon_png), "PNG")

            url_file = root / "Cool Game.url"
            url_file.write_text(
                "[InternetShortcut]\n"
                "URL=com.epicgames.launcher://apps/cool\n"
                f"IconFile={icon_png}\n",
                encoding="utf-8",
            )

            store = ConfigStore(root / "cfg")
            editor = GroupEditor(store)
            editor._on_urls_dropped([QUrl.fromLocalFile(str(url_file))])

            # ลบไฟล์ .url ต้นฉบับทิ้งก่อนบันทึก
            url_file.unlink()
            self.assertEqual(len(editor._group.items), 1)
            sc = editor._group.items[0]
            self.assertEqual(sc.target, "com.epicgames.launcher://apps/cool")
            self.assertIn(id(sc), editor.pending_icons())

            # แคชลงกลุ่ม → ต้องได้ไฟล์ใน icons/ แม้ .url หายไปแล้ว
            group = Group(name="Games", items=[sc])
            store.save_group(group)
            win = MainWindow(store)
            win._cache_shortcut_icons(group, "Games", editor.pending_icons())
            self.assertTrue(sc.icon and sc.icon.startswith("icons/"))
            cached = store.resolve_relative("Games", sc.icon)
            self.assertIsNotNone(cached)
            self.assertTrue(cached.is_file())
            win.close()
            editor.close()


if __name__ == "__main__":
    unittest.main()
