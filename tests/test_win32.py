"""เทสต์ backend Windows.

- ส่วนใหญ่รันได้ทุก OS (pure function / mock runner)
- `ComLnkTests` ต้องรันบน Windows จริง (COM ไม่มีบน Linux)
"""

import os
import struct
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

    def test_app_aumid_differs_from_group_and_calls_shell32(self) -> None:
        self.assertNotEqual(win32.app_aumid(), win32.aumid("app"))
        fake = mock.MagicMock()
        with mock.patch.object(sys, "platform", "win32"), mock.patch.dict(
            sys.modules, {"ctypes": fake}
        ):
            win32.set_app_aumid()
            fn = fake.windll.shell32.SetCurrentProcessExplicitAppUserModelID
            fn.assert_called_once_with(win32.app_aumid())


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
    """เทสต์ png_to_ico แบบ pure Python (PNG-in-ICO, lossless)."""

    @staticmethod
    def _fake_png(width: int = 64, height: int = 64) -> bytes:
        """สร้าง bytes ที่มี PNG signature + IHDR header พอให้ png_to_ico อ่านขนาดได้."""
        sig = b"\x89PNG\r\n\x1a\n"
        # IHDR: length=13, type="IHDR", width, height, bit_depth=8, color_type=2 (truecolor)
        ihdr = (
            struct.pack(">I", 13)
            + b"IHDR"
            + struct.pack(">II", width, height)
            + bytes([8, 2, 0, 0, 0])
        )
        # CRC ปลอม (png_to_ico ไม่ได้ validate CRC)
        crc = b"\x00\x00\x00\x00"
        return sig + ihdr + crc

    def test_script_uses_system_drawing(self) -> None:
        script = win32.build_png_to_ico_ps_script("C:\\a\\b.png", "C:\\a\\b.ico")
        self.assertIn("System.Drawing", script)
        self.assertIn("$icon.Save($fs)", script)
        self.assertIn("b.png", script)
        self.assertIn("b.ico", script)

    def test_converts_png_in_ico(self) -> None:
        """PNG-in-ICO: header ถูก + PNG bytes ถูกฝังตรงๆ (lossless)."""
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            png_data = self._fake_png(128, 128)
            png.write_bytes(png_data)

            ico = win32.png_to_ico(png)
            self.assertIsNotNone(ico)
            self.assertEqual(ico.name, "g.ico")

            raw = ico.read_bytes()
            # ICONDIR: reserved=0, type=1 (icon), count=1
            self.assertEqual(raw[:6], struct.pack("<HHH", 0, 1, 1))
            # ICONDIRENTRY: width/height byte = 0 (PNG-in-ICO convention — Windows อ่านจาก PNG header)
            self.assertEqual(raw[6], 0)
            self.assertEqual(raw[7], 0)
            offset = struct.unpack("<I", raw[18:22])[0]
            self.assertEqual(offset, 22)
            # PNG bytes ถูกฝังตรงๆ (lossless — ไม่ผ่าน System.Drawing)
            self.assertEqual(raw[22:], png_data)

    def test_size_any_writes_zero(self) -> None:
        """ขนาดใดก็ตาม → เขียน 0 ใน ICONDIRENTRY (0 = อ่านจาก PNG header ตาม convention)."""
        for size in (64, 128, 256, 512):
            with tempfile.TemporaryDirectory() as tmp:
                png = Path(tmp) / "g.png"
                png.write_bytes(self._fake_png(size, size))
                ico = win32.png_to_ico(png)
                self.assertIsNotNone(ico, f"size={size}")
                raw = ico.read_bytes()
                self.assertEqual(raw[6], 0, f"size={size}")
                self.assertEqual(raw[7], 0, f"size={size}")

    def test_returns_none_on_invalid_png(self) -> None:
        """ไม่ใช่ PNG จริง → None."""
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            png.write_bytes(b"not a png at all")
            self.assertIsNone(win32.png_to_ico(png))

    def test_returns_none_on_too_short(self) -> None:
        """PNG สั้นเกินไป (ไม่มี IHDR) → None."""
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            png.write_bytes(b"\x89PNG\r\n\x1a\n")  # เหลือแค่ signature
            self.assertIsNone(win32.png_to_ico(png))

    def test_skips_non_png(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ico = Path(tmp) / "g.ico"
            ico.write_bytes(b"ico")
            self.assertIsNone(win32.png_to_ico(ico))

    def test_reuses_existing_ico(self) -> None:
        """มี .ico ใหม่กว่า .png แล้ว = ไม่เขียนซ้ำ."""
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            ico = Path(tmp) / "g.ico"
            png.write_bytes(self._fake_png())
            ico.write_bytes(b"existing")
            os.utime(ico, (png.stat().st_atime + 10, png.stat().st_mtime + 10))

            self.assertEqual(win32.png_to_ico(png), ico)
            self.assertEqual(ico.read_bytes(), b"existing")

    def test_converts_when_ico_is_stale(self) -> None:
        """มี .ico เก่ากว่า .png = ต้องแปลงใหม่."""
        with tempfile.TemporaryDirectory() as tmp:
            png = Path(tmp) / "g.png"
            ico = Path(tmp) / "g.ico"
            png.write_bytes(self._fake_png())
            ico.write_bytes(b"old")
            os.utime(png, (ico.stat().st_atime + 10, ico.stat().st_mtime + 10))

            result = win32.png_to_ico(png)
            self.assertEqual(result, ico)
            # ไฟล์ใหม่ต้องเป็น PNG-in-ICO ไม่ใช่ b"old"
            self.assertNotEqual(ico.read_bytes(), b"old")
            self.assertEqual(ico.read_bytes()[:6], struct.pack("<HHH", 0, 1, 1))

    def test_resize_rgba_area_premultiplied_no_dark_fringe(self) -> None:
        """ย่อขอบวงกลมสีขาวบนพื้นโปร่งใส (0,0,0,0) ต้องไม่ติดขอบดำ และมี alpha ไล่ระดับเนียน."""
        src_w = src_h = 64
        pixels = bytearray(src_w * src_h * 4)
        for y in range(src_h):
            for x in range(src_w):
                dx = x - 31.5
                dy = y - 31.5
                if dx * dx + dy * dy <= 28.0 * 28.0:
                    idx = (y * src_w + x) * 4
                    pixels[idx : idx + 4] = bytes((255, 255, 255, 255))
        out = win32._resize_rgba(pixels, src_w, src_h, 16, 16)
        edge_pixels = []
        for i in range(0, len(out), 4):
            r, g, b, a = out[i], out[i + 1], out[i + 2], out[i + 3]
            if 0 < a < 255:
                edge_pixels.append((r, g, b, a))
                # Premultiplied alpha: ขอบต้องยังคงเป็นสีขาวบริสุทธิ์ ไม่มีขอบดำปน
                self.assertEqual((r, g, b), (255, 255, 255))
        self.assertGreater(len(edge_pixels), 10)


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

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_read_icon_location_roundtrip(self) -> None:
        """IconLocation ต้องอ่านกลับได้ — ใช้ resolve ไอคอนจริงของ .lnk."""
        from taskbargroups.core import win32_com

        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "Game.lnk"
            win32_com.write_lnk(
                link,
                r"C:\app\TaskbarNoob.exe",
                icon_location=r"C:\app\custom.ico",
            )
            self.assertEqual(
                win32_com.read_icon_location(link), (r"C:\app\custom.ico", 0)
            )

    @unittest.skipUnless(sys.platform == "win32", "ต้องรันบน Windows")
    def test_read_icon_location_empty_is_none(self) -> None:
        from taskbargroups.core import win32_com

        with tempfile.TemporaryDirectory() as tmp:
            link = Path(tmp) / "Plain.lnk"
            win32_com.write_lnk(link, r"C:\app\x.exe")
            self.assertIsNone(win32_com.read_icon_location(link))
            self.assertIsNone(win32_com.read_icon_location(Path(tmp) / "nope.lnk"))

    def test_guids_are_wellformed(self) -> None:
        """กัน GUID พิมพ์ผิด (เคยพังเพราะขาดเลขฐาน 16 ไป 1 ตัว)."""
        import uuid

        from taskbargroups.core import win32_com

        for value in (
            win32_com.CLSID_SHELL_LINK,
            win32_com.IID_SHELL_LINK_W,
            win32_com.IID_PERSIST_FILE,
            win32_com.IID_PROPERTY_STORE,
            win32_com.IID_SHELL_ITEM_IMAGE_FACTORY,
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
        with mock.patch.object(sys, "platform", "linux"), self.assertRaises(
            win32.WindowsError
        ):
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

    def test_filter_spawns_center_flyout_on_wm_hotkey(self) -> None:
        import ctypes
        from taskbargroups.gui import win32_hotkey

        registry = win32_hotkey.HotkeyRegistry()
        with mock.patch.object(win32_hotkey, "register_hotkey"):
            registry.register_slot("taskbargroups-game", "Game", "<Control><Alt>g", 100)
        msg = win32_hotkey._MSG(
            hwnd=100,
            message=win32_hotkey.WM_HOTKEY,
            wParam=1,
            lParam=0,
            time=0,
            x=0,
            y=0,
        )
        filt = win32_hotkey.WinHotkeyFilter(registry, ["TaskbarNoob.exe"])
        with mock.patch.object(win32_hotkey.subprocess, "Popen") as popen:
            handled, result = filt.nativeEventFilter(
                b"windows_generic_MSG", ctypes.addressof(msg)
            )
        self.assertTrue(handled)
        self.assertEqual(result, 0)
        popen.assert_called_once_with(
            ["TaskbarNoob.exe", "--open", "Game", "--center"],
            start_new_session=True,
        )


class AppExecLinkTests(unittest.TestCase):
    """เทสต์แกะ reparse point ของแอป MSIX/WindowsApps และการสกัดไอคอน."""

    def _build_reparse(self, *strings: str, tag: int = 0x8000001B) -> bytes:
        body = struct.pack("<I", 3) + "".join(s + "\x00" for s in strings).encode(
            "utf-16-le"
        )
        return struct.pack("<IHH", tag, len(body), 0) + body

    def test_parse_valid_app_exec_link(self) -> None:
        from taskbargroups.core import win32_com

        buf = self._build_reparse(
            "Canva.Affinity_8a0j1tnjnt4a4",
            "Canva.Affinity_8a0j1tnjnt4a4!App",
            r"C:\Program Files\WindowsApps\Canva.Affinity\Affinity.exe",
        )
        self.assertEqual(
            win32_com.parse_app_exec_link_reparse(buf),
            (
                "Canva.Affinity_8a0j1tnjnt4a4!App",
                r"C:\Program Files\WindowsApps\Canva.Affinity\Affinity.exe",
            ),
        )

    def test_parse_rejects_wrong_tag_or_short_data(self) -> None:
        from taskbargroups.core import win32_com

        self.assertIsNone(win32_com.parse_app_exec_link_reparse(b"short"))
        bad_tag = self._build_reparse("pkg", "pkg!App", tag=0xA000000C)
        self.assertIsNone(win32_com.parse_app_exec_link_reparse(bad_tag))

    def test_shell_icon_uses_appsfolder_for_msix_alias(self) -> None:
        from taskbargroups.core import win32_com
        from taskbargroups.gui import icons as gui_icons

        with tempfile.TemporaryDirectory() as tmp:
            fake_alias = Path(tmp) / "Affinity.exe"
            fake_alias.write_bytes(b"")
            dest = Path(tmp) / "out.png"
            with mock.patch.object(sys, "platform", "win32"), mock.patch.object(
                win32_com,
                "read_app_exec_link",
                return_value=("Canva.Affinity_8a0j1tnjnt4a4!App", ""),
            ), mock.patch.object(
                gui_icons, "_appsfolder_icon_png", return_value=dest
            ) as apps_fn:
                result = gui_icons.extract_os_icon_png(fake_alias, dest, 256)
            self.assertEqual(result, dest)
            apps_fn.assert_called_once_with(
                "Canva.Affinity_8a0j1tnjnt4a4!App", dest, 256
            )


if __name__ == "__main__":
    unittest.main()
