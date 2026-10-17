import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path

from taskbargroups.core.settings import Settings

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except ImportError:
    HAVE_QT = False


class SettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_default_theme_is_auto(self) -> None:
        self.assertEqual(self.settings.get_theme(), "auto")

    def test_set_theme_persists(self) -> None:
        self.settings.set_theme("dark")
        self.assertEqual(self.settings.get_theme(), "dark")
        reloaded = Settings(self._tmp.name)
        self.assertEqual(reloaded.get_theme(), "dark")

    def test_invalid_theme_falls_back_to_auto(self) -> None:
        (Path(self._tmp.name) / "settings.json").write_text(
            '{"theme": "neon"}', encoding="utf-8"
        )
        self.assertEqual(Settings(self._tmp.name).get_theme(), "auto")

    def test_corrupt_json_ignored(self) -> None:
        (Path(self._tmp.name) / "settings.json").write_text(
            "{not-json", encoding="utf-8"
        )
        self.assertEqual(Settings(self._tmp.name).get_theme(), "auto")

    def test_settings_path_is_in_config_dir(self) -> None:
        self.assertEqual(self.settings.path, Path(self._tmp.name) / "settings.json")

    def test_donate_url_default_and_custom(self) -> None:
        from taskbargroups.core.settings import DEFAULT_DONATE_URL

        self.assertEqual(self.settings.get_donate_url(), DEFAULT_DONATE_URL)
        self.settings.set_donate_url("https://example.com/x")
        self.assertEqual(Settings(self._tmp.name).get_donate_url(), "https://example.com/x")

    def test_flyout_labels_off_by_default(self) -> None:
        self.assertFalse(self.settings.get_flyout_labels())

    def test_set_flyout_labels_persists(self) -> None:
        self.settings.set_flyout_labels(True)
        self.assertTrue(self.settings.get_flyout_labels())
        self.assertTrue(Settings(self._tmp.name).get_flyout_labels())

    def test_flyout_labels_bad_value_falls_back(self) -> None:
        (Path(self._tmp.name) / "settings.json").write_text(
            '{"flyout_labels": "yes"}', encoding="utf-8"
        )
        self.assertFalse(Settings(self._tmp.name).get_flyout_labels())


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class ThemeTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_resolve_passthrough(self) -> None:
        from taskbargroups.gui.theme import resolve_theme

        self.assertEqual(resolve_theme("light", self.app), "light")
        self.assertEqual(resolve_theme("dark", self.app), "dark")
        self.assertEqual(resolve_theme("weird", self.app), "light")

    def test_resolve_auto_returns_scheme(self) -> None:
        from taskbargroups.gui.theme import resolve_theme

        self.assertIn(resolve_theme("auto", self.app), ("light", "dark"))

    def test_apply_dark_sets_window_color(self) -> None:
        from PySide6.QtGui import QPalette

        from taskbargroups.gui.theme import apply_theme, resolve_theme

        apply_theme(self.app, resolve_theme("dark", self.app))
        color = self.app.palette().color(QPalette.ColorRole.Window)
        self.assertEqual(color.name(), "#2b2b2b")

    def test_apply_light_resets_to_system(self) -> None:
        from PySide6.QtGui import QPalette

        from taskbargroups.gui.theme import apply_theme

        apply_theme(self.app, "dark")
        apply_theme(self.app, "light")
        standard = self.app.style().standardPalette().color(QPalette.ColorRole.Window)
        self.assertEqual(
            self.app.palette().color(QPalette.ColorRole.Window), standard
        )


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class SettingsDialogTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_theme_change_applies_and_saves(self) -> None:
        import tempfile

        from taskbargroups.gui.settings_dialog import SettingsDialog

        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("TASKBARGROUPS_CONFIG")
            os.environ["TASKBARGROUPS_CONFIG"] = tmp
            try:
                class FakeMain:
                    def on_install_launcher(self) -> None:
                        pass

                    def on_set_hotkey(self) -> None:
                        pass

                dialog = SettingsDialog(FakeMain())
                index = dialog.theme_combo.findData("dark")
                dialog.theme_combo.setCurrentIndex(index)
                saved = Settings(tmp)
                self.assertEqual(saved.get_theme(), "dark")
                dialog.close()
            finally:
                if old is None:
                    os.environ.pop("TASKBARGROUPS_CONFIG", None)
                else:
                    os.environ["TASKBARGROUPS_CONFIG"] = old

    def test_language_change_applies_immediately(self) -> None:
        import tempfile

        from taskbargroups.core import i18n
        from taskbargroups.gui.settings_dialog import SettingsDialog

        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("TASKBARGROUPS_CONFIG")
            os.environ["TASKBARGROUPS_CONFIG"] = tmp
            try:
                i18n.setup("th", tmp)
                dialog = SettingsDialog(object())
                dialog._retranslate()
                th_title = dialog.windowTitle()
                index = dialog.language_combo.findData("en")
                dialog.language_combo.setCurrentIndex(index)
                self.assertEqual(Settings(tmp).get_language(), "en")
                self.assertEqual(i18n._active.language, "en")
                self.assertNotEqual(dialog.windowTitle(), th_title)
                self.assertEqual(dialog.windowTitle(), "Settings")
                dialog.close()
            finally:
                i18n.setup("th", tmp)
                if old is None:
                    os.environ.pop("TASKBARGROUPS_CONFIG", None)
                else:
                    os.environ["TASKBARGROUPS_CONFIG"] = old

    def test_config_button_shows_config_dir(self) -> None:
        import tempfile

        from taskbargroups.gui.settings_dialog import SettingsDialog

        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("TASKBARGROUPS_CONFIG")
            os.environ["TASKBARGROUPS_CONFIG"] = tmp
            try:
                dialog = SettingsDialog(object())
                self.assertEqual(dialog.config_button.text(), str(Settings(tmp).config_dir))
                dialog.close()
            finally:
                if old is None:
                    os.environ.pop("TASKBARGROUPS_CONFIG", None)
                else:
                    os.environ["TASKBARGROUPS_CONFIG"] = old

    def test_backup_buttons_present_and_retranslated(self) -> None:
        import tempfile

        from taskbargroups.core import i18n
        from taskbargroups.gui.settings_dialog import SettingsDialog

        with tempfile.TemporaryDirectory() as tmp:
            old = os.environ.get("TASKBARGROUPS_CONFIG")
            os.environ["TASKBARGROUPS_CONFIG"] = tmp
            try:
                i18n.setup("th", tmp)
                dialog = SettingsDialog(object())
                self.assertEqual(dialog.export_all_button.text(), i18n.tr("settings.export_all"))
                self.assertEqual(dialog.import_all_button.text(), i18n.tr("settings.import_all"))
                self.assertEqual(
                    dialog.delete_backups_button.text(),
                    i18n.tr("settings.delete_backups"),
                )
                i18n.setup("en", tmp)
                dialog._retranslate()
                self.assertEqual(dialog.export_all_button.text(), i18n.tr("settings.export_all"))
                self.assertEqual(dialog.import_all_button.text(), i18n.tr("settings.import_all"))
                self.assertEqual(
                    dialog.delete_backups_button.text(),
                    i18n.tr("settings.delete_backups"),
                )
                dialog.close()
            finally:
                i18n.setup("th", tmp)
                if old is None:
                    os.environ.pop("TASKBARGROUPS_CONFIG", None)
                else:
                    os.environ["TASKBARGROUPS_CONFIG"] = old


class HotkeysDictTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_empty_by_default(self) -> None:
        self.assertEqual(self.settings.get_hotkeys(), {})

    def test_set_remove_roundtrip(self) -> None:
        self.settings.set_hotkey("taskbargroups-game", "<Control><Alt>g")
        self.assertEqual(
            self.settings.get_hotkeys(), {"taskbargroups-game": "<Control><Alt>g"}
        )
        reloaded = Settings(self._tmp.name)
        self.assertEqual(
            reloaded.get_hotkeys(), {"taskbargroups-game": "<Control><Alt>g"}
        )
        reloaded.remove_hotkey("taskbargroups-game")
        self.assertEqual(reloaded.get_hotkeys(), {})

    def test_corrupt_value_ignored(self) -> None:
        (Path(self._tmp.name) / "settings.json").write_text(
            '{"hotkeys": ["nope"]}', encoding="utf-8"
        )
        self.assertEqual(Settings(self._tmp.name).get_hotkeys(), {})


if __name__ == "__main__":
    unittest.main()