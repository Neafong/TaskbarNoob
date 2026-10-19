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
            # ชื่อไฟล์ = ชื่อกลุ่ม เพราะ Windows เอาไปแสดงบน taskbar/Start
            self.assertEqual(launchers.launcher_file_name("My Game"), "My Game.lnk")

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
                win32, "create_lnk", side_effect=fake_create
            ):
                path = launchers.install_launcher(
                    _group(), store, "Game", target_dir=tmp
                )
            self.assertTrue(str(path).endswith(".lnk"))
            self.assertIn('--open "Game"', created["arguments"])
            # AUMID เฉพาะกลุ่ม — ไม่งั้นปุ่มบน taskbar จะซ้อนกัน
            self.assertEqual(created["aumid_value"], win32.aumid("Game"))
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

    def test_windows_pin_reveals_instead_of_copying(self) -> None:
        """Windows 11 ไม่ให้ปักเอง — ต้องเปิด Explorer ให้ผู้ใช้คลิกขวา/ลากวาง."""
        with tempfile.TemporaryDirectory() as tmp:
            shortcuts = Path(tmp) / "shortcuts"
            pinned = Path(tmp) / "pinned"
            shortcuts.mkdir()
            (shortcuts / "Game.lnk").write_bytes(b"lnk")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "shortcuts_dir", return_value=shortcuts
            ), mock.patch.object(win32, "taskbar_pinned_dir", return_value=pinned):
                calls: list = []
                result = taskbar.pin_to_panel("Game.lnk", runner=calls.append)
                self.assertEqual(result, "taskbar-manual")
                self.assertTrue(calls[0].startswith("explorer /select,"))
                self.assertIn('"', calls[0])  # quote path ที่มีช่องว่าง
                self.assertFalse(pinned.exists())  # ไม่ก๊อปไฟล์ปลอม
                self.assertFalse(taskbar.is_pinned("Game.lnk"))

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
            # Windows เติม " (2)" เมื่อชนกับ .lnk ของแอปอื่น
            (pinned / "Game (2).lnk").write_bytes(b"x")
            (pinned / "someone-else.lnk").write_bytes(b"x")
            values = {
                "Game (2).lnk": win32.aumid("Game"),
                "someone-else.lnk": "some.other.app",
            }
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32, "read_lnk_aumid", side_effect=lambda p: values[Path(p).name]
            ):
                self.assertEqual(taskbar.pinned_desktop_ids(config), {"Game.lnk"})

    def test_windows_unpin_reads_user_pinned_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp)
            shortcuts = config / "shortcuts"
            pinned = Path(tmp) / "pinned"
            shortcuts.mkdir()
            pinned.mkdir()
            (groups := config / "groups")
            (groups / "Game").mkdir(parents=True)
            (groups / "Game" / "group.json").write_text(
                '{"schema_version": 1, "name": "Game", "items": []}',
                encoding="utf-8",
            )
            (pinned / "Game.lnk").write_bytes(b"lnk")
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "shortcuts_dir", return_value=shortcuts
            ), mock.patch.object(win32, "taskbar_pinned_dir", return_value=pinned), mock.patch.object(
                win32, "read_lnk_aumid", return_value=win32.aumid("Game")
            ):
                self.assertTrue(taskbar.is_pinned("Game.lnk", config_dir=config))
                self.assertTrue(taskbar.unpin_from_panel("Game.lnk"))
                self.assertFalse(taskbar.is_pinned("Game.lnk", config_dir=config))

    def test_windows_detects_stale_taskbar_label(self) -> None:
        """เปลี่ยนชื่อกลุ่มแล้วป้ายบน taskbar แก้ไม่ได้ — ต้องเตือนผู้ใช้"""
        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "pinned"
            pinned.mkdir()
            (pinned / "Test.lnk").write_bytes(b"x")  # ชื่อไฟล์เก่า (จากตอนลากวาง)
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32, "read_lnk_aumid", return_value=win32.aumid("Game")
            ):
                self.assertTrue(taskbar.stale_pin_label("Game"))  # ชื่อไม่ตรง

        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "pinned"
            pinned.mkdir()
            (pinned / "Game.lnk").write_bytes(b"x")  # ชื่อตรงแล้ว
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32, "read_lnk_aumid", return_value=win32.aumid("Game")
            ):
                self.assertFalse(taskbar.stale_pin_label("Game"))

    def test_windows_pin_missing_source_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            shortcuts = Path(tmp) / "shortcuts"
            shortcuts.mkdir()
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32, "shortcuts_dir", return_value=shortcuts
            ):
                from taskbargroups.core.panel import PinError

                with self.assertRaises(PinError):
                    taskbar.pin_to_panel("Nope.lnk")

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
