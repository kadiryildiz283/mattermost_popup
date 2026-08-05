import os
import subprocess
from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QApplication, QMessageBox
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPen, QPainterPath
from PySide6.QtCore import Signal, QObject
from src.autostart import AutoStartManager
from src.utils import get_resource_path

class SystemTrayApp(QObject):
    test_alert_requested = Signal()
    reconnect_requested = Signal()
    quit_requested = Signal()

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(self.create_default_icon(is_connected=False))
        self.tray_icon.setToolTip("Mattermost Emergency Client - Başlatılıyor...")

        self.create_menu()
        self.tray_icon.show()

    def create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #313244;
                color: #ffffff;
            }
            QMenu::item:checked {
                color: #00e676;
                font-weight: bold;
            }
        """)

        # Status item
        self.status_action = menu.addAction("🔴 Durum: Bağlantı Yok")
        self.status_action.setEnabled(False)

        menu.addSeparator()

        # Test Alert Action
        test_action = menu.addAction("🚨 Test Acil Uyarısı Aç")
        test_action.triggered.connect(self.on_test_alert)

        # Reconnect Action
        reconnect_action = menu.addAction("🔄 WebSocket Yeniden Bağlan")
        reconnect_action.triggered.connect(self.on_reconnect)

        menu.addSeparator()

        # Checkable Autostart Action
        self.autostart_action = menu.addAction("🚀 Başlangıçta Otomatik Çalıştır")
        self.autostart_action.setCheckable(True)
        is_auto = AutoStartManager.is_autostart_enabled()
        self.autostart_action.setChecked(is_auto)
        self.autostart_action.toggled.connect(self.on_autostart_toggled)

        # Config Edit Action
        config_action = menu.addAction("⚙️ Yapılandırma (config.json)")
        config_action.triggered.connect(self.on_open_config)

        menu.addSeparator()

        # Quit Action
        quit_action = menu.addAction("❌ Çıkış")
        quit_action.triggered.connect(self.on_quit)

        self.tray_icon.setContextMenu(menu)

    def set_connection_status(self, is_connected, status_text):
        if is_connected:
            self.tray_icon.setIcon(self.create_default_icon(is_connected=True))
            self.status_action.setText("🟢 Durum: Bağlandı")
            self.tray_icon.setToolTip(f"Mattermost Emergency Client\n{status_text}")
        else:
            self.tray_icon.setIcon(self.create_default_icon(is_connected=False))
            self.status_action.setText(f"🔴 Durum: {status_text}")
            self.tray_icon.setToolTip(f"Mattermost Emergency Client\n{status_text}")

    def create_default_icon(self, is_connected=True):
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(0, 0, 0, 0))

        logo_path = get_resource_path("albay-logo.png")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("albay-logo.jpg")

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        if os.path.exists(logo_path):
            logo_img = QPixmap(logo_path)
            path = QPainterPath()
            path.addEllipse(2, 2, 60, 60)
            painter.setClipPath(path)
            painter.drawPixmap(2, 2, 60, 60, logo_img)
            painter.setClipping(False)

            painter.setPen(QPen(QColor(0, 210, 255), 2))
            painter.drawEllipse(2, 2, 60, 60)
        else:
            bg_color = QColor(30, 30, 46)
            painter.setBrush(bg_color)
            painter.setPen(QColor(69, 71, 90))
            painter.drawEllipse(2, 2, 60, 60)

            font = QFont("Segoe UI", 24, QFont.Weight.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 50, 50))
            painter.drawText(pixmap.rect(), 0x0084, "🚨")

        dot_color = QColor(0, 230, 118) if is_connected else QColor(255, 23, 68)
        painter.setBrush(dot_color)
        painter.setPen(QPen(QColor(255, 255, 255), 1.5))
        painter.drawEllipse(42, 42, 18, 18)

        painter.end()
        return QIcon(pixmap)

    def on_autostart_toggled(self, checked):
        success = AutoStartManager.set_autostart(checked)
        if success:
            self.config.set("autostart_enabled", checked)
            status_str = "etkinleştirildi" if checked else "devre dışı bırakıldı"
            self.tray_icon.showMessage(
                "Başlangıç Ayarı Güncellendi",
                f"Uygulamanın bilgisayar açılışında otomatik çalışması {status_str}.",
                QSystemTrayIcon.Information,
                3000
            )

    def on_test_alert(self):
        self.test_alert_requested.emit()

    def on_reconnect(self):
        self.reconnect_requested.emit()

    def on_open_config(self):
        config_path = os.path.abspath(self.config.config_path)
        if not os.path.exists(config_path):
            self.config.save_config()

        try:
            if os.name == 'nt':
                os.startfile(config_path)
            else:
                subprocess.Popen(['xdg-open', config_path])
        except Exception as e:
            print(f"Primary open config failed: {e}. Trying editor fallback...")
            try:
                if os.name == 'nt':
                    subprocess.Popen(['notepad.exe', config_path])
                else:
                    subprocess.Popen(['nano', config_path])
            except Exception as ex:
                print(f"Fallback open config failed: {ex}")

    def on_quit(self):
        reply = QMessageBox.question(
            None,
            "Çıkış Onayı",
            "Uygulamayı kapatmak istediğinizden emin misiniz?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.quit_requested.emit()
            QApplication.quit()
