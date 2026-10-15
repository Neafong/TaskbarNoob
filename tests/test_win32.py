"""เทสต์ backend Windows (รันบน Linux ได้ — ทุกอย่างรับ runner/env/home จำลอง)."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core import win32


class LnkNameTests(unittest.TestCase):
    def test_slug(self) -> None:
        self.assertEqual(win32.lnk_name("My Game"), "taskbargroups-my-game.lnk")
        self.assertEqual(win32.launcher_id("My Game"), "taskbargroups-my-game")


class DirTests(unittest.TestCase):
    def test_appdata_env_wins(self) -> None:
        env = {"APPDATA": r"C:\Users\Noob\AppData\Roaming"}
        menu = win32.start_menu_dir(env=env)
        self.assertTrue(str(menu).startswith(r"C:\Users\Noob"))
        self.assertTrue(str(menu).endswith("TaskbarNoob"))
        pinned = win32.taskbar_pinned_dir(env=env)
        self.assertIn("User Pinned", str(pinned))

    def test_appdata_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            menu = win32.start_menu_dir(env={}, home=tmp)
            self.assertEqual(
                menu,
                Path(tmp) / "AppData" / "Roaming" / "Microsoft" / "Windows"
                / "Start Menu" / "Programs" / "TaskbarNoob",
            )


class PsScriptTests(unittest.TestCase):
    def test_create_quotes_and_escapes(self) -> None:
        script = win32.build_lnk_ps_script(
            "C:\\a\\b's.lnk", "C:\\app\\app.exe", "--open \"G\"",
            workdir="C:\\app", icon_location="C:\\app\\i.ico",
        )
        self.assertIn("b''s.lnk", script)  # ' หนีเป็น ''
        self.assertIn("$sc.TargetPath", script)
        self.assertIn("$sc.WorkingDirectory", script)
        self.assertIn("$sc.IconLocation", script)
        self.assertIn("$sc.Save()", script)
        command = win32.lnk_command(script)
        self.assertEqual(command[:3], ["powershell", "-NoProfile", "-NonInteractive"])

    def test_read_script(self) -> None:
        self.assertIn("TargetPath", win32.build_read_lnk_ps_script("x.lnk"))


class LnkActionTests(unittest.TestCase):
    def test_create_calls_runner_and_makes_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "sub" / "g.lnk"
            calls: list = []
            win32.create_lnk(link, "C:\\app.exe", runner=calls.append)
            self.assertTrue(link.parent.is_dir())
            self.assertTrue(calls)
            self.assertIn("powershell", calls[0][0])

    def test_read_target_strips(self) -> None:
        self.assertEqual(
            win32.read_lnk_target("x", runner=lambda _c: "C:\\app.exe\r\n"),
            "C:\\app.exe",
        )
        self.assertIsNone(win32.read_lnk_target("x", runner=lambda _c: "  \n"))
        def boom(_c):
            raise win32.WindowsError("nope")

        self.assertIsNone(win32.read_lnk_target("x", runner=boom))


class PinTests(unittest.TestCase):
    def test_pin_unpin_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"APPDATA": tmp}
            src = Path(tmp) / "taskbargroups-game.lnk"
            src.write_bytes(b"lnk")
            dest = win32.pin_to_taskbar(src, env=env)
            self.assertTrue(dest.is_file())
            self.assertTrue(win32.is_pinned("Game", env=env))
            self.assertTrue(win32.unpin_from_taskbar("Game", env=env))
            self.assertFalse(win32.is_pinned("Game", env=env))
            self.assertFalse(win32.unpin_from_taskbar("Game", env=env))


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
