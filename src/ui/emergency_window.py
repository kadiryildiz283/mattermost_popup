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
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f2027, stop:0.5 #203a43, stop:1 #2c5364)",
        "card_bg": "rgba(15, 32, 39, 0.85)",
        "accent": "#00d2ff",
        "border": "#0088ff",
        "badge_bg": "#0055ff",
        "badge_text": "#FFFFFF",
        "badge_label": "BİLGİ / NORMAL",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0088ff, stop:1 #00d2ff)",
        "btn_hover": "#33e0ff"
    },
    "warning": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2b1f00, stop:0.5 #4a3500, stop:1 #6b4c00)",
        "card_bg": "rgba(43, 31, 0, 0.88)",
        "accent": "#ffb703",
        "border": "#ffaa00",
        "badge_bg": "#d48800",
        "badge_text": "#FFFFFF",
        "badge_label": "⚠️ UYARI",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ffaa00, stop:1 #ffc107)",
        "btn_hover": "#ffca28"
    },
    "critical": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #300000, stop:0.5 #5c0000, stop:1 #800000)",
        "card_bg": "rgba(48, 0, 0, 0.90)",
        "accent": "#ff4d4d",
        "border": "#ff0000",
        "badge_bg": "#cc0000",
        "badge_text": "#FFFFFF",
        "badge_label": "🚨 KRİTİK ACİL DURUM",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #cc0000, stop:1 #ff3333)",
        "btn_hover": "#ff6666"
    },
    "disaster": {
        "bg_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2b001a, stop:0.5 #52001e, stop:1 #800000)",
        "card_bg": "rgba(43, 0, 26, 0.92)",
        "accent": "#ff0055",
        "border": "#ff0055",
        "badge_bg": "#990033",
        "badge_text": "#FFFFFF",
        "badge_label": "🔥 AFET / KRİTİK ALARM",
        "btn_bg": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #990033, stop:1 #ff0055)",
        "btn_hover": "#ff3377"
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
        # Frameless, Always on top
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumSize(680, 440)
        self.setWindowTitle("Mattermost Emergency Client")

        ico_path = get_resource_path("app.ico")
        if os.path.exists(ico_path):
            self.setWindowIcon(QIcon(ico_path))

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Container Frame with rounded corners and dark shadow
        self.container_frame = QFrame(self)
        self.container_frame.setObjectName("ContainerFrame")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.container_frame.setGraphicsDropShadowEffect(shadow)

        card_layout = QVBoxLayout(self.container_frame)
        card_layout.setContentsMargins(30, 25, 30, 25)
        card_layout.setSpacing(15)

        # 1. Header Bar (Logo + Badge + Channel + Time)
        header_layout = QHBoxLayout()
        
        logo_path = get_resource_path("albay-logo.png")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("albay-logo.jpg")

        if os.path.exists(logo_path):
            logo_label = QLabel(self)
            logo_pixmap = QPixmap(logo_path).scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
            logo_label.setStyleSheet("border-radius: 21px; background: transparent;")
            header_layout.addWidget(logo_label)

        self.badge_label = QLabel("🚨 ACİL DURUM", self)
        self.badge_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.badge_label.setContentsMargins(12, 6, 12, 6)
        
        self.channel_label = QLabel("Kanal: #genel", self)
        self.channel_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.channel_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")

        self.time_label = QLabel("10:00:00", self)
        self.time_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: rgba(255, 255, 255, 0.9);")

        header_layout.addWidget(self.badge_label)
        header_layout.addWidget(self.channel_label)
        header_layout.addStretch()
        header_layout.addWidget(self.time_label)

        # 2. Title Section
        self.title_label = QLabel("YANGIN ALARMI", self)
        self.title_label.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.title_label.setWordWrap(True)

        # 3. Sender Info
        self.sender_label = QLabel("Gönderen: Ali Yılmaz", self)
        self.sender_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.sender_label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); max-height: 1px;")

        # 4. Message Content Box
        self.msg_box = QLabel("Sunucu odasında duman algılandı. Lütfen derhal tahliye edin.", self)
        self.msg_box.setFont(QFont("Segoe UI", 13))
        self.msg_box.setWordWrap(True)
        self.msg_box.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.msg_box.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.35);"
            "border-radius: 8px;"
            "padding: 16px;"
            "color: #FFFFFF;"
            "line-height: 1.4;"
        )

        # 5. Acknowledge Button ("OKUDUM")
        self.ack_btn = QPushButton("✔ OKUDUM / ONAYLADIM", self)
        self.ack_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.ack_btn.setCursor(Qt.PointingHandCursor)
        self.ack_btn.setMinimumHeight(56)
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

        priority = payload.get("priority", "critical").lower()
        theme = THEMES.get(priority, THEMES["critical"])

        # Update styling based on priority theme
        self.container_frame.setStyleSheet(f"""
            QFrame#ContainerFrame {{
                background: {theme["bg_gradient"]};
                border: 2px solid {theme["border"]};
                border-radius: 16px;
            }}
        """)

        self.badge_label.setText(theme["badge_label"])
        self.badge_label.setStyleSheet(f"""
            background-color: {theme["badge_bg"]};
            color: {theme["badge_text"]};
            border-radius: 6px;
            padding: 4px 10px;
        """)

        self.title_label.setText(payload.get("title", "ACİL DURUM ALARMI"))
        self.title_label.setStyleSheet(f"color: {theme['accent']}; margin-top: 5px;")

        sender = payload.get("sender", "Bilinmeyen")
        self.sender_label.setText(f"👤 Gönderen: {sender}")

        channel = payload.get("channel", "Genel")
        self.channel_label.setText(f"📢 Kanal: #{channel}")

        curr_time = time.strftime("%H:%M:%S")
        self.time_label.setText(f"🕒 {curr_time}")

        self.msg_box.setText(payload.get("message", ""))

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

        # Center on screen or set fullscreen
        if self.config.get("fullscreen_for_critical", False) and priority in ("critical", "disaster"):
            self.showFullScreen()
        else:
            self.showNormal()
            self.center_on_screen()

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
            title = self.current_payload.get("title", "Acil Durum")
            message = self.current_payload.get("message", "")

            if channel_id:
                # Post ACK reply back to Mattermost channel
                self.api_client.post_ack(channel_id, post_id, title, message)

            self.acknowledged.emit(self.current_payload)

        self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        # Prevent ESC from closing the window if configured
        if event.key() == Qt.Key_Escape:
            if self.config.get("disable_esc_key", True) and not self.is_acknowledged:
                print("[EmergencyWindow] ESC key blocked - User must click OKUDUM!")
                event.ignore()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # Prevent closing until acknowledged
        if not self.is_acknowledged:
            print("[EmergencyWindow] Close attempt blocked - User must click OKUDUM!")
            event.ignore()
        else:
            event.accept()
