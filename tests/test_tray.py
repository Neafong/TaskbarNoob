"""เทสต์ System Tray Icon (minimize_to_tray) ใน MainWindow และ SettingsDialog."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtGui import QCloseEvent
    from PySide6.QtWidgets import QApplication, QSystemTrayIcon

    HAVE_QT = True
except ImportError:
    HAVE_QT = False


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class SystemTrayTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self._old_cfg = os.environ.get("TASKBARNOOB_CONFIG")
        os.environ["TASKBARNOOB_CONFIG"] = self._tmp.name

    def tearDown(self) -> None:
        if self._old_cfg is None:
            os.environ.pop("TASKBARNOOB_CONFIG", None)
        else:
            os.environ["TASKBARNOOB_CONFIG"] = self._old_cfg
        self._tmp.cleanup()
        if self.app is not None:
            self.app.setQuitOnLastWindowClosed(True)

    def _make_window(self):
        from taskbarnoob.core.storage import ConfigStore
        from taskbarnoob.gui.main_window import MainWindow

        store = ConfigStore(self._tmp.name)
        return MainWindow(store)

    def test_tray_disabled_by_default_closes_normally(self) -> None:
        win = self._make_window()
        win.show()
        self.assertIsNone(win._tray)
        event = QCloseEvent()
        win.closeEvent(event)
        self.assertTrue(event.isAccepted())

    def test_tray_enabled_hides_on_close_and_has_menu_actions(self) -> None:
        from taskbarnoob.core import i18n
        from taskbarnoob.core.settings import Settings

        i18n.setup("th", self._tmp.name)
        Settings(self._tmp.name).set_minimize_to_tray(True)
        with patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
            win = self._make_window()
            # offscreen platform อาจคืน isVisible()=False สำหรับ native tray → mock ไว้
            win._tray.isVisible = MagicMock(return_value=True)
            win.show()
            self.assertFalse(self.app.quitOnLastWindowClosed())
            self.assertEqual(
                set(win._tray_actions.keys()),
                {"tray.open", "tray.settings", "tray.quit"},
            )
            self.assertEqual(win._tray_actions["tray.open"].text(), i18n.tr("tray.open"))

            # กดปิดหน้าต่าง → ignore close แล้วซ่อนลง tray
            event = QCloseEvent()
            win.closeEvent(event)
            self.assertFalse(event.isAccepted())
            self.assertTrue(win.isHidden())

            # เปลี่ยนภาษา → เมนู tray ต้องแปลตามทันที
            i18n.setup("en", self._tmp.name)
            win.retranslate()
            self.assertEqual(win._tray_actions["tray.open"].text(), "Open TaskbarNoob")
            self.assertEqual(win._tray_actions["tray.settings"].text(), "Settings...")
            self.assertEqual(win._tray_actions["tray.quit"].text(), "Quit")

            # กดออกจริง → ยอมรับ closeEvent และคืน quitOnLastWindowClosed
            with patch.object(self.app, "quit") as mock_quit:
                win.quit_app()
                mock_quit.assert_called_once()
            self.assertTrue(self.app.quitOnLastWindowClosed())

    def test_settings_dialog_toggles_tray_and_calls_sync(self) -> None:
        from taskbarnoob.core.settings import Settings
        from taskbarnoob.gui.settings_dialog import SettingsDialog

        main_stub = MagicMock()
        dialog = SettingsDialog(main_stub)
        self.assertFalse(dialog.tray_check.isChecked())
        dialog.tray_check.setChecked(True)
        self.assertTrue(Settings(self._tmp.name).get_minimize_to_tray())
        main_stub.sync_tray.assert_called()
        dialog.close()


if __name__ == "__main__":
    unittest.main()
