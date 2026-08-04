import os
import time
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtGui import QFont, QColor, QKeyEvent, QIcon, QPixmap
from src.utils import get_resource_path

THEMES = {
    "normal": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1b26, stop:0.6 #16161e, stop:1 #13141c)",
        "card_bg": "rgba(26, 27, 38, 0.95)",
        "accent": "#7aa2f7",
        "border": "rgba(122, 162, 247, 0.45)",
        "badge_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)",
        "badge_text": "#FFFFFF",
        "badge_label": "💬 YENİ MESAJ BİLDİRİMİ",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #3b82f6)",
        "btn_hover": "#60a5fa",
        "btn_text": "✓ OKUDUM / ANLADIM"
    },
    "warning": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #291e10, stop:0.6 #21170a, stop:1 #191105)",
        "card_bg": "rgba(41, 30, 16, 0.95)",
        "accent": "#ff9e3b",
        "border": "rgba(255, 158, 59, 0.5)",
        "badge_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b)",
        "badge_text": "#FFFFFF",
        "badge_label": "⚠️ UYARI BİLDİRİMİ",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #f59e0b)",
        "btn_hover": "#fbbf24",
        "btn_text": "✓ UYARIYI ANLADIM / KAPAT"
    },
    "critical": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25131e, stop:0.6 #1e0e17, stop:1 #180911)",
        "card_bg": "rgba(37, 19, 30, 0.95)",
        "accent": "#f7768e",
        "border": "rgba(247, 118, 142, 0.55)",
        "badge_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #ef4444)",
        "badge_text": "#FFFFFF",
        "badge_label": "🚨 ACİL MESAJ BİLDİRİMİ",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #ef4444)",
        "btn_hover": "#f87171",
        "btn_text": "✓ ACİL MESAJI ANLADIM / KAPAT"
    },
    "disaster": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2b0b1a, stop:0.6 #200612, stop:1 #17030c)",
        "card_bg": "rgba(43, 11, 26, 0.95)",
        "accent": "#ff0055",
        "border": "rgba(255, 0, 85, 0.6)",
        "badge_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #990033, stop:1 #ff0055)",
        "badge_text": "#FFFFFF",
        "badge_label": "🔥 ACİL DURUM UYARISI",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #990033, stop:1 #ff0055)",
        "btn_hover": "#ff3377",
        "btn_text": "✓ ACİL UYARIYI ANLADIM / KAPAT"
    }
}

