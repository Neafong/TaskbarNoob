"""เทสต์ backend Windows.

- ส่วนใหญ่รันได้ทุก OS (pure function / mock runner)
- `ComLnkTests` ต้องรันบน Windows จริง (COM ไม่มีบน Linux)
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core import win32


class LnkNameTests(unittest.TestCase):
    def test_name_is_group_name(self) -> None:
        # Windows เอาชื่อไฟล์ .lnk ไปแสดงบน taskbar → ต้องเป็นชื่อกลุ่ม
        self.assertEqual(win32.lnk_name("My Game"), "My Game.lnk")
        self.assertEqual(win32.launcher_id("My Game"), "My Game")

    def test_aumid_is_per_group(self) -> None:
        self.assertEqual(win32.aumid("Game"), "taskbargroups.group.game")
        self.assertNotEqual(win32.aumid("Game"), win32.aumid("Production"))


class ShortcutsDirTests(unittest.TestCase):
    def test_lives_under_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(
                win32.shortcuts_dir(tmp), Path(tmp) / "shortcuts"
            )


class DirTests(unittest.TestCase):
    def test_appdata_env_wins(self) -> None:
        env = {"APPDATA": r"C:\Users\Noob\AppData\Roaming"}
        menu = win32.start_menu_dir(env=env)
        self.assertTrue(str(menu).startswith(r"C:\Users\Noob"))
        self.assertTrue(str(menu).endswith("Programs"))
        pinned = win32.taskbar_pinned_dir(env=env)
        self.assertIn("User Pinned", str(pinned))

    def test_appdata_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            menu = win32.start_menu_dir(env={}, home=tmp)
            self.assertEqual(
                menu,
                Path(tmp) / "AppData" / "Roaming" / "Microsoft" / "Windows"
                / "Start Menu" / "Programs",
            )


class LnkActionTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_create_makes_parent_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "sub" / "Game.lnk"  # โฟลเดอร์แม่ยังไม่มี
            win32.create_lnk(
                link, r"C:\app\TaskbarNoob.exe", aumid_value=win32.aumid("Game")
            )
            self.assertTrue(link.is_file())

    def test_read_target_missing_file_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(win32.read_lnk_target(Path(tmp) / "nope.lnk"))

    def test_read_aumid_missing_file_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(win32.read_lnk_aumid(Path(tmp) / "nope.lnk"))


class SetProcessAumidTests(unittest.TestCase):
    def test_noop_on_non_windows(self) -> None:
        with mock.patch.object(sys, "platform", "linux"):
            win32.set_process_aumid("Game")  # ต้องไม่พัง

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_calls_shell32(self) -> None:
        import ctypes

        with mock.patch.object(
            ctypes.windll.shell32,
            "SetCurrentProcessExplicitAppUserModelID",
            create=True,
        ) as fn:
            win32.set_process_aumid("Game")
            fn.assert_called_once_with(win32.aumid("Game"))


class PinTests(unittest.TestCase):
    def test_pin_opens_explorer_with_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "Game.lnk"
            src.write_bytes(b"lnk")
            calls: list = []
            result = win32.pin_to_taskbar(src, runner=calls.append)
            self.assertEqual(result, src)
            # string เดี่ยว + quote ไว้ ไม่งั้น path ที่มีช่องว่างพัดไปเปิดโฟลเดอร์อื่น
            self.assertIsInstance(calls[0], str)
            self.assertTrue(calls[0].startswith("explorer /select,"))
            self.assertIn('"', calls[0])

    def test_run_accepts_plain_string(self) -> None:
        """_run ต้องไม่แตก string เป็นรายตัวอักษร."""
        with mock.patch.object(win32.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="ok", stderr="")
            win32._run('explorer /select,"C:\\a b\\c.lnk"')
            (args, _kwargs) = run.call_args
            self.assertEqual(args[0], 'explorer /select,"C:\\a b\\c.lnk"')

    def test_run_accepts_list(self) -> None:
        with mock.patch.object(win32.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="ok", stderr="")
            win32._run(["powershell", "-Command", "x"])
            (args, _kwargs) = run.call_args
            self.assertEqual(args[0], ["powershell", "-Command", "x"])

    def test_pin_does_not_fake_pinned_file(self) -> None:
        """ไม่ก๊อปไฟล์ปลอมลง User Pinned — Win11 ไม่อ่านและจะทำให้ UI โกหก."""
        with tempfile.TemporaryDirectory() as tmp:
            env = {"APPDATA": tmp}
            src = Path(tmp) / "Game.lnk"
            src.write_bytes(b"lnk")
            win32.pin_to_taskbar(src, env=env, runner=lambda _c: "")
            self.assertFalse(win32.is_pinned("Game", env=env))
            self.assertEqual(list(win32.taskbar_pinned_dir(env=env).glob("*.lnk")), [])

    def test_unpin_removes_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"APPDATA": tmp}
            dest = win32.taskbar_pinned_dir(env=env) / "Game.lnk"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"lnk")
            self.assertTrue(win32.is_pinned("Game", env=env))
            self.assertTrue(win32.unpin_from_taskbar("Game", env=env))
            self.assertFalse(win32.is_pinned("Game", env=env))
            self.assertFalse(win32.unpin_from_taskbar("Game", env=env))


class RepointPinnedTests(unittest.TestCase):
    """หลังเปลี่ยนชื่อกลุ่ม ปุ่มบน taskbar ต้องตามไปด้วย (ไม่งั้นกดแล้วเปิดกลุ่มที่ไม่มี)"""

    def test_writes_over_pin_that_has_old_aumid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "TaskBar"
            pinned.mkdir()
            stale = pinned / "555.lnk"
            stale.write_bytes(b"old")
            new_lnk = Path(tmp) / "Game.lnk"
            new_lnk.write_bytes(b"new")

            def fake_aumid(path):
                return win32.aumid("555") if Path(path) == stale else None

            with mock.patch.object(
                win32, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32, "read_lnk_aumid", side_effect=fake_aumid
            ):
                self.assertTrue(win32.repoint_pinned("555", new_lnk))
            self.assertEqual(stale.read_bytes(), b"new")

    def test_leaves_other_apps_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "TaskBar"
            pinned.mkdir()
            theirs = pinned / "Browser.lnk"
            theirs.write_bytes(b"theirs")
            new_lnk = Path(tmp) / "Game.lnk"
            new_lnk.write_bytes(b"new")
            with mock.patch.object(
                win32, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(
                win32, "read_lnk_aumid", return_value="tjackenpacken.taskbarGroup.menu.Browser"
            ):
                self.assertFalse(win32.repoint_pinned("555", new_lnk))
            self.assertEqual(theirs.read_bytes(), b"theirs")  # ไม่แตะของคนอื่น

    def test_no_pin_yet_is_not_an_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pinned = Path(tmp) / "TaskBar"
            pinned.mkdir()
            new_lnk = Path(tmp) / "Game.lnk"
            new_lnk.write_bytes(b"new")
            with mock.patch.object(
                win32, "taskbar_pinned_dir", return_value=pinned
            ), mock.patch.object(win32, "read_lnk_aumid", return_value=None):
                self.assertFalse(win32.repoint_pinned("555", new_lnk))


class PngToIcoTests(unittest.TestCase):
    def test_script_uses_system_drawing(self) -> None:
        script = win32.build_png_to_ico_ps_script("C:\\a\\b.png", "C:\\a\\b.ico")
        self.assertIn("System.Drawing", script)
        self.assertIn("$icon.Save($fs)", script)
        self.assertIn("b.png", script)
        self.assertIn("b.ico", script)

    def test_converts_when_runner_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            png.write_bytes(b"png")

            def fake(_cmd):
                png.with_suffix(".ico").write_bytes(b"ico")
                return ""

            ico = win32.png_to_ico(png, runner=fake)
            self.assertIsNotNone(ico)
            self.assertEqual(ico.name, "g.ico")

    def test_returns_none_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            png.write_bytes(b"png")

            def boom(_cmd):
                raise win32.WindowsError("no powershell")

            self.assertIsNone(win32.png_to_ico(png, runner=boom))

    def test_skips_non_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ico = Path(tmp) / "g.ico"
            ico.write_bytes(b"ico")
            self.assertIsNone(win32.png_to_ico(ico, runner=lambda _c: ""))


class ComLnkTests(unittest.TestCase):
    """เทสต์ COM จริง — รันได้เฉพาะ Windows (บน Linux ไม่มี COM)."""

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_roundtrip_keeps_target_and_aumid(self) -> None:
        from taskbargroups.core import win32_com

        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "Game.lnk"
            win32_com.write_lnk(
                link,
                r"C:\app\TaskbarNoob.exe",
                arguments='--open "Game"',
                workdir=r"C:\app",
                description="Game",
                aumid=win32.aumid("Game"),
            )
            self.assertTrue(link.is_file())
            self.assertEqual(win32.read_lnk_target(link), r"C:\app\TaskbarNoob.exe")
            self.assertEqual(win32.read_lnk_aumid(link), win32.aumid("Game"))

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_write_without_aumid_is_allowed(self) -> None:
        from taskbargroups.core import win32_com

        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "Plain.lnk"
            win32_com.write_lnk(link, r"C:\app\x.exe")
            self.assertTrue(link.is_file())
            self.assertIsNone(win32.read_lnk_aumid(link))

    def test_guids_are_wellformed(self) -> None:
        """กัน GUID พิมพ์ผิด (เคยพังเพราะขาดเลขฐาน 16 ไป 1 ตัว)."""
        import uuid

        from taskbargroups.core import win32_com

        for value in (
            win32_com.CLSID_SHELL_LINK,
            win32_com.IID_SHELL_LINK_W,
            win32_com.IID_PERSIST_FILE,
            win32_com.IID_PROPERTY_STORE,
            win32_com._PKEY_AUMID_FMTID,
        ):
            uuid.UUID(value)  # จะ raise ถ้าผิดรูป

    def test_write_outside_windows_raises(self) -> None:
        from taskbargroups.core import win32_com

        with mock.patch.object(sys, "platform", "linux"), self.assertRaises(
            win32_com.ComError
        ):
            win32_com.write_lnk(Path("/tmp/x.lnk"), "/tmp/x.exe")


class HotkeyParseTests(unittest.TestCase):
    def test_modifiers_and_letter(self) -> None:
        mods, vk = win32.parse_hotkey_binding("<Control><Alt>t")
        self.assertEqual(mods, win32.MOD_CONTROL | win32.MOD_ALT)
        self.assertEqual(vk, ord("T"))

    def test_shift_super_digit(self) -> None:
        mods, vk = win32.parse_hotkey_binding("<Shift><Super>5")
        self.assertEqual(mods, win32.MOD_SHIFT | win32.MOD_WIN)
        self.assertEqual(vk, ord("5"))

    def test_invalid_raises(self) -> None:
        with self.assertRaises(win32.WindowsError):
            win32.parse_hotkey_binding("<Control><Alt>F5")
        with self.assertRaises(win32.WindowsError):
            win32.parse_hotkey_binding("")

    def test_register_outside_windows_raises(self) -> None:
        with self.assertRaises(win32.WindowsError):
            win32.register_hotkey(1, 0, 0, ord("A"))


class RegistryTests(unittest.TestCase):
    def test_register_unregister_find(self) -> None:
        from taskbargroups.gui import win32_hotkey

        registry = win32_hotkey.HotkeyRegistry()
        with mock.patch.object(
            win32_hotkey, "register_hotkey"
        ) as reg, mock.patch.object(win32_hotkey, "unregister_hotkey") as unreg:
            registry.register_slot("taskbargroups-game", "Game", "<Control><Alt>g", 1234)
            reg.assert_called_once()
            args = reg.call_args[0]
            self.assertEqual(args[1], 1234)  # hwnd
            self.assertEqual(registry.find_dir(args[0]), "Game")
            self.assertTrue(registry.unregister_slot("taskbargroups-game", 1234))
            unreg.assert_called_once()
            self.assertIsNone(registry.find_dir(args[0]))
            self.assertFalse(registry.unregister_slot("taskbargroups-game", 1234))

    def test_invalid_binding_raises_before_register(self) -> None:
        from taskbargroups.gui import win32_hotkey

        registry = win32_hotkey.HotkeyRegistry()
        with mock.patch.object(win32_hotkey, "register_hotkey") as reg:
            with self.assertRaises(OSError):
                registry.register_slot("s", "G", "<Control>F5", 0)
            reg.assert_not_called()


if __name__ == "__main__":
    unittest.main()
