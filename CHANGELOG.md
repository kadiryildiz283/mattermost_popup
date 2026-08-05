# 📋 Değişiklik Günlüğü (Changelog) - Mattermost Emergency Client

Bu dosyada `~/Projeler/mattermost_popup` projesinde gerçekleştirilen en son güncellemeler, tasarım kararları ve mimari değişiklikler kayıt altına alınmaktadır.

---

## 🚀 [2.1.0] - 2026-08-05

### 🎯 Eklenen & Güncellenen Özellikler

#### 1. Yönetici (Admin) Yetkisi ve Otomatik Başlatma Mantığı (`src/autostart.py`, `main.py`)
* **Task Scheduler Entegrasyonu:** Windows başlangıcında uygulamanın yüksek yetkilerle (`/rl highest`) ve varsayılan olarak başlatılması sağlandı.
* **Şirket İçi Kullanıcı Koruması (Sıfır UAC Uyarısı):**
  * Uygulamanın her çalışmasında Admin şifresi sorması (**UAC Prompt**) engellendi.
  * Kurulum/ilk yapılandırma Admin yetkisiyle 1 defa yapıldıktan sonra, şirket çalışanları bilgisayarlarını açtığında veya uygulamaya tıkladığında **hiçbir admin şifresi girmeden** uygulama arka planda sorunsuz çalışır.
* **Yedekleme Mekanizmaları:** Windows `shell:startup` klasörü kısayol entegrasyonu ve `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` Registry yedekleme kayıtları aktif tutuldu.

#### 2. Uygulama Kapalı / Kullanıcı İnaktifken: Merkezi Apple macOS Modal Popup (`src/ui/emergency_window.py`)
* **Akrilik Cam (Dark Glassmorphism) Arayüz:** Apple macOS tasarım çizgileri entegre edilerek `rgba(28, 28, 34, 0.95)` koyu transparan cam teması, yumuşatılmış 18px köşe yuvarlatmaları ve akıcı tipografi uygulandı.
* **Tam Ekran / Merkez Konumlandırma:** Uygulama kapalı veya kullanıcı çevrimdışıyken gelen tüm mesajlar ekranın ortasında yüksek öncelikli modal olarak görüntülenir.
* **Kilitli Onay Mekanizması:** Kullanıcı `✓ Okudum / Anladım` butonuna basana kadar pencere ekrandan gitmez ve onay yanıtını Mattermost kanalına iletir.

#### 3. Uygulama Açık / Kullanıcı Aktifken: Sağ Alt Köşe Kalıcı Apple Bildirim Kartı (`src/ui/tray_banner.py`)
* **Yeni UI Modülü (`AppleTrayBanner`):** Kullanıcı aktifken veya Mattermost uygulaması açıkken gelen mesajlar için ekranın sağ alt köşesinde (sistem tepsisi ikonlarının hemen üstünde) beliren özel bildirim widget'ı oluşturuldu.
* **Kibar & Minimalist Boyut (`360x150 px`):** Apple macOS Notification Banner stili, mini uygulama logosu, kanal adı, zaman damgası ve mesaj özeti.
* **Kalıcı (Persistent) Yapı:** Bildirim kendiliğinden kaybolmaz; kullanıcının `✕` butonuna basması gerekir.

#### 4. Akıllı Mesaj Yönlendirme (Router) (`src/websocket_client.py`, `main.py`)
* WebSocket üzerinden gelen mesajın anlık aktiflik durumuna göre yönlendirilmesi sağlandı:
  * Kullanıcı Aktif / Mattermost Açık ➔ **Sağ Alt Köşe Kalıcı Apple Bildirimi**
  * Kullanıcı İnaktif / Mattermost Kapalı ➔ **Ekran Ortası Merkezi Apple Modal Popup**

#### 5. GitHub Actions & Otomatik Windows Build (`.github/workflows/build.yml`)
* Yapılan değişiklikler otomatik test edilip `origin/main` dalına pushlandı.
* GitHub Actions CI/CD iş akışı üzerinden tek tıkla indirilebilir `.exe` (`MattermostEmergencyClient-Windows.exe`) çıktısı üretilmektedir.

---

### 📁 Değiştirilen ve Eklenen Dosyalar
* [`main.py`](file:///home/kadir/Projeler/mattermost_popup/main.py): Uygulama başlatıcı ve mesaj yönlendirme mantığı güncellendi.
* [`src/autostart.py`](file:///home/kadir/Projeler/mattermost_popup/src/autostart.py): Task Scheduler yetki yapılandırması ve kullanıcı UAC koruması eklendi.
* [`src/websocket_client.py`](file:///home/kadir/Projeler/mattermost_popup/src/websocket_client.py): `is_app_open` durum tespiti ve sinyal yönlendirmesi eklendi.
* [`src/ui/emergency_window.py`](file:///home/kadir/Projeler/mattermost_popup/src/ui/emergency_window.py): Merkezi Apple macOS modal tasarımı uygulandı.
* [`src/ui/tray_banner.py`](file:///home/kadir/Projeler/mattermost_popup/src/ui/tray_banner.py): Sağ alt köşe kalıcı Apple notification banner modülü yazıldı.
* [`src/ui/system_tray.py`](file:///home/kadir/Projeler/mattermost_popup/src/ui/system_tray.py): Çıkış onayındaki gereksiz admin kısıtlamaları kaldırıldı.