class EmergencyWindow(QWidget):
    acknowledged = Signal(dict)

    def __init__(self, config_manager, sound_manager, api_client, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.sound_manager = sound_manager
        self.api_client = api_client
        self.current_payload = None
        self.is_acknowledged = False
        
        self.init_ui()

    def init_ui(self):
        # Frameless, Always on top, clean tool window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(620, 400)
        self.setWindowTitle("Mattermost Bildirim Popup")

        ico_path = get_resource_path("app.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Container Frame with rounded corners and glassmorphic shadow
        self.container_frame = QFrame(self)
        self.container_frame.setObjectName("ContainerFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 8)
        self.container_frame.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.container_frame)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(14)

        # 1. Header Bar (Logo + Badge + Channel + Time)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        logo_path = get_resource_path("albay-logo.png")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("albay-logo.jpg")

        if os.path.exists(logo_path):
            logo_label = QLabel(self)
            logo_pixmap = QPixmap(logo_path).scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setStyleSheet("border-radius: 17px; background: transparent;")
            header_layout.addWidget(logo_label)

        self.badge_label = QLabel("💬 YENİ MESAJ BİLDİRİMİ", self)
        self.badge_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.badge_label.setContentsMargins(10, 4, 10, 4)
        
        self.channel_label = QLabel("#genel", self)
        self.channel_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.channel_label.setStyleSheet("color: rgba(255, 255, 255, 0.65); padding-left: 5px;")

        self.time_label = QLabel("10:00:00", self)
        self.time_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")

        header_layout.addWidget(self.badge_label)
        header_layout.addWidget(self.channel_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)

        # 2. Title Section
        self.title_label = QLabel("Yeni Mesaj Geldi", self)
        self.title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)

        # 3. Sender Info
        self.sender_label = QLabel("👤 Gönderen: Ali Yılmaz", self)
        self.sender_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.sender_label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.12); max-height: 1px;")

        # 4. Message Content Box
        self.msg_box = QLabel("Mesaj içeriği buraya gelecek.", self)
        self.msg_box.setFont(QFont("Segoe UI", 11))
        self.msg_box.setWordWrap(True)
        self.msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.msg_box.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.30);"
            "border: 1px solid rgba(255, 255, 255, 0.08);"
            "border-radius: 10px;"
            "padding: 14px;"
            "color: #F3F4F6;"
            "line-height: 1.4;"
        )

        # 5. Acknowledge / Close Button
        self.ack_btn = QPushButton("✓ OKUDUM / ANLADIM", self)
        self.ack_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.ack_btn.setCursor(Qt.PointingHandCursor)
        self.ack_btn.setMinimumHeight(48)
        self.ack_btn.clicked.connect(self.on_acknowledge)

        # Add components to layout
        card_layout.addLayout(header_layout)
        card_layout.addWidget(self.title_label)
        card_layout.addWidget(self.sender_label)
        card_layout.addWidget(line)
        card_layout.addWidget(self.msg_box, stretch=1)
        card_layout.addWidget(self.ack_btn)

        main_layout.addWidget(self.container_frame)

    def display_alert(self, payload):
        self.current_payload = payload
        self.is_acknowledged = False

        priority = payload.get("priority", "normal").lower()
        theme = THEMES.get(priority, THEMES["normal"])

        # Update styling based on theme
        self.container_frame.setStyleSheet(f"""
            QFrame#ContainerFrame {{
                background: {theme["bg_gradient"]};
                border: 1px solid {theme["border"]};
                border-radius: 18px;
            }}
        """)

        self.badge_label.setText(theme["badge_label"])
        self.badge_label.setStyleSheet(f"""
            background: {theme["badge_bg"]};
            color: {theme["badge_text"]};
            border-radius: 6px;
            padding: 4px 10px;
        """)

        self.title_label.setText(payload.get("title", "Mesaj Bildirimi"))
        self.title_label.setStyleSheet(f"color: {theme['accent']}; margin-top: 2px;")

        sender = payload.get("sender", "Bilinmeyen")
        self.sender_label.setText(f"👤 Gönderen: {sender}")

        channel = payload.get("channel", "Genel")
        self.channel_label.setText(f"📢 #{channel}")

        curr_time = time.strftime("%H:%M:%S")
        self.time_label.setText(f"🕒 {curr_time}")

        self.msg_box.setText(payload.get("message", ""))

        btn_text = theme.get("btn_text", "✓ OKUDUM / ANLADIM")
        self.ack_btn.setText(btn_text)
        self.ack_btn.setStyleSheet(f"""
            QPushButton {{
                background: {theme["btn_bg"]};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: {theme["btn_hover"]};
            }}
            QPushButton:pressed {{
                background-color: #000000;
            }}
        """)

        self.showNormal()
        self.center_on_screen()

        self.show()
        self.raise_()
        self.activateWindow()

        # Play gentle sound
        self.sound_manager.play_alert_sound(priority)

    def center_on_screen(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2)
        )

    def on_acknowledge(self):
        self.is_acknowledged = True
        self.sound_manager.stop_sound()

        if self.current_payload:
            channel_id = self.current_payload.get("channel_id", "")
            post_id = self.current_payload.get("post_id", "")
            title = self.current_payload.get("title", "Mesaj Bildirimi")
            message = self.current_payload.get("message", "")

            # Send ACK reply back to Mattermost channel if auto_post_ack is enabled and message was emergency
            if channel_id and self.current_payload.get("has_acil", False):
                self.api_client.post_ack(channel_id, post_id, title, message)

            self.acknowledged.emit(self.current_payload)

        self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        # User must click the button to dismiss the window
        if not self.is_acknowledged:
            print("[EmergencyWindow] Window dismissal blocked - User must click the button!")
            event.ignore()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Prevent window close until user explicitly clicks the acknowledge button
        if not self.is_acknowledged:
            print("[EmergencyWindow] Close attempt blocked - User must click the button!")
            event.ignore()
        else:
            event.accept()

