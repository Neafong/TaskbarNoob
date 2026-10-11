"""ไดอะล็อก About — ชื่อแอป/เวอร์ชัน/เครดิต (Noob & Pickle)."""

from __future__ import annotations

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from taskbargroups.core.i18n import tr
from taskbargroups.core.paths import app_icon_path
from taskbargroups.core.settings import Settings

try:  # เวอร์ชันมาจากแพ็กเกจ (single source of truth)
    from taskbargroups import __version__ as APP_VERSION
except Exception:  # pragma: no cover - กัน import พังตอน build แปลกๆ
    APP_VERSION = ""


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, donate_url: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.donate_url = donate_url if donate_url is not None else Settings().get_donate_url()
        self.resize(360, 280)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        icon_path = app_icon_path()
        if icon_path is not None:
            logo = QLabel()
            logo.setPixmap(QPixmap(str(icon_path)).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)

        name = QLabel(tr("app.title"))
        name_font = name.font()
        name_font.setPointSize(name_font.pointSize() + 6)
        name_font.setBold(True)
        name.setFont(name_font)
        name.setAlignment(Qt.AlignCenter)
        layout.addWidget(name)

        if APP_VERSION:
            version = QLabel(tr("about.version", version=APP_VERSION))
            version.setAlignment(Qt.AlignCenter)
            layout.addWidget(version)

        tagline = QLabel(tr("about.tagline"))
        tagline.setWordWrap(True)
        tagline.setAlignment(Qt.AlignCenter)
        layout.addWidget(tagline)

        layout.addStretch(1)

        credits = QLabel(tr("about.credits"))
        credits_font = credits.font()
        credits_font.setBold(True)
        credits.setFont(credits_font)
        credits.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits)

        note = QLabel(tr("about.credits_note"))
        note.setWordWrap(True)
        note.setAlignment(Qt.AlignCenter)
        layout.addWidget(note)

        layout.addStretch(1)

        if self.donate_url:
            donate = QPushButton(tr("about.donate"))
            donate.setToolTip(tr("about.donate_tip"))
            donate.clicked.connect(self._open_donate)
            layout.addWidget(donate)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.accept)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        icon = QIcon(str(icon_path)) if icon_path is not None else QIcon()
        self.setWindowIcon(icon)

    def _open_donate(self) -> None:
        if self.donate_url:
            QDesktopServices.openUrl(QUrl(self.donate_url))
