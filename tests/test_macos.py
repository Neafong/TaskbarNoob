"""เทสต์ backend macOS (รันบน Linux ได้ — runner จำลอง)."""

import plistlib
import tempfile
import unittest
from pathlib import Path

from taskbargroups.core import macos


class NameTests(unittest.TestCase):
    def test_names(self) -> None:
        self.assertEqual(macos.command_name("My Game"), "taskbargroups-my-game.command")
        self.assertEqual(macos.launcher_id("My Game"), "taskbargroups-my-game")


class CommandLauncherTests(unittest.TestCase):
    def test_install_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = macos.install_command_launcher("/Applications/X.app", "Game", tmp)
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertIn('--open "Game"', text)
            import os

            self.assertTrue(os.access(path, os.X_OK))
            self.assertTrue(macos.remove_command_launcher("Game", tmp))
            self.assertFalse(macos.remove_command_launcher("Game", tmp))


class DockTests(unittest.TestCase):
    def _runner(self, calls: list, apps: list):
        def run(command):
            calls.append(list(command))
            if command[:3] == ["defaults", "read", "com.apple.dock"]:
                return plistlib.dumps(apps).decode("utf-8")
            return ""

        return run

    def test_pin_unpin_roundtrip(self) -> None:
        calls: list = []
        macos.pin_to_dock("/Applications/Foo.app", runner=self._runner(calls, []))
        writes = [c for c in calls if c[:2] == ["defaults", "write"]]
        self.assertTrue(writes)
        self.assertIn("killall", calls[-1])
        self.assertTrue(any("Foo.app" in " ".join(c) for c in writes))

    def test_unpin_missing_returns_false(self) -> None:
        self.assertFalse(
            macos.unpin_from_dock("/Applications/Foo.app", runner=self._runner([], []))
        )

    def test_read_error_gives_empty(self) -> None:
        def boom(_c):
            raise macos.MacOSError("nope")

        self.assertEqual(macos.read_dock_apps(runner=boom), [])

    def test_dock_app_paths(self) -> None:
        apps = [
            {"tile-data": {"file-data": {"_CFURLString": "file:///Applications/Foo.app"}}},
            {"nope": True},
        ]
        paths = macos.dock_app_paths(runner=self._runner([], apps))
        self.assertIn("file:///Applications/Foo.app", paths)


if __name__ == "__main__":
    unittest.main()
