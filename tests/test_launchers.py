"""เทสต์ชั้น dispatch ข้าม OS (mock sys.platform — รันบน Linux ได้)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core import launchers, macos, taskbar, win32
from taskbargroups.core.models import Group


def _group() -> Group:
    return Group(name="Game")


def _store(tmp: str):
    from taskbargroups.core.storage import ConfigStore

    store = ConfigStore(tmp)
    store.save_group(_group())
    return store


class FileNameTests(unittest.TestCase):
    def test_linux_desktop(self) -> None:
        with mock.patch.object(sys, "platform", "linux"):
            self.assertEqual(
                launchers.launcher_file_name("My Game"), "taskbargroups-my-game.desktop"
            )

    def test_windows_lnk(self) -> None:
        with mock.patch.object(sys, "platform", "win32"):
            self.assertEqual(
                launchers.launcher_file_name("My Game"), "taskbargroups-my-game.lnk"
            )

    def test_macos_command(self) -> None:
        with mock.patch.object(sys, "platform", "darwin"):
            self.assertEqual(
                launchers.launcher_file_name("My Game"),
                "taskbargroups-my-game.command",
            )


class InstallRemoveTests(unittest.TestCase):
    def test_windows_install_uses_lnk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = _store(tmp)
            created = {}

            def fake_create(link, target, arguments="", workdir="", icon_location=""):
                created.update(
                    link=str(link), target=str(target), arguments=arguments
                )
                Path(link).parent.mkdir(parents=True, exist_ok=True)
                Path(link).write_bytes(b"lnk")
                return Path(link)

            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "create_lnk", side_effect=fake_create
            ):
                path = launchers.install_launcher(
                    _group(), store, "Game", target_dir=tmp
                )
            self.assertTrue(str(path).endswith(".lnk"))
            self.assertIn('--open "Game"', created["arguments"])
            with mock.patch.object(sys, "platform", "win32"):
                self.assertTrue(launchers.remove_launcher("Game", target_dir=tmp))
                self.assertFalse(launchers.remove_launcher("Game", target_dir=tmp))

    def test_macos_install_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = _store(tmp)
            with mock.patch.object(sys, "platform", "darwin"):
                path = launchers.install_launcher(
                    _group(), store, "Game", target_dir=tmp
                )
            self.assertTrue(str(path).endswith(".command"))
            with mock.patch.object(sys, "platform", "darwin"):
                self.assertTrue(launchers.remove_launcher("Game", target_dir=tmp))


class TaskbarDispatchTests(unittest.TestCase):
    def test_linux_passthrough_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(sys, "platform", "linux"):
                self.assertEqual(taskbar.pinned_desktop_ids(config_dir=tmp), set())

    def test_windows_pin_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            menu = Path(tmp) / "menu"
            pinned = Path(tmp) / "pinned"
            menu.mkdir()
            (menu / "taskbargroups-game.lnk").write_bytes(b"lnk")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "start_menu_dir", return_value=menu
            ), mock.patch.object(win32, "taskbar_pinned_dir", return_value=pinned):
                self.assertEqual(taskbar.pin_to_panel("taskbargroups-game.lnk"), "taskbar-pinned")
                self.assertIn("taskbargroups-game.lnk", taskbar.pinned_desktop_ids())
                self.assertTrue(taskbar.is_pinned("taskbargroups-game.lnk"))
                self.assertTrue(taskbar.unpin_from_panel("taskbargroups-game.lnk"))
                self.assertFalse(taskbar.is_pinned("taskbargroups-game.lnk"))

    def test_windows_pin_missing_source_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            menu = Path(tmp) / "menu"
            menu.mkdir()
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "start_menu_dir", return_value=menu
            ):
                from taskbargroups.core.panel import PinError

                with self.assertRaises(PinError):
                    taskbar.pin_to_panel("taskbargroups-nope.lnk")

    def test_macos_pin_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "taskbargroups-game.command"
            target.write_text("x")
            with mock.patch.object(sys, "platform", "darwin"), mock.patch.object(
                macos, "launchers_dir", return_value=Path(tmp)
            ), mock.patch.object(macos, "pin_to_dock") as pin, mock.patch.object(
                macos, "unpin_from_dock", return_value=True
            ):
                self.assertEqual(taskbar.pin_to_panel(target.name), "dock-pinned")
                pin.assert_called_once()
                self.assertTrue(taskbar.unpin_from_panel(target.name))


if __name__ == "__main__":
    unittest.main()
