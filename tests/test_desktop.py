import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core.desktop import (
    build_desktop_entry,
    build_exec,
    desktop_file_name,
    install_launcher,
    install_launcher_icon,
    launcher_id,
    remove_launcher,
    remove_launcher_icon,
    shortcut_from_path,
)
from taskbargroups.core.models import Group, Shortcut
from taskbargroups.core.paths import app_dir
from taskbargroups.core.storage import ConfigStore


class DesktopTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConfigStore(Path(self._tmp.name) / "config")
        self.data = Path(self._tmp.name) / "apps"
        self.icons = Path(self._tmp.name) / "icons"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_file_name_slug(self) -> None:
        self.assertEqual(desktop_file_name("My Group"), "taskbargroups-my-group.desktop")

    def test_build_exec_quotes_group(self) -> None:
        self.assertIn('--open "My Group"', build_exec("My Group", python="/usr/bin/python3"))

    def test_build_exec_uses_appimage(self) -> None:
        with mock.patch.dict(os.environ, {"APPIMAGE": "/opt/App.AppImage"}):
            self.assertEqual(
                build_exec("Tools"), '"/opt/App.AppImage" --open "Tools"'
            )

    def test_build_exec_center_flag(self) -> None:
        with mock.patch.dict(os.environ, {"APPIMAGE": "/opt/App.AppImage"}):
            self.assertEqual(
                build_exec("Tools", center=True),
                '"/opt/App.AppImage" --open "Tools" --center',
            )
        self.assertTrue(
            build_exec("Tools", python="/usr/bin/python3", center=True).endswith(" --center")
        )

    def test_entry_contains_required_fields(self) -> None:
        group = Group(name="Tools")
        self.store.save_group(group)
        entry = build_desktop_entry(group, self.store, "Tools", python="/usr/bin/python3")
        self.assertIn("[Desktop Entry]", entry)
        self.assertIn("Type=Application", entry)
        self.assertIn("Name=Tools", entry)
        self.assertIn('--open "Tools"', entry)
        self.assertIn("Icon=", entry)
        self.assertIn(f"Path={app_dir()}", entry)

    def test_install_and_remove(self) -> None:
        group = Group(name="Tools", items=[Shortcut(name="a", target="/bin/true")])
        self.store.save_group(group)
        path = install_launcher(
            group,
            self.store,
            "Tools",
            target_dir=self.data,
            python="/usr/bin/python3",
            icons_root=self.icons,
        )
        self.assertTrue(path.is_file())
        self.assertTrue(path.stat().st_mode & 0o100)
        self.assertTrue(
            remove_launcher("Tools", target_dir=self.data, icons_root=self.icons)
        )
        self.assertFalse(
            remove_launcher("Tools", target_dir=self.data, icons_root=self.icons)
        )

    def test_launcher_id_matches_desktop_name(self) -> None:
        self.assertEqual(launcher_id("My Group"), "taskbargroups-my-group")

    def test_install_launcher_icon_svg_uses_scalable(self) -> None:
        source = Path(self._tmp.name) / "icon.svg"
        source.write_text("<svg/>", encoding="utf-8")
        name = install_launcher_icon("Tools", source, icons_root=self.icons)
        self.assertEqual(name, "taskbargroups-tools")
        dest = (
            self.icons / "hicolor" / "scalable" / "apps" / "taskbargroups-tools.svg"
        )
        self.assertTrue(dest.is_file())

    def test_install_launcher_icon_png_uses_256(self) -> None:
        source = Path(self._tmp.name) / "icon.png"
        source.write_bytes(b"png")
        install_launcher_icon("Tools", source, icons_root=self.icons)
        dest = (
            self.icons / "hicolor" / "256x256" / "apps" / "taskbargroups-tools.png"
        )
        self.assertTrue(dest.is_file())
        self.assertTrue(remove_launcher_icon("Tools", icons_root=self.icons))
        self.assertFalse(dest.exists())

    def test_launcher_references_theme_icon_name(self) -> None:
        source = Path(self._tmp.name) / "icon.svg"
        source.write_text("<svg/>", encoding="utf-8")
        group = Group(name="Tools", icon="group_icon.svg")
        self.store.save_group(group)
        self.store.import_group_icon("Tools", str(source))
        path = install_launcher(
            group, self.store, "Tools", target_dir=self.data, icons_root=self.icons
        )
        entry = path.read_text(encoding="utf-8")
        self.assertIn("Icon=taskbargroups-tools", entry)
        self.assertNotIn(str(self.icons), entry)

    def test_no_group_icon_falls_back_to_themed(self) -> None:
        group = Group(name="Tools")
        self.store.save_group(group)
        entry = build_desktop_entry(group, self.store, "Tools")
        self.assertIn("Icon=folder", entry)

    def test_remove_launcher_icon_missing_is_false(self) -> None:
        self.assertFalse(remove_launcher_icon("Tools", icons_root=self.icons))

    def test_shortcut_from_desktop_uses_name(self) -> None:
        desktop = Path(self._tmp.name) / "app.desktop"
        desktop.write_text(
            "[Desktop Entry]\nType=Application\nName=My App\nExec=myapp\n",
            encoding="utf-8",
        )
        shortcut = shortcut_from_path(desktop)
        self.assertIsNotNone(shortcut)
        self.assertEqual(shortcut.name, "My App")
        self.assertEqual(shortcut.target, str(desktop))

    def test_shortcut_from_plain_file_uses_stem(self) -> None:
        target = Path(self._tmp.name) / "tool.bin"
        target.write_bytes(b"x")
        shortcut = shortcut_from_path(target)
        self.assertEqual(shortcut.name, "tool")
        self.assertEqual(shortcut.target, str(target))

    def test_shortcut_from_missing_path_is_none(self) -> None:
        self.assertIsNone(shortcut_from_path(Path(self._tmp.name) / "nope"))

    def test_shortcut_name_is_truncated(self) -> None:
        target = Path(self._tmp.name) / ("x" * 60 + ".bin")
        target.write_bytes(b"x")
        shortcut = shortcut_from_path(target)
        self.assertLessEqual(len(shortcut.name), 27)


if __name__ == "__main__":
    unittest.main()
