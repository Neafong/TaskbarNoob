import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core import icons
from taskbargroups.core.storage import ConfigStore


class SafeStemTests(unittest.TestCase):
    def test_replaces_unsafe(self) -> None:
        self.assertEqual(icons.safe_stem("My App!"), "My_App")

    def test_blank_falls_back(self) -> None:
        self.assertEqual(icons.safe_stem("   "), "icon")


class ThemeIconTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.theme = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_finds_direct_icon(self) -> None:
        target = self.theme / "firefox.png"
        target.write_bytes(b"png")
        self.assertEqual(icons.find_theme_icon("firefox", [self.theme]), target)

    def test_finds_nested_icon(self) -> None:
        nested = self.theme / "hicolor" / "48x48" / "apps"
        nested.mkdir(parents=True)
        target = nested / "editor.svg"
        target.write_text("<svg/>")
        self.assertEqual(icons.find_theme_icon("editor", [self.theme]), target)

    def test_missing_returns_none(self) -> None:
        self.assertIsNone(icons.find_theme_icon("nope", [self.theme]))


class DesktopFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_desktop(self, icon_value: str) -> Path:
        desktop = self.root / "app.desktop"
        desktop.write_text(
            "[Desktop Entry]\nType=Application\nName=App\n"
            f"Icon={icon_value}\nExec=app\n",
            encoding="utf-8",
        )
        return desktop

    def test_absolute_icon(self) -> None:
        image = self.root / "logo.png"
        image.write_bytes(b"png")
        self.assertEqual(icons.icon_from_desktop_file(self._write_desktop(str(image))), image)

    def test_unknown_icon_returns_none(self) -> None:
        self.assertIsNone(
            icons.icon_from_desktop_file(self._write_desktop("definitely-missing-icon-xyz"))
        )


class ResolveTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_image_returns_itself(self) -> None:
        image = self.root / "pic.png"
        image.write_bytes(b"png")
        self.assertEqual(icons.resolve_icon_source(str(image)), image)

    def test_executable_returns_none(self) -> None:
        self.assertIsNone(icons.resolve_icon_source("/usr/bin/definitely-not-an-image"))

    def test_none_returns_none(self) -> None:
        self.assertIsNone(icons.resolve_icon_source(None))


class AppImageTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _fake_appimage(self, name: str = "App.AppImage") -> Path:
        path = self.root / name
        path.write_bytes(
            b"\x7fELF\x02\x01\x01\x00" + icons._APPIMAGE_TYPE2_MAGIC + b"\x00" * 8
        )
        return path

    def test_detects_type2_magic(self) -> None:
        self.assertTrue(icons.is_appimage(self._fake_appimage()))

    def test_detects_by_suffix(self) -> None:
        plain = self.root / "thing.AppImage"
        plain.write_bytes(b"not really")
        self.assertTrue(icons.is_appimage(plain))

    def test_plain_elf_is_not_appimage(self) -> None:
        elf = self.root / "tool.x86_64"
        elf.write_bytes(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 8)
        self.assertFalse(icons.is_appimage(elf))

    def test_plain_text_is_not_appimage(self) -> None:
        text = self.root / "notes.txt"
        text.write_text("hi")
        self.assertFalse(icons.is_appimage(text))

    def test_resolve_extracts_embedded_icon(self) -> None:
        appimage = self._fake_appimage()
        cache = self.root / "cache"

        def fake_run(cmd, cwd=None, **kwargs):
            squash = Path(cwd) / "squashfs-root"
            icon_dir = (
                squash / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
            )
            icon_dir.mkdir(parents=True, exist_ok=True)
            (icon_dir / "app.png").write_bytes(b"real-icon")
            (squash / "App.desktop").write_text(
                "[Desktop Entry]\nName=App\nIcon=app\nExec=app\n",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(cmd, 0)

        patches = (
            mock.patch.object(icons, "_appimage_cache_dir", return_value=cache),
            mock.patch.object(icons.subprocess, "run", side_effect=fake_run),
        )
        with patches[0], patches[1]:
            result = icons.resolve_icon_source(str(appimage))
        self.assertIsNotNone(result)
        self.assertEqual(result.read_bytes(), b"real-icon")

    def test_extract_returns_none_when_extract_fails(self) -> None:
        appimage = self._fake_appimage()
        with mock.patch.object(icons.subprocess, "run", side_effect=OSError("no exec")):
            self.assertIsNone(icons.icon_from_appimage(appimage))

    def test_clean_env_strips_appimage_vars(self) -> None:
        with mock.patch.dict(
            icons.os.environ,
            {"APPDIR": "/x", "LD_LIBRARY_PATH": "/y", "KEEP_ME": "1"},
        ):
            env = icons._clean_appimage_env()
        self.assertNotIn("APPDIR", env)
        self.assertNotIn("LD_LIBRARY_PATH", env)
        self.assertEqual(env.get("KEEP_ME"), "1")


class CacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConfigStore(Path(self._tmp.name) / "config")
        self.icons_dir = self.store.icons_dir("Grp")
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_cache_copies_file(self) -> None:
        src = self.root / "logo.png"
        src.write_bytes(b"png-data")
        name = icons.cache_icon(src, self.icons_dir, "My Icon")
        self.assertEqual(name, "My_Icon.png")
        self.assertEqual((self.icons_dir / name).read_bytes(), b"png-data")

    def test_cache_replaces_same_stem(self) -> None:
        first = self.root / "a.png"
        first.write_bytes(b"a")
        icons.cache_icon(first, self.icons_dir, "dupe")
        second = self.root / "b.ico"
        second.write_bytes(b"b")
        icons.cache_icon(second, self.icons_dir, "dupe")
        remaining = sorted(p.name for p in self.icons_dir.iterdir())
        self.assertEqual(remaining, ["dupe.ico"])

    def test_cache_shortcut_with_source(self) -> None:
        src = self.root / "logo.png"
        src.write_bytes(b"png")
        result = icons.cache_shortcut_icon(self.icons_dir, "/usr/bin/app", "App", source=src)
        self.assertEqual(result, "icons/App.png")

    def test_cache_shortcut_without_source(self) -> None:
        self.assertIsNone(
            icons.cache_shortcut_icon(self.icons_dir, "/usr/bin/app", "App")
        )

    def test_cache_missing_raises(self) -> None:
        with self.assertRaises(icons.IconError):
            icons.cache_icon(self.root / "nope.png", self.icons_dir, "x")


if __name__ == "__main__":
    unittest.main()
