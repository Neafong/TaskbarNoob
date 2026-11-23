"""เทสต์ชั้น dispatch ข้าม OS (`core.platform` — Linux / Windows, พับเก็บ macOS แล้ว)."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbarnoob.core import platform
from taskbarnoob.core.models import Group
from taskbarnoob.core.platform import PinError, win32
from taskbarnoob.core.platform.win32 import lnk as win32_lnk
from taskbarnoob.core.platform.win32 import pin as win32_pin


def _group() -> Group:
    return Group(name="Game")


def _store(tmp: str):
    from taskbarnoob.core.storage import ConfigStore

    store = ConfigStore(tmp)
    store.save_group(_group())
    return store


class FileNameTests(unittest.TestCase):
    def test_linux_desktop(self) -> None:
        with mock.patch.object(sys, "platform", "linux"):
            self.assertEqual(
                platform.launcher_file_name("My Game"), "taskbarnoob-my-game.desktop"
            )

    def test_windows_lnk(self) -> None:
        with mock.patch.object(sys, "platform", "win32"):
            self.assertEqual(platform.launcher_file_name("My Game"), "My Game.lnk")

    def test_backend_capabilities(self) -> None:
        linux = platform.get_backend("linux")
        self.assertEqual(linux.name, "linux")
        self.assertTrue(linux.supports_direct_pin)
        self.assertTrue(linux.supports_cinnamon_hotkeys)
        self.assertFalse(linux.supports_win_hotkeys)

        win = platform.get_backend("win32")
        self.assertEqual(win.name, "win32")
        self.assertFalse(win.supports_direct_pin)
        self.assertFalse(win.supports_cinnamon_hotkeys)
        self.assertTrue(win.supports_win_hotkeys)


class InstallRemoveTests(unittest.TestCase):
    def test_windows_install_uses_lnk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = _store(tmp)
            created = {}

            def fake_create(
                link, target, arguments="", workdir="", icon_location="", **kw
            ):
                created.update(
                    link=str(link), target=str(target), arguments=arguments, **kw
                )
                Path(link).parent.mkdir(parents=True, exist_ok=True)
                Path(link).write_bytes(b"lnk")
                return Path(link)

            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_lnk, "create_lnk", side_effect=fake_create
            ):
                path = platform.install_launcher(
                    _group(), store, "Game", target_dir=tmp
                )
            self.assertTrue(str(path).endswith(".lnk"))
            self.assertIn('--open "Game"', created["arguments"])
            self.assertEqual(created["aumid_value"], win32.aumid("Game"))
            with mock.patch.object(sys, "platform", "win32"):
                self.assertTrue(platform.remove_launcher("Game", target_dir=tmp))
                self.assertFalse(platform.remove_launcher("Game", target_dir=tmp))


class TaskbarDispatchTests(unittest.TestCase):
    def test_linux_passthrough_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(sys, "platform", "linux"):
                self.assertEqual(platform.pinned_desktop_ids(config_dir=tmp), set())

    def test_windows_pin_reveals_instead_of_copying(self) -> None:
        """Windows 11 ไม่ให้ปักเอง — ต้องเปิด Explorer ให้ผู้ใช้คลิกขวา/ลากวาง."""
        with tempfile.TemporaryDirectory() as tmp:
            shortcuts = Path(tmp) / "shortcuts"
            pinned = Path(tmp) / "pinned"
            shortcuts.mkdir()
            (shortcuts / "Game.lnk").write_bytes(b"lnk")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_lnk, "shortcuts_dir", return_value=shortcuts
            ), mock.patch.object(win32_pin, "taskbar_pinned_dir", return_value=pinned):
                calls: list = []
                result = platform.pin_to_panel("Game.lnk", runner=calls.append)
                self.assertEqual(result, "taskbar-manual")
                self.assertTrue(calls[0].startswith("explorer /select,"))
                self.assertIn('"', calls[0])
                self.assertFalse(pinned.exists())
                self.assertFalse(platform.is_pinned("Game.lnk"))

    def test_windows_pinned_ids_match_aumid(self) -> None:
        """ระบุตัวตนจาก AUMID ไม่ใช่ชื่อไฟล์ — Windows เปลี่ยนชื่อให้ได้เอง."""
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            pinned = Path(tmp) / "pinned"
            pinned.mkdir()
            groups = config / "groups"
            for name in ("Game", "Other"):
                (groups / name).mkdir(parents=True)
                (groups / name / "group.json").write_text(
                    '{"schema_version": 1, "name": "%s", "items": []}' % name,
                    encoding="utf-8",
                )
            (pinned / "Game (2).lnk").write_bytes(b"x")
            (pinned / "someone-else.lnk").write_bytes(b"x")
            values = {
                "Game (2).lnk": win32.aumid("Game"),
                "someone-else.lnk": "some.other.app",
            }
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_pin, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32_pin, "read_lnk_aumid", side_effect=lambda p: values[Path(p).name]
            ):
                self.assertEqual(platform.pinned_desktop_ids(config), {"Game.lnk"})

    def test_windows_unpin_reads_user_pinned_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            shortcuts = config / "shortcuts"
            pinned = Path(tmp) / "pinned"
            shortcuts.mkdir()
            pinned.mkdir()
            groups = config / "groups"
            (groups / "Game").mkdir(parents=True)
            (groups / "Game" / "group.json").write_text(
                '{"schema_version": 1, "name": "Game", "items": []}',
                encoding="utf-8",
            )
            (pinned / "Game.lnk").write_bytes(b"lnk")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_lnk, "shortcuts_dir", return_value=shortcuts
            ), mock.patch.object(
                win32_pin, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32_pin, "read_lnk_aumid", return_value=win32.aumid("Game")
            ):
                self.assertTrue(platform.is_pinned("Game.lnk", config_dir=config))
                self.assertTrue(platform.unpin_from_panel("Game.lnk"))
                self.assertFalse(platform.is_pinned("Game.lnk", config_dir=config))

    def test_windows_detects_stale_taskbar_label(self) -> None:
        """เปลี่ยนชื่อกลุ่มแล้วป้ายบน taskbar แก้ไม่ได้ — ต้องเตือนผู้ใช้."""
        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "pinned"
            pinned.mkdir()
            (pinned / "Test.lnk").write_bytes(b"x")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_pin, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32_pin, "read_lnk_aumid", return_value=win32.aumid("Game")
            ):
                self.assertTrue(platform.stale_pin_label("Game"))

        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "pinned"
            pinned.mkdir()
            (pinned / "Game.lnk").write_bytes(b"x")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_pin, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32_pin, "read_lnk_aumid", return_value=win32.aumid("Game")
            ):
                self.assertFalse(platform.stale_pin_label("Game"))

    def test_windows_pin_missing_source_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shortcuts = Path(tmp) / "shortcuts"
            shortcuts.mkdir()
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_lnk, "shortcuts_dir", return_value=shortcuts
            ):
                with self.assertRaises(PinError):
                    platform.pin_to_panel("Nope.lnk")


if __name__ == "__main__":
    unittest.main()
