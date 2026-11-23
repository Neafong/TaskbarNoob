"""เทสต์ Steam `steam://rungameid/<appid>` icon resolver ข้าม OS (Linux + Windows)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbarnoob.core import icons
from taskbarnoob.core.icons import steam as steam_icons


class SteamAppIdTests(unittest.TestCase):
    def test_extracts_rungameid_and_run(self) -> None:
        self.assertEqual(steam_icons.extract_steam_appid("steam://rungameid/730"), "730")
        self.assertEqual(
            steam_icons.extract_steam_appid("steam steam://rungameid/1245620"),
            "1245620",
        )
        self.assertEqual(steam_icons.extract_steam_appid("STEAM://RUN/570"), "570")

    def test_non_steam_returns_none(self) -> None:
        self.assertIsNone(steam_icons.extract_steam_appid("https://example.com"))
        self.assertIsNone(steam_icons.extract_steam_appid(""))
        self.assertIsNone(steam_icons.extract_steam_appid(None))

    def test_reads_appid_from_desktop_and_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            desktop = root / "cs2.desktop"
            desktop.write_text(
                "[Desktop Entry]\nName=CS2\nExec=steam steam://rungameid/730\n"
                "Icon=steam_icon_730\n",
                encoding="utf-8",
            )
            url = root / "dota2.url"
            url.write_text(
                "[InternetShortcut]\nURL=steam://rungameid/570\n"
                "IconFile=C:\\missing\\570.ico\n",
                encoding="utf-8",
            )
            self.assertEqual(steam_icons.steam_appid_from_file(desktop), "730")
            self.assertEqual(steam_icons.steam_appid_from_file(url), "570")


class SteamLibraryCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self._tmp.name) / "appcache" / "librarycache"
        self.cache.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_finds_legacy_icon(self) -> None:
        icon = self.cache / "730_icon.jpg"
        icon.write_bytes(b"jpg-icon")
        self.assertEqual(
            steam_icons.find_steam_game_icon("730", cache_dirs=[self.cache]),
            icon,
        )

    def test_finds_new_subdir_layout_and_prefers_icon(self) -> None:
        sub = self.cache / "570"
        sub.mkdir()
        header = sub / "header.jpg"
        header.write_bytes(b"x" * 500)
        icon = sub / "abc123_icon.jpg"
        icon.write_bytes(b"x" * 50)
        self.assertEqual(
            steam_icons.find_steam_game_icon("570", cache_dirs=[self.cache]),
            icon,
        )

    def test_resolve_desktop_falls_back_to_steam_cache(self) -> None:
        icon = self.cache / "730_icon.jpg"
        icon.write_bytes(b"jpg-icon")
        desktop = Path(self._tmp.name) / "cs2.desktop"
        desktop.write_text(
            "[Desktop Entry]\nName=CS2\nExec=steam steam://rungameid/730\n"
            "Icon=steam_icon_730_not_in_theme\n",
            encoding="utf-8",
        )
        with mock.patch.object(
            steam_icons, "steam_librarycache_dirs", return_value=[self.cache]
        ):
            self.assertEqual(icons.resolve_icon_source(desktop), icon)

    def test_resolve_url_falls_back_to_steam_cache_when_iconfile_missing(self) -> None:
        icon = self.cache / "570_icon.jpg"
        icon.write_bytes(b"jpg-icon")
        url = Path(self._tmp.name) / "dota2.url"
        url.write_text(
            "[InternetShortcut]\nURL=steam://rungameid/570\n"
            "IconFile=/nonexistent/570.ico\n",
            encoding="utf-8",
        )
        with mock.patch.object(
            steam_icons, "steam_librarycache_dirs", return_value=[self.cache]
        ):
            self.assertEqual(icons.resolve_icon_source(url), icon)

    def test_resolve_raw_steam_uri(self) -> None:
        icon = self.cache / "440_icon.jpg"
        icon.write_bytes(b"tf2")
        with mock.patch.object(
            steam_icons, "steam_librarycache_dirs", return_value=[self.cache]
        ):
            self.assertEqual(icons.resolve_icon_source("steam://rungameid/440"), icon)

    def test_windows_registry_steam_path_lookup(self) -> None:
        steam_root = Path(self._tmp.name)
        with mock.patch.object(steam_icons.sys, "platform", "win32"), mock.patch.object(
            steam_icons, "_read_windows_steam_path", return_value=steam_root
        ):
            dirs = steam_icons.steam_librarycache_dirs()
        self.assertIn(self.cache, dirs)


if __name__ == "__main__":
    unittest.main()
