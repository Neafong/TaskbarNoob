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


class _FakeScreen:
    def __init__(self, geometry: QRect, available: QRect) -> None:
        self._geometry = geometry
        self._available = available

    def geometry(self) -> QRect:
        return self._geometry

    def availableGeometry(self) -> QRect:
        return self._available


@unittest.skipUnless(HAVE_QT, "PySide6 not installed")
class PanelAnchorTests(unittest.TestCase):
    def test_bottom_panel_anchors_above_panel(self) -> None:
        from taskbargroups.gui.flyout import panel_anchor_position

        screen = _FakeScreen(QRect(0, 0, 1920, 1080), QRect(0, 0, 1920, 1040))
        pos = panel_anchor_position(QPoint(960, 1030), QSize(300, 200), screen)
        self.assertEqual(pos.y(), 1040 - 200)
        self.assertEqual(pos.x(), 960 - 150)

    def test_top_panel_anchors_below_panel(self) -> None:
        from taskbargroups.gui.flyout import panel_anchor_position

        screen = _FakeScreen(QRect(0, 0, 1920, 1080), QRect(0, 40, 1920, 1040))
        pos = panel_anchor_position(QPoint(960, 10), QSize(300, 200), screen)
        self.assertEqual(pos.y(), 40)

    def test_left_panel_anchors_and_clamps(self) -> None:
        from taskbargroups.gui.flyout import panel_anchor_position

        screen = _FakeScreen(QRect(0, 0, 1920, 1080), QRect(60, 0, 1860, 1080))
        pos = panel_anchor_position(QPoint(10, 5), QSize(300, 200), screen)
        self.assertEqual(pos.x(), 60)
        self.assertEqual(pos.y(), 0)

    def test_no_panel_falls_back_to_cursor(self) -> None:
        from taskbargroups.gui.flyout import MOUSE_OFFSET, panel_anchor_position

        screen = _FakeScreen(QRect(0, 0, 1920, 1080), QRect(0, 0, 1920, 1080))
        pos = panel_anchor_position(QPoint(960, 800), QSize(300, 200), screen)
        self.assertEqual(pos.y(), 800 - 200 - MOUSE_OFFSET)

    def test_focus_position_is_centered(self) -> None:
        from taskbargroups.gui.flyout import focus_position

        pos = focus_position(QSize(300, 200), QRect(0, 0, 1920, 1080))
        self.assertEqual(pos.x(), (1920 - 300) // 2)
        self.assertEqual(pos.y(), (1080 - 200) // 2)


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

    def test_reveal_uses_platform_opener(self) -> None:
        import sys
        from pathlib import Path
        from unittest import mock

        from taskbargroups.gui.flyout import FlyoutWindow

        target = Path(self._tmp.name) / "song.mp3"
        target.write_bytes(b"ID3fake")
        group = self.store.load_group("G")
        window = FlyoutWindow(group, self.store, "G")
        try:
            item = Shortcut(name="s", target=str(target))
            cases = [
                ("win32", ["explorer", f"/select,{target}"]),
                ("darwin", ["open", "-R", str(target)]),
                ("linux", ["xdg-open", str(target.parent)]),
            ]
            for platform, expected in cases:
                with self.subTest(platform=platform):
                    with mock.patch.object(
                        sys, "platform", platform
                    ), mock.patch("subprocess.Popen") as popen:
                        window._reveal(item)
                    popen.assert_called_once_with(
                        expected, env=mock.ANY, start_new_session=True
                    )
        finally:
            window.deleteLater()

    def test_labels_hidden_makes_square_buttons(self) -> None:
        from taskbargroups.gui.flyout import FlyoutWindow

        group = self.store.load_group("G")
        window = FlyoutWindow(group, self.store, "G", default_show_labels=False)
        try:
            button = window.buttons[0]
            self.assertEqual(button.text(), "")
            self.assertEqual(button.width(), button.height())
        finally:
            window.deleteLater()

    def test_labels_shown_uses_item_name(self) -> None:
        from taskbargroups.gui.flyout import FlyoutWindow

        group = self.store.load_group("G")
        window = FlyoutWindow(group, self.store, "G", default_show_labels=True)
        try:
            self.assertEqual(window.buttons[0].text(), "a")
        finally:
            window.deleteLater()

    def test_group_override_beats_app_default(self) -> None:
        from taskbargroups.core.models import Group
        from taskbargroups.gui.flyout import FlyoutWindow

        for override, expected_text in ((True, True), (False, False)):
            group = Group(
                name="H",
                show_labels=override,
                items=[Shortcut(name="z", target="/bin/true")],
            )
            window = FlyoutWindow(group, self.store, "H", default_show_labels=not override)
            try:
                self.assertEqual(window.show_labels, override)
                self.assertEqual(bool(window.buttons[0].text()), expected_text)
            finally:
                window.deleteLater()

    def test_focus_mode_scales_icons(self) -> None:
        from taskbargroups.gui.flyout import FOCUS_MIN_ICON, FlyoutWindow

        group = self.store.load_group("G")
        normal = FlyoutWindow(group, self.store, "G")
        focus = FlyoutWindow(group, self.store, "G", focus=True)
        try:
            self.assertGreater(focus._icon_size(), normal._icon_size())
            self.assertGreaterEqual(focus._icon_size(), FOCUS_MIN_ICON)
        finally:
            normal.deleteLater()
            focus.deleteLater()

    def test_focus_mode_uses_group_scale(self) -> None:
        from taskbargroups.core.models import Group
        from taskbargroups.gui.flyout import FlyoutWindow

        group = Group(
            name="G",
            icon_size=32,
            focus_scale=2.0,
            items=[Shortcut(name="a", target="/bin/true")],
        )
        window = FlyoutWindow(group, self.store, "G", focus=True)
        try:
            self.assertEqual(window._icon_size(), 64)
        finally:
            window.deleteLater()


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

    def test_start_primary_carries_focus_mode(self) -> None:
        from taskbargroups.gui.flyout import FlyoutController

        primary = FlyoutController(self.app, self.store, server_name=self.name)
        primary.start_primary("G", QPoint(100, 100), True)
        try:
            self.assertIsNotNone(primary.window)
            self.assertTrue(primary.window.focus_mode)

            secondary = FlyoutController(self.app, self.store, server_name=self.name)
            self.assertTrue(secondary.try_delegate("H", QPoint(5, 5), True))
            for _ in range(100):
                self.app.processEvents()
                if primary.window is not None and primary.window.dir_name == "H":
                    break
                QTest.qWait(10)
            self.assertIsNotNone(primary.window)
            self.assertEqual(primary.window.dir_name, "H")
            self.assertTrue(primary.window.focus_mode)
        finally:
            if primary.window is not None:
                primary.window.close()
            if primary.server is not None:
                primary.server.close()


if __name__ == "__main__":
    unittest.main()
