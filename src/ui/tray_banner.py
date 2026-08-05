import os
import time
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtGui import QFont, QColor, QIcon, QPixmap
from src.utils import get_resource_path

class AppleTrayBanner(QWidget):
    """
    Kullanıcı aktifken / Mattermost açıkken ekranın sağ alt köşesinde (sistem tepsisi üstü)
    beliren, kibar, zarif Apple macOS bildirim kartı stiline sahip KALICI popup.
    """
    closed = Signal(dict)

    def __init__(self, config_manager, sound_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.sound_manager = sound_manager
        self.current_payload = None

        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(360, 150)
        self.setWindowTitle("Mattermost Bildirim")

        ico_path = get_resource_path("app.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # Glassmorphic Container Card
        self.card_frame = QFrame(self)
        self.card_frame.setObjectName("AppleCardFrame")

        # Soft drop shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 6)
        self.card_frame.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card_frame)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(6)

        # 1. Header (Icon + App Title + Time + Close Button)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        logo_path = get_resource_path("albay-logo.png")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("albay-logo.jpg")

        if os.path.exists(logo_path):
            logo_label = QLabel(self)
            pix = QPixmap(logo_path).scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
            header_layout.addWidget(logo_label)

        self.app_title_label = QLabel("Mattermost", self)
        self.app_title_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.app_title_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        self.dot_label = QLabel("•", self)
        self.dot_label.setStyleSheet("color: rgba(255, 255, 255, 0.4);")

        self.time_label = QLabel("Şimdi", self)
        self.time_label.setFont(QFont("Segoe UI", 8))
        self.time_label.setStyleSheet("color: rgba(255, 255, 255, 0.5);")

        header_layout.addWidget(self.app_title_label)
        header_layout.addWidget(self.dot_label)
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()

        # Close button ('✕')
        self.close_btn = QPushButton("✕", self)
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.12);
                color: rgba(255, 255, 255, 0.7);
                border: none;
                border-radius: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 59, 48, 0.85);
                color: #FFFFFF;
            }
        """)
        self.close_btn.clicked.connect(self.on_close_clicked)
        header_layout.addWidget(self.close_btn)

        # 2. Sender Name
        self.sender_label = QLabel("Gönderici", self)
        self.sender_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.sender_label.setStyleSheet("color: #FFFFFF;")

        # 3. Message Body Snippet
        self.msg_label = QLabel("Mesaj metni...", self)
        self.msg_label.setFont(QFont("Segoe UI", 9))
        self.msg_label.setWordWrap(True)
        self.msg_label.setMaxLines(2) if hasattr(self.msg_label, 'setMaxLines') else None
        self.msg_label.setStyleSheet("color: rgba(235, 235, 245, 0.85); line-height: 1.2;")

        card_layout.addLayout(header_layout)
        card_layout.addWidget(self.sender_label)
        card_layout.addWidget(self.msg_label, stretch=1)

        main_layout.addWidget(self.card_frame)

    def display_alert(self, payload):
        self.current_payload = payload
        has_acil = payload.get("has_acil", False)
        priority = payload.get("priority", "normal").lower()

        # Apple Dark Glass styling with subtle accent borders
        border_color = "rgba(10, 132, 255, 0.45)"
        badge_prefix = ""
        if has_acil or priority in ("critical", "disaster", "warning"):
            border_color = "rgba(255, 69, 58, 0.65)"
            badge_prefix = "🚨 "

        self.card_frame.setStyleSheet(f"""
            QFrame#AppleCardFrame {{
                background-color: rgba(28, 28, 34, 0.94);
                border: 1px solid {border_color};
                border-radius: 14px;
            }}
        """)

        sender = payload.get("sender", "Bilinmeyen")
        channel = payload.get("channel", "Genel")
        self.sender_label.setText(f"{badge_prefix}{sender} (#{channel})")

        msg_text = payload.get("message", "").strip()
        if len(msg_text) > 110:
            msg_text = msg_text[:107] + "..."
        self.msg_label.setText(msg_text)

        curr_time = time.strftime("%H:%M")
        self.time_label.setText(curr_time)

        self.reposition_to_bottom_right()
        self.show()
        self.raise_()

        # Sound playback
        self.sound_manager.play_alert_sound(priority)

    def reposition_to_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        width = self.width()
        height = self.height()
        
        # Bottom-right corner with 16px margin from taskbar
        x = screen.right() - width - 16
        y = screen.bottom() - height - 16
        self.move(x, y)

    def on_close_clicked(self):
        self.sound_manager.stop_sound()
        if self.current_payload:
            self.closed.emit(self.current_payload)
        self.hide()
