import os
import time
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtGui import QFont, QColor, QKeyEvent, QIcon, QPixmap
from src.utils import get_resource_path

THEMES = {
    "normal": {
        "bg_gradient": "rgba(28, 28, 34, 0.95)",
        "accent": "#0A84FF",
        "border": "rgba(10, 132, 255, 0.40)",
        "badge_bg": "rgba(10, 132, 255, 0.20)",
        "badge_text": "#64D2FF",
        "badge_label": "💬 YENİ MESAJ BİLDİRİMİ",
        "btn_bg": "#0A84FF",
        "btn_hover": "#409CFF",
        "btn_text": "✓ Okudum / Anladım"
    },
    "warning": {
        "bg_gradient": "rgba(34, 28, 20, 0.95)",
        "accent": "#FF9F0A",
        "border": "rgba(255, 159, 10, 0.45)",
        "badge_bg": "rgba(255, 159, 10, 0.20)",
        "badge_text": "#FFD60A",
        "badge_label": "⚠️ UYARI BİLDİRİMİ",
        "btn_bg": "#FF9F0A",
        "btn_hover": "#FFB340",
        "btn_text": "✓ Uvarıyı Anladım / Kapat"
    },
    "critical": {
        "bg_gradient": "rgba(36, 22, 26, 0.95)",
        "accent": "#FF453A",
        "border": "rgba(255, 69, 58, 0.50)",
        "badge_bg": "rgba(255, 69, 58, 0.20)",
        "badge_text": "#FF6961",
        "badge_label": "🚨 ACİL MESAJ BİLDİRİMİ",
        "btn_bg": "#FF453A",
        "btn_hover": "#FF6961",
        "btn_text": "✓ Acil Mesajı Anladım / Kapat"
    },
    "disaster": {
        "bg_gradient": "rgba(40, 16, 24, 0.95)",
        "accent": "#FF375F",
        "border": "rgba(255, 55, 95, 0.60)",
        "badge_bg": "rgba(255, 55, 95, 0.25)",
        "badge_text": "#FF6482",
        "badge_label": "🔥 ACİL DURUM UYARISI",
        "btn_bg": "#FF375F",
        "btn_hover": "#FF597B",
        "btn_text": "✓ Acil Uyarıyı Anladım / Kapat"
    }
}

class EmergencyWindow(QWidget):
    """
    Uygulama kapalıyken / kullanıcı inaktifken tam ekranda beliren,
    Zarif Apple macOS tasarım çizgilerine sahip MERKEZİ bildirim popup'ı.
    """
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
        # Frameless, Always on top, Apple-style floating window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(580, 390)
        self.setWindowTitle("Mattermost Bildirim Popup")

        ico_path = get_resource_path("app.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Apple Acrylic Glass Container Frame
        self.container_frame = QFrame(self)
        self.container_frame.setObjectName("ContainerFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(35)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container_frame.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.container_frame)
        card_layout.setContentsMargins(24, 20, 24, 20)
        card_layout.setSpacing(12)

        # 1. Header Bar (Logo + Badge + Channel + Time)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        logo_path = get_resource_path("albay-logo.png")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("albay-logo.jpg")

        if os.path.exists(logo_path):
            logo_label = QLabel(self)
            logo_pixmap = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setStyleSheet("border-radius: 16px; background: transparent;")
            header_layout.addWidget(logo_label)

        self.badge_label = QLabel("💬 YENİ MESAJ BİLDİRİMİ", self)
        self.badge_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.badge_label.setContentsMargins(10, 4, 10, 4)
        
        self.channel_label = QLabel("#genel", self)
        self.channel_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Medium))
        self.channel_label.setStyleSheet("color: rgba(235, 235, 245, 0.6); padding-left: 4px;")

        self.time_label = QLabel("10:00:00", self)
        self.time_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: rgba(235, 235, 245, 0.85);")

        header_layout.addWidget(self.badge_label)
        header_layout.addWidget(self.channel_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)

        # 2. Title Section
        self.title_label = QLabel("Yeni Mesaj Geldi", self)
        self.title_label.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)

        # 3. Sender Info
        self.sender_label = QLabel("👤 Gönderen: Ali Yılmaz", self)
        self.sender_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        self.sender_label.setStyleSheet("color: rgba(235, 235, 245, 0.9);")

        # Apple Divider Line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.08); max-height: 1px;")

        # 4. Message Content Box (Apple Dark Acrylic Glass bubble)
        self.msg_box = QLabel("Mesaj içeriği buraya gelecek.", self)
        self.msg_box.setFont(QFont("Segoe UI", 10))
        self.msg_box.setWordWrap(True)
        self.msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.msg_box.setStyleSheet("""
            background-color: rgba(18, 18, 22, 0.60);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px;
            color: #F2F2F7;
            line-height: 1.4;
        """)

        # 5. Acknowledge / Close Button (Apple macOS primary button)
        self.ack_btn = QPushButton("✓ Okudum / Anladım", self)
        self.ack_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.ack_btn.setCursor(Qt.PointingHandCursor)
        self.ack_btn.setMinimumHeight(44)
        self.ack_btn.clicked.connect(self.on_acknowledge)

        # Add components to card layout
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

        # Apple Dark Glass styling with dynamic accent colors
        self.container_frame.setStyleSheet(f"""
            QFrame#ContainerFrame {{
                background-color: {theme["bg_gradient"]};
                border: 1px solid {theme["border"]};
                border-radius: 18px;
            }}
        """)

        self.badge_label.setText(theme["badge_label"])
        self.badge_label.setStyleSheet(f"""
            background-color: {theme["badge_bg"]};
            color: {theme["badge_text"]};
            border-radius: 8px;
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

        btn_text = theme.get("btn_text", "✓ Okudum / Anladım")
        self.ack_btn.setText(btn_text)
        self.ack_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme["btn_bg"]};
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 8px;
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

        # Play sound
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

            # Send ACK reply back to Mattermost channel if message was emergency
            if channel_id and self.current_payload.get("has_acil", False):
                self.api_client.post_ack(channel_id, post_id, title, message)

            self.acknowledged.emit(self.current_payload)

        self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        if not self.is_acknowledged:
            event.ignore()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        if not self.is_acknowledged:
            event.ignore()
        else:
            event.accept()
