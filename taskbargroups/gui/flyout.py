"""หน้าต่าง flyout แสดง grid ไอคอนของกลุ่ม (Phase 2 MVP)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QMenu,
)

from taskbargroups.core.i18n import tr
from taskbargroups.core.launcher import LaunchError, child_env, launch
from taskbargroups.core.models import (
    MAX_ICON_SIZE,
    MIN_ICON_SIZE,
    ColorMode,
    Group,
    Shortcut,
)
from taskbargroups.core.settings import Settings
from taskbargroups.core.storage import ConfigStore, StorageError

from .icons import shortcut_icon

_BACKGROUNDS = {
    ColorMode.DARK: "#202124",
    ColorMode.LIGHT: "#f1f3f4",
}

SERVER_NAME_PREFIX = "taskbargroups-flyout"
DELEGATE_TIMEOUT_MS = 350
QUIT_GRACE_MS = 4000
MOUSE_OFFSET = 6

# โหมดโฟกัส (เปิดด้วย hotkey): ขยายไอคอนตาม group.focus_scale + โผล่กลางจอ
FOCUS_MIN_ICON = 48

# ความกว้าง/สูงปุ่มเมื่อโชว์ชื่อใต้ไอคอน
LABEL_PADDING = 16
LABEL_MAX_WIDTH = 168


def default_server_name() -> str:
    """ชื่อ QLocalServer ร่วมกันทุก process (แยกตาม user)."""
    uid = getattr(os, "getuid", lambda: 0)()
    return f"{SERVER_NAME_PREFIX}-{uid}"


def flyout_position(point: QPoint, size: QSize, area, offset: int = MOUSE_OFFSET) -> QPoint:
    """คำนวณตำแหน่ง flyout: กึ่งกลางแนวนอนเหนือจุดเมาส์ + clamp ให้อยู่ในจอ."""
    x = point.x() - size.width() // 2
    x = max(area.left(), min(x, area.right() - size.width() + 1))
    y = point.y() - size.height() - offset
    if y < area.top():
        y = point.y() + offset
    y = max(area.top(), min(y, area.bottom() - size.height() + 1))
    return QPoint(x, y)


def panel_anchor_position(point: QPoint, size: QSize, screen) -> QPoint:
    """วาง flyout ชิดขอบ panel แล้วตรึงไว้ (ไม่วิ่งตามเมาส์).

    หา panel จากส่วนต่างระหว่างจอเต็มกับ work area · วางชิดขอบ panel นั้น
    ส่วนแกนตามขอบใช้ตำแหน่งที่จับได้ (ประมาณไอคอนที่คลิก) · ถ้าไม่เจอ panel
    (work area เท่าจอ) ค่อยถอยไปใช้ flyout_position แบบเดิม
    """
    geom = screen.geometry()
    area = screen.availableGeometry()
    gaps = {
        "bottom": geom.bottom() - area.bottom(),
        "top": area.top() - geom.top(),
        "left": area.left() - geom.left(),
        "right": geom.right() - area.right(),
    }
    edge = max(gaps, key=lambda key: gaps[key])
    if gaps[edge] <= 0:
        return flyout_position(point, size, area)

    if edge in ("bottom", "top"):
        x = point.x() - size.width() // 2
        x = max(area.left(), min(x, area.right() - size.width() + 1))
        y = area.bottom() - size.height() + 1 if edge == "bottom" else area.top()
    else:
        y = point.y() - size.height() // 2
        x = area.left() if edge == "left" else area.right() - size.width() + 1
    x = max(area.left(), min(x, area.right() - size.width() + 1))
    y = max(area.top(), min(y, area.bottom() - size.height() + 1))
    return QPoint(x, y)


def focus_position(size: QSize, geom) -> QPoint:
    """วาง flyout กึ่งกลางจอ (โหมดโฟกัสจาก hotkey)."""
    x = geom.left() + (geom.width() - size.width()) // 2
    y = geom.top() + (geom.height() - size.height()) // 2
    return QPoint(max(geom.left(), x), max(geom.top(), y))


class FlyoutWindow(QWidget):
    closed = Signal()

    def __init__(
        self,
        group: Group,
        store: ConfigStore,
        dir_name: str,
        focus: bool = False,
        default_show_labels: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.group = group
        self.store = store
        self.dir_name = dir_name
        self.focus_mode = focus
        # กลุ่มตั้งค่าเองได้ (show_labels) · ไม่ตั้ง = ใช้ค่าเริ่มต้นระดับแอป
        self.show_labels = (
            group.show_labels if group.show_labels is not None else default_show_labels
        )
        self.buttons: list[QToolButton] = []
        self._closed_emitted = False

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowTitle(group.name)

        self._build_ui()
        self._apply_style()

        if 0 <= group.opacity <= 100:
            self.setWindowOpacity(1.0 - (group.opacity / 100.0))

    def closeEvent(self, event) -> None:
        self._emit_closed()
        super().closeEvent(event)

    def hideEvent(self, event) -> None:
        super().hideEvent(event)
        self._emit_closed()

    def _emit_closed(self) -> None:
        if not self._closed_emitted:
            self._closed_emitted = True
            self.closed.emit()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 10)

        frame = QFrame()
        frame.setObjectName("flyoutFrame")
        outer.addWidget(frame)

        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(10, 8, 10, 10)

        title = QLabel(self.group.name)
        title.setObjectName("flyoutTitle")
        title.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(6)
        columns = max(1, self.group.width)

        for index, item in enumerate(self.group.items):
            button = self._make_button(item)
            self.buttons.append(button)
            grid.addWidget(button, index // columns, index % columns)

        frame_layout.addLayout(grid)

    def _icon_size(self) -> int:
        base = max(MIN_ICON_SIZE, min(MAX_ICON_SIZE, self.group.icon_size))
        if self.focus_mode:
            base = min(
                MAX_ICON_SIZE,
                max(FOCUS_MIN_ICON, round(base * self.group.focus_scale)),
            )
        return base

    def _make_button(self, item) -> QToolButton:
        icon_size = self._icon_size()
        button = QToolButton()
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setIcon(shortcut_icon(item, self.store, self.dir_name))
        button.setIconSize(QSize(icon_size, icon_size))
        button.setToolTip(item.name or item.target)
        if self.show_labels:
            label = item.name or item.target
            button.setText(label)
            metrics = button.fontMetrics()
            width = metrics.horizontalAdvance(label) + LABEL_PADDING
            width = max(icon_size + 28, min(width, LABEL_MAX_WIDTH))
            height = icon_size + metrics.height() + 20
        else:
            button.setText("")
            width = height = icon_size + LABEL_PADDING
        button.setFixedSize(QSize(width, height))
        button.setContextMenuPolicy(Qt.CustomContextMenu)
        button.customContextMenuRequested.connect(
            lambda _pos, it=item: self._show_context_menu(it)
        )
        button.clicked.connect(lambda _=False, it=item: self._launch(it))
        return button

    def _background(self) -> str:
        mode = self.group.color_mode
        if mode is ColorMode.CUSTOM and self.group.custom_color:
            return self.group.custom_color
        return _BACKGROUNDS.get(mode, "#202124")

    def _apply_style(self) -> None:
        background = self._background()
        color = QColor(background)
        if not color.isValid():
            color = QColor(_BACKGROUNDS[ColorMode.DARK])
            background = _BACKGROUNDS[ColorMode.DARK]
        luminance = color.red() * 0.2126 + color.green() * 0.7152 + color.blue() * 0.0722
        if luminance > 127:
            text = "#202124"
            hover_bg = "rgba(0, 0, 0, 30)"
            hover_border = "rgba(0, 0, 0, 60)"
        else:
            text = "#f5f5f5"
            hover_bg = "rgba(255, 255, 255, 40)"
            hover_border = "rgba(255, 255, 255, 70)"
        self.setStyleSheet(
            f"""
            QFrame#flyoutFrame {{
                background-color: {background};
                border-radius: 10px;
            }}
            QLabel#flyoutTitle {{
                color: {text};
                font-weight: bold;
                padding-bottom: 4px;
            }}
            QToolButton {{
                color: {text};
                border: 1px solid transparent;
                border-radius: 8px;
                padding: 4px;
            }}
            QToolButton:hover {{
                background-color: {hover_bg};
                border: 1px solid {hover_border};
            }}
            """
        )

    def show_at(self, point: QPoint | None = None) -> None:
        """โชว์ flyout โดยตรึงตำแหน่งไว้ (point = ตำแหน่งที่จับได้ตอนเรียก)."""
        self.adjustSize()
        if point is None:
            point = QCursor.pos()
        screen = QGuiApplication.screenAt(point) or QGuiApplication.primaryScreen()
        if self.focus_mode:
            pos = focus_position(self.size(), screen.geometry())
        else:
            pos = panel_anchor_position(point, self.size(), screen)
        self.move(pos)
        self.show()
        self.raise_()
        self.activateWindow()

    def show_at_cursor(self) -> None:
        self.show_at(None)

    def _show_context_menu(self, item: Shortcut) -> None:
        path = Path(item.target.strip())
        if not path.exists():
            return
        menu = QMenu(self)
        menu.addAction(tr("flyout.reveal"), lambda: self._reveal(item))
        menu.exec(QCursor.pos())
        menu.deleteLater()

    def _reveal(self, item: Shortcut) -> None:
        path = Path(item.target.strip())
        if not path.exists():
            return
        parent = path.parent
        if not parent.exists():
            return
        env = child_env()
        try:
            import subprocess

            if sys.platform == "win32":
                # เลือกไฟล์ค้างไว้ใน Explorer
                subprocess.Popen(
                    ["explorer", f"/select,{path}"], env=env, start_new_session=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen(
                    ["open", "-R", str(path)], env=env, start_new_session=True
                )
            else:
                subprocess.Popen(
                    ["xdg-open", str(parent)], env=env, start_new_session=True
                )
        except OSError:
            if sys.platform != "linux":
                return
            try:
                import subprocess

                subprocess.Popen(
                    ["gio", "open", str(parent)], env=env, start_new_session=True
                )
            except OSError:
                pass

    def _launch(self, item) -> None:
        try:
            launch(item)
        except LaunchError as exc:
            self.setToolTip(str(exc))
            return
        self.close()

    def keyPressEvent(self, event) -> None:
        key = event.key()

        if key == Qt.Key_Escape:
            self.close()
            return

        digit = self._digit_index(key)
        if digit is not None and digit < len(self.group.items):
            self._launch(self.group.items[digit])
            return

        super().keyPressEvent(event)

    @staticmethod
    def _digit_index(key: int) -> int | None:
        if Qt.Key_1 <= key <= Qt.Key_9:
            return key - Qt.Key_1
        if key == Qt.Key_0:
            return 9
        return None


class FlyoutController(QObject):
    """คุม flyout ให้เป็น single-instance ข้าม process (กันค้างซ้อน).

    process แรกเป็นเจ้าของ `QLocalServer` + หน้าต่าง · process ถัดไป connect
    แล้วส่งชื่อกลุ่มมาให้เจ้าของเปิด/สลับให้ แล้วปิดตัวเองทันที.
    """

    def __init__(
        self,
        app,
        store: ConfigStore,
        server_name: str | None = None,
    ) -> None:
        super().__init__()
        self.app = app
        self.store = store
        self.window: FlyoutWindow | None = None
        self.server: QLocalServer | None = None
        self._server_name = server_name or default_server_name()
        self._quit_timer = QTimer(self)
        self._quit_timer.setSingleShot(True)
        self._quit_timer.setInterval(QUIT_GRACE_MS)
        self._quit_timer.timeout.connect(self.app.quit)
        self.app.setQuitOnLastWindowClosed(False)
        try:
            self.show_labels = Settings(store.config_dir).get_flyout_labels()
        except Exception:
            self.show_labels = False

    @property
    def server_name(self) -> str:
        return self._server_name

    def try_delegate(
        self, group_dir: str, point: QPoint | None = None, center: bool = False
    ) -> bool:
        """ถ้ามี instance อยู่แล้ว ส่งชื่อกลุ่มไปแล้วคืน True (ไม่ต้องเปิดหน้าต่างเอง)."""
        socket = QLocalSocket()
        socket.connectToServer(self._server_name)
        if not socket.waitForConnected(DELEGATE_TIMEOUT_MS):
            socket.abort()
            return False
        payload: dict[str, object] = {"group": group_dir, "center": bool(center)}
        if point is not None:
            payload["x"] = point.x()
            payload["y"] = point.y()
        socket.write((json.dumps(payload) + "\n").encode("utf-8"))
        socket.flush()
        socket.waitForBytesWritten(DELEGATE_TIMEOUT_MS)
        socket.disconnectFromServer()
        if socket.state() != QLocalSocket.UnconnectedState:
            socket.waitForDisconnected(DELEGATE_TIMEOUT_MS)
        return True

    def start_primary(
        self, group_dir: str, point: QPoint | None = None, center: bool = False
    ) -> None:
        QLocalServer.removeServer(self._server_name)
        self.server = QLocalServer(self)
        if not self.server.listen(self._server_name):
            self.open_group(group_dir, point, center)
            return
        self.server.newConnection.connect(self._on_new_connection)
        self.open_group(group_dir, point, center)

    def _on_new_connection(self) -> None:
        while self.server is not None and self.server.hasPendingConnections():
            connection = self.server.nextPendingConnection()
            connection.readyRead.connect(lambda c=connection: self._read_request(c))
            connection.disconnected.connect(connection.deleteLater)

    def _read_request(self, connection: QLocalSocket) -> None:
        data = bytes(connection.readAll()).decode("utf-8", "replace").strip()
        if not data:
            return
        group_dir = data
        point: QPoint | None = None
        center = False
        if data.startswith("{"):
            try:
                payload = json.loads(data)
            except (ValueError, TypeError):
                payload = None
            if isinstance(payload, dict):
                group_dir = str(payload.get("group", ""))
                center = bool(payload.get("center"))
                if payload.get("x") is not None and payload.get("y") is not None:
                    try:
                        point = QPoint(int(payload["x"]), int(payload["y"]))
                    except (TypeError, ValueError):
                        point = None
        if group_dir:
            self.open_group(group_dir, point, center)

    def open_group(
        self, group_dir: str, point: QPoint | None = None, center: bool = False
    ) -> None:
        self._quit_timer.stop()
        if self.window is not None:
            if self.window.dir_name == group_dir and self.window.focus_mode == center:
                self.window.show_at(point)
                return
            old = self.window
            self.window = None
            try:
                old.closed.disconnect(self._on_closed)
            except (RuntimeError, TypeError):
                pass
            old.close()
            old.deleteLater()
        try:
            group = self.store.load_group(group_dir)
        except StorageError:
            self._schedule_quit()
            return
        window = FlyoutWindow(
            group,
            self.store,
            group_dir,
            focus=center,
            default_show_labels=self.show_labels,
        )
        window.closed.connect(self._on_closed)
        self.window = window
        window.show_at(point)

    def _on_closed(self) -> None:
        window = self.window
        self.window = None
        if window is not None:
            window.deleteLater()
        self._schedule_quit()

    def shutdown(self) -> None:
        self._quit_timer.stop()
        if self.server is not None:
            self.server.close()
        window = self.window
        self.window = None
        if window is not None:
            window.close()
            window.deleteLater()

    def _schedule_quit(self) -> None:
        self._quit_timer.start()
