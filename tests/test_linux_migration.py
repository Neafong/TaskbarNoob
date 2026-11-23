"""เทสต์ Auto-Migration จาก taskbargroups → taskbarnoob บน Linux Mint (Cinnamon)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from taskbarnoob.core.models import Group
from taskbarnoob.core.platform.linux import migrate
from taskbarnoob.core.storage import ConfigStore


class LinuxMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.store = ConfigStore(self.root / "config")
        self.store.save_group(Group(name="Game"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_migrates_pinned_launcher_in_place_and_is_idempotent(self) -> None:
        apps_dir = self.root / "applications"
        apps_dir.mkdir()
        icons_root = self.root / "icons" / "hicolor"
        old_icon = icons_root / "256x256" / "apps" / "taskbargroups-game.png"
        old_icon.parent.mkdir(parents=True)
        old_icon.write_bytes(b"old-png")
        old_desktop = apps_dir / "taskbargroups-game.desktop"
        old_desktop.write_text("[Desktop Entry]\nName=Game\n", encoding="utf-8")

        panel_dir = self.root / "panel"
        panel_dir.mkdir()
        gwl_cfg = panel_dir / "12.json"
        gwl_cfg.write_text(
            json.dumps(
                {
                    "pinned-apps": {
                        "value": [
                            "firefox.desktop",
                            "taskbargroups-game.desktop",
                            "nemo.desktop",
                        ]
                    }
                }
            ),
            encoding="utf-8",
        )

        calls: list[list[str]] = []

        def fake_runner(cmd):
            calls.append(list(cmd))
            if cmd[:3] == ["gsettings", "get", "org.cinnamon"]:
                return "@as []"
            return ""

        with mock.patch.object(
            migrate._panel, "reload_grouped_window_applet", return_value=True
        ) as reload_mock:
            count = migrate.migrate_pinned_launchers(
                self.store,
                applications_dir=apps_dir,
                icons_root=icons_root,
                panel_config_dir=panel_dir,
                runner=fake_runner,
            )
        self.assertEqual(count, 1)
        data = json.loads(gwl_cfg.read_text(encoding="utf-8"))
        # ตำแหน่งบน taskbar ต้องอยู่ตรงกลางเหมือนเดิม
        self.assertEqual(
            data["pinned-apps"]["value"],
            ["firefox.desktop", "taskbarnoob-game.desktop", "nemo.desktop"],
        )
        self.assertTrue((apps_dir / "taskbarnoob-game.desktop").is_file())
        self.assertFalse(old_desktop.exists())
        self.assertFalse(old_icon.exists())
        reload_mock.assert_called_once()

        # รันซ้ำอีกครั้งต้องเป็น no-op (idempotent)
        count_again = migrate.migrate_pinned_launchers(
            self.store,
            applications_dir=apps_dir,
            icons_root=icons_root,
            panel_config_dir=panel_dir,
            runner=fake_runner,
        )
        self.assertEqual(count_again, 0)

    def test_migrates_cinnamon_hotkey_slot_and_cleans_legacy(self) -> None:
        state = {
            "custom-list": ["taskbargroups-game", "custom0"],
            "bindings": {"taskbargroups-game": "['<Control><Alt>g']"},
        }
        calls: list[list[str]] = []

        def fake_runner(cmd):
            calls.append(list(cmd))
            if cmd[:4] == ["gsettings", "get", "org.cinnamon.desktop.keybindings", "custom-list"]:
                return "[" + ", ".join(f"'{s}'" for s in state["custom-list"]) + "]"
            if cmd[0:2] == ["gsettings", "get"] and cmd[-1] == "binding":
                slot = cmd[2].rstrip("/").split("/")[-1]
                return state["bindings"].get(slot, "[]")
            if cmd[:4] == ["gsettings", "set", "org.cinnamon.desktop.keybindings", "custom-list"]:
                import ast
                state["custom-list"] = list(ast.literal_eval(cmd[4]))
            return ""

        count = migrate.migrate_cinnamon_hotkeys(self.store, runner=fake_runner)
        self.assertEqual(count, 1)
        self.assertIn("taskbarnoob-game", state["custom-list"])
        self.assertNotIn("taskbargroups-game", state["custom-list"])
        self.assertIn("custom0", state["custom-list"])
        # ตรวจว่าตั้ง binding ให้ slot ใหม่ และล้าง binding ของ slot เก่าก่อนถอด
        self.assertTrue(
            any("taskbarnoob-game/" in c[2] and c[3] == "binding" and "<Control><Alt>g" in c[4] for c in calls if len(c) >= 5)
        )
        self.assertTrue(
            any("taskbargroups-game/" in c[2] and c[3] == "binding" and c[4] == "[]" for c in calls if len(c) >= 5)
        )

    def test_migrate_legacy_linux_state_respects_no_pin_env(self) -> None:
        with mock.patch.dict(os.environ, {"TASKBARGROUPS_NO_PIN": "1"}):
            self.assertEqual(migrate.migrate_legacy_linux_state(self.store), (0, 0))
        with mock.patch.dict(os.environ, {"TASKBARNOOB_NO_PIN": "1"}):
            self.assertEqual(migrate.migrate_legacy_linux_state(self.store), (0, 0))


if __name__ == "__main__":
    unittest.main()
