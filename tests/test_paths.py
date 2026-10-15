import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core import paths


class AppDirTests(unittest.TestCase):
    def test_appimage_env_uses_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            appimage = Path(tmp) / "TaskbarGroups-x86_64.AppImage"
            with mock.patch.dict(os.environ, {"APPIMAGE": str(appimage)}):
                self.assertEqual(paths.app_dir(), Path(tmp))

    def test_source_tree_without_env(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            expected = Path(paths.__file__).resolve().parents[2]
            self.assertEqual(paths.app_dir(), expected)


class DefaultConfigDirTests(unittest.TestCase):
    def test_env_override_wins(self) -> None:
        with mock.patch.dict(os.environ, {"TASKBARGROUPS_CONFIG": "/custom/cfg"}, clear=True):
            self.assertEqual(paths.default_config_dir(), Path("/custom/cfg"))

    def test_portable_next_to_appimage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            appimage = Path(tmp) / "App.AppImage"
            with mock.patch.dict(os.environ, {"APPIMAGE": str(appimage)}, clear=True):
                self.assertEqual(paths.default_config_dir(), Path(tmp) / "config")

    def test_fallback_when_not_writable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "not-a-dir"
            blocker.write_text("file")
            env = {"APPIMAGE": str(blocker / "App.AppImage"), "XDG_CONFIG_HOME": str(Path(tmp) / "xdg")}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(
                    paths.default_config_dir(), Path(tmp) / "xdg" / "taskbargroups"
                )


class AppIconPathTests(unittest.TestCase):
    def test_source_tree_icon_exists(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            icon = paths.app_icon_path()
        self.assertIsNotNone(icon)
        self.assertTrue(icon.is_file())
        self.assertEqual(icon.name, "taskbargroups.png")

    def test_bundled_meipass_icon_preferred(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bundled = Path(tmp) / "taskbargroups" / "assets" / "taskbargroups.png"
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b"png")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                paths.sys, "_MEIPASS", tmp, create=True
            ):
                self.assertEqual(paths.app_icon_path(), bundled)

    def test_bundled_internal_layout_pyinstaller6(self) -> None:
        # PyInstaller 6 (onedir) วาง data ใต้ _internal/ — ต้องหาเจอเหมือนกัน
        with tempfile.TemporaryDirectory() as tmp:
            bundled = (
                Path(tmp) / "_internal" / "taskbargroups" / "assets" / "taskbargroups.png"
            )
            bundled.parent.mkdir(parents=True)
            bundled.write_bytes(b"png")
            with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
                paths.sys, "_MEIPASS", tmp, create=True
            ):
                self.assertEqual(paths.app_icon_path(), bundled)
                self.assertEqual(
                    paths.bundled_assets_dir(), bundled.parent
                )


if __name__ == "__main__":
    unittest.main()
