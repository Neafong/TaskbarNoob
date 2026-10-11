import os
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QPoint, QRect, QSize
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except ImportError:
    HAVE_QT = False

from taskbargroups.core.models import Group, Shortcut
from taskbargroups.core.storage import ConfigStore


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class PositionTests(unittest.TestCase):
    def test_centered_above_cursor(self) -> None:
        from taskbargroups.gui.flyout import MOUSE_OFFSET, flyout_position

        area = QRect(0, 0, 1920, 1080)
        pos = flyout_position(QPoint(960, 800), QSize(300, 200), area)
        self.assertEqual(pos.x(), 960 - 150)
        self.assertEqual(pos.y(), 800 - 200 - MOUSE_OFFSET)

    def test_clamped_to_left_edge(self) -> None:
        from taskbargroups.gui.flyout import flyout_position

        area = QRect(0, 0, 1920, 1080)
        pos = flyout_position(QPoint(5, 800), QSize(300, 200), area)
        self.assertEqual(pos.x(), 0)

    def test_clamped_to_right_edge(self) -> None:
        from taskbargroups.gui.flyout import flyout_position

        area = QRect(0, 0, 1920, 1080)
        pos = flyout_position(QPoint(1915, 800), QSize(300, 200), area)
        self.assertEqual(pos.x(), 1920 - 300)

    def test_flips_below_when_no_room_above(self) -> None:
        from taskbargroups.gui.flyout import MOUSE_OFFSET, flyout_position

        area = QRect(0, 0, 1920, 1080)
        pos = flyout_position(QPoint(960, 5), QSize(300, 200), area)
        self.assertEqual(pos.y(), 5 + MOUSE_OFFSET)

    def test_clamps_when_taller_than_screen(self) -> None:
        from taskbargroups.gui.flyout import flyout_position

        area = QRect(0, 0, 400, 100)
        pos = flyout_position(QPoint(200, 80), QSize(300, 200), area)
        self.assertEqual(pos.y(), 0)
        self.assertEqual(pos.x(), 50)


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class FlyoutWindowTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConfigStore(self._tmp.name)
        self.store.save_group(
            Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_closed_signal_emits_once(self) -> None:
        from taskbargroups.gui.flyout import FlyoutWindow

        group = self.store.load_group("G")
        window = FlyoutWindow(group, self.store, "G")
        received: list[int] = []
        window.closed.connect(lambda: received.append(1))
        window.show()
        window.close()
        window.close()
        window.deleteLater()
        self.app.processEvents()
        self.assertEqual(received, [1])


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class ControllerTests(unittest.TestCase):
    app = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = ConfigStore(self._tmp.name)
        self.store.save_group(
            Group(name="G", items=[Shortcut(name="a", target="/bin/true")])
        )
        self.store.save_group(
            Group(name="H", items=[Shortcut(name="b", target="/bin/false")])
        )
        self.name = f"tbg-test-{os.getpid()}-{id(self)}"

    def tearDown(self) -> None:
        from PySide6.QtNetwork import QLocalServer

        QLocalServer.removeServer(self.name)
        self._tmp.cleanup()

    def test_delegate_false_without_running_instance(self) -> None:
        from taskbargroups.gui.flyout import FlyoutController

        controller = FlyoutController(self.app, self.store, server_name=self.name)
        self.assertFalse(controller.try_delegate("G"))

    def test_primary_opens_then_delegate_switches_group(self) -> None:
        from taskbargroups.gui.flyout import FlyoutController

        primary = FlyoutController(self.app, self.store, server_name=self.name)
        primary.start_primary("G")
        self.assertIsNotNone(primary.window)
        self.assertEqual(primary.window.dir_name, "G")

        secondary = FlyoutController(self.app, self.store, server_name=self.name)
        self.assertTrue(secondary.try_delegate("H"))

        for _ in range(100):
            self.app.processEvents()
            if primary.window is not None and primary.window.dir_name == "H":
                break
            QTest.qWait(10)
        self.assertIsNotNone(primary.window)
        self.assertEqual(primary.window.dir_name, "H")

        if primary.window is not None:
            primary.window.close()
        if primary.server is not None:
            primary.server.close()

    def test_same_group_is_reused(self) -> None:
        from taskbargroups.gui.flyout import FlyoutController

        primary = FlyoutController(self.app, self.store, server_name=self.name)
        primary.start_primary("G")
        first = primary.window

        secondary = FlyoutController(self.app, self.store, server_name=self.name)
        self.assertTrue(secondary.try_delegate("G"))
        for _ in range(50):
            self.app.processEvents()
            QTest.qWait(5)
        self.assertIs(primary.window, first)

        if primary.window is not None:
            primary.window.close()
        if primary.server is not None:
            primary.server.close()


if __name__ == "__main__":
    unittest.main()
