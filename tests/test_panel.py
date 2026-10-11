import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbargroups.core import panel
from taskbargroups.core.panel import (
    PinError,
    add_grouped_window_pin,
    add_panel_launcher,
    pin_to_panel,
    read_panel_launchers,
)


class PanelLauncherTests(unittest.TestCase):
    def test_read_panel_launchers(self) -> None:
        def runner(command):
            self.assertEqual(command[1], "get")
            return "@as ['a.desktop', 'b.desktop']"

        self.assertEqual(read_panel_launchers(runner), ["a.desktop", "b.desktop"])

    def test_add_panel_launcher_appends_and_strips_deprecated(self) -> None:
        calls: list[list[str]] = []

        def runner(command):
            calls.append(list(command))
            if command[1] == "get":
                return "['DEPRECATED', 'keep.desktop']"
            return ""

        add_panel_launcher("new.desktop", runner)
        set_call = calls[-1]
        self.assertEqual(set_call[1], "set")
        payload = set_call[-1]
        self.assertIn("new.desktop", payload)
        self.assertIn("keep.desktop", payload)
        self.assertNotIn("DEPRECATED", payload)

    def test_add_panel_launcher_skips_when_present(self) -> None:
        calls: list[list[str]] = []

        def runner(command):
            calls.append(list(command))
            return "['have.desktop']"

        add_panel_launcher("have.desktop", runner)
        self.assertEqual(len(calls), 1)


class GroupedWindowPinTests(unittest.TestCase):
    def test_appends_to_existing_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            path = cfg / "1.json"
            path.write_text(
                json.dumps(
                    {"pinned-apps": {"value": ["existing.desktop"], "type": "as"}}
                ),
                encoding="utf-8",
            )
            self.assertTrue(add_grouped_window_pin("new.desktop", cfg))
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("new.desktop", data["pinned-apps"]["value"])
            self.assertIn("existing.desktop", data["pinned-apps"]["value"])

    def test_missing_dir_returns_false(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(add_grouped_window_pin("x", Path(tmp) / "nope"))

    def test_ignores_config_without_pinned_apps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            (cfg / "1.json").write_text(json.dumps({"other": 1}), encoding="utf-8")
            self.assertFalse(add_grouped_window_pin("x", cfg))


class PinToPanelTests(unittest.TestCase):
    def test_non_cinnamon_raises(self) -> None:
        with mock.patch.object(panel, "is_cinnamon", return_value=False):
            with self.assertRaises(PinError):
                pin_to_panel("x.desktop", config_dir=Path("/nonexistent"))

    def test_disabled_by_env(self) -> None:
        with mock.patch.object(panel, "is_cinnamon", return_value=True):
            with mock.patch.dict("os.environ", {"TASKBARGROUPS_NO_PIN": "1"}):
                with self.assertRaises(PinError):
                    pin_to_panel("x.desktop", config_dir=Path("/nonexistent"))

    def test_uses_grouped_window_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            (cfg / "1.json").write_text(
                json.dumps({"pinned-apps": {"value": [], "type": "as"}}),
                encoding="utf-8",
            )
            with mock.patch.object(panel, "is_cinnamon", return_value=True):
                self.assertEqual(
                    pin_to_panel("g.desktop", config_dir=cfg, refresh=False),
                    "grouped-window-list",
                )

    def test_pin_refreshes_applet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            (cfg / "1.json").write_text(
                json.dumps({"pinned-apps": {"value": [], "type": "as"}}),
                encoding="utf-8",
            )
            with mock.patch.object(panel, "is_cinnamon", return_value=True):
                with mock.patch.object(panel, "reload_grouped_window_applet") as reload:
                    pin_to_panel("g.desktop", config_dir=cfg)
            reload.assert_called_once()

    def test_already_pinned_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            path = cfg / "1.json"
            path.write_text(
                json.dumps({"pinned-apps": {"value": ["g.desktop"], "type": "as"}}),
                encoding="utf-8",
            )
            with mock.patch.object(panel, "is_cinnamon", return_value=True):
                self.assertTrue(add_grouped_window_pin("g.desktop", cfg))
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["pinned-apps"]["value"], ["g.desktop"])


class ReloadTests(unittest.TestCase):
    def test_reload_missing_gdbus_returns_false(self) -> None:
        with mock.patch.object(panel.shutil, "which", return_value=None):
            self.assertFalse(panel.reload_grouped_window_applet())

    def test_reload_runs_gdbus_reloadxlet(self) -> None:
        calls: list[list[str]] = []

        def runner(command, *args, **kwargs):
            calls.append(list(command))
            return mock.Mock(returncode=0)

        with mock.patch.object(panel.shutil, "which", return_value="/usr/bin/gdbus"):
            with mock.patch.object(panel.subprocess, "run", side_effect=runner) as run:
                self.assertTrue(panel.reload_grouped_window_applet())
        self.assertTrue(run.called)
        command = calls[0]
        self.assertIn("org.Cinnamon.ReloadXlet", command)
        self.assertIn("grouped-window-list@cinnamon.org", command)
        self.assertIn("APPLET", command)


class ConfigDirTests(unittest.TestCase):
    def test_dirs_prefer_xdg_config_home(self) -> None:
        with mock.patch.dict("os.environ", {"XDG_CONFIG_HOME": "/tmp/xdgtest"}):
            dirs = panel.grouped_window_config_dirs()
        self.assertEqual(dirs[0], Path("/tmp/xdgtest/cinnamon/spices/grouped-window-list@cinnamon.org"))
        self.assertEqual(dirs[1], Path.home() / ".cinnamon" / "configs" / "grouped-window-list@cinnamon.org")


class PinnedStateTests(unittest.TestCase):
    def _write(self, cfg: Path, values: list[str]) -> Path:
        path = cfg / "2.json"
        path.write_text(
            json.dumps({"pinned-apps": {"value": list(values), "type": "as"}}),
            encoding="utf-8",
        )
        return path

    def test_grouped_window_pinned_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            self._write(cfg, ["a.desktop", "b.desktop"])
            self.assertEqual(
                panel.grouped_window_pinned_ids(cfg), {"a.desktop", "b.desktop"}
            )

    def test_remove_grouped_window_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            path = self._write(cfg, ["a.desktop", "b.desktop"])
            self.assertTrue(panel.remove_grouped_window_pin("a.desktop", cfg))
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["pinned-apps"]["value"], ["b.desktop"])
            self.assertFalse(panel.remove_grouped_window_pin("zzz.desktop", cfg))

    def test_is_pinned_reads_grouped_window(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            self._write(cfg, ["g.desktop"])
            with mock.patch.object(panel, "is_cinnamon", return_value=False):
                self.assertTrue(panel.is_pinned("g.desktop", cfg))
                self.assertFalse(panel.is_pinned("x.desktop", cfg))

    def test_unpin_from_panel_removes_and_reloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cfg = Path(tmp)
            path = self._write(cfg, ["g.desktop"])
            with mock.patch.object(panel, "is_cinnamon", return_value=True):
                with mock.patch.object(panel, "reload_grouped_window_applet") as reload:
                    self.assertTrue(panel.unpin_from_panel("g.desktop", config_dir=cfg))
            reload.assert_called_once()
            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8"))["pinned-apps"]["value"], []
            )

    def test_unpin_non_cinnamon_raises(self) -> None:
        with mock.patch.object(panel, "is_cinnamon", return_value=False):
            with self.assertRaises(PinError):
                panel.unpin_from_panel("g.desktop", config_dir=Path("/nonexistent"))


if __name__ == "__main__":
    unittest.main()
