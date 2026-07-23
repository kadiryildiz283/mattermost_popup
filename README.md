# 🚨 Mattermost Emergency Client (Acil Uyarı Sistemi)

Mattermost sunucusunu **WebSocket API** üzerinden dinleyen, `/acil` komutu veya özel acil durum mesajları geldiğinde masaüstünde (Windows / Linux / macOS) yüksek öncelikli, ekranda en üstte kalan (`Always on Top`), sesli ve onay butonlu (`OKUDUM`) popup pencereleri açan kurumsal istemci uygulaması.

---

## 🎯 Öne Çıkan Özellikler

1. **Mattermost Dokunulmazlığı**: Mattermost sunucusunu fork etmeniz veya eklenti (plugin) yazmanız gerekmez. Yalnızca **Personal Access Token (PAT)** veya bot token'ı kullanır.
2. **WebSocket Dinleyici**: Tüm yeni mesajları `wss://` üzerinden anlık (0ms gecikme ile) yakalar. Kopmalarda otomatik olarak tekrar bağlanır (`Auto-Reconnect`).
3. **Masaüstü Popup (PySide6 / Qt)**:
   - Modern, yüksek çözünürlüklü ve şık arayüz.
   - Her zaman en üstte (`WindowStaysOnTopHint`).
   - Kullanıcı `[OKUDUM / ONAYLADIM]` butonuna basana kadar ekrandan gitmez ve `ESC` tuşu engellenir.
   - İsteğe bağlı Tam Ekran (`Fullscreen`) modu.
4. **Otomatik Okundu (ACK) Bildirimi**: Kullanıcı popup üzerindeki `OKUDUM` butonuna bastığında, Mattermost kanalına otomatik yanıt atar:
   > `✅ Kadir Yılmaz acil durumu gördü ve onayladı: Yangın Alarmı`
5. **Ses Seviyeleri (Priority Audio)**:
   - `normal`: Bilgilendirme sesi (`ding.wav`)
   - `warning`: Uyarı ikazı (`warning.wav`)
   - `critical`: Kritik siren alarmı (`siren.wav`)
   - `disaster`: Yüksek tonlu afet ikazı (`airraid.wav`)
6. **Sistem Tepsi (System Tray) Desteği**:
   - Arka planda sessizce çalışır.
   - **RAM**: ~25-40 MB | **CPU**: %0.

---

## 📁 Proje Yapısı

```
mattermost_popup/
├── config.json                 # Sunucu URL, PAT Token ve ses ayarları
├── main.py                     # Ana uygulama başlatıcı (System Tray + WebSocket + Qt)
├── audio_generator.py          # Yerleşik varsayılan alarm seslerini üreten modül
├── build_exe.py                # PyInstaller ile tek tıkla .exe derleme betiği
├── requirements.txt            # Python bağımlılıkları (PySide6, websocket-client, requests)
├── sounds/                     # Alarm WAV ses dosyaları
│   ├── ding.wav
│   ├── warning.wav
│   ├── siren.wav
│   └── airraid.wav
└── src/
    ├── config.py               # Yapılandırma yöneticisi
    ├── api_client.py           # REST API istemcisi (OKUDUM yanıtı göndermek için)
    ├── sound_manager.py        # Qt QSoundEffect tabanlı ses oynatıcı
    ├── websocket_client.py     # Otomatik bağlantı yenilemeli WebSocket dinleyicisi
    └── ui/
        ├── emergency_window.py # Acil durum popup penceresi (Qt)
        └── system_tray.py      # Arka plan tepsi simgesi ve sağ tık menüsü
```

---

## 🚀 Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 2. Yapılandırma (`config.json`)

`config.json` dosyasını açıp kendi Mattermost sunucu bilgilerinizi yazın:

```json
{
  "server_url": "https://mattermost.sirketiniz.com",
  "pat_token": "SİZİN_PERSONAL_ACCESS_TOKEN_BİLGİNİZ",
  "trigger_prefixes": ["/acil", "[ACIL]", "[URGENT]", "[EMERGENCY]"],
  "channels": ["*"],
  "audio_enabled": true,
  "audio_loop": true,
  "auto_post_ack": true,
  "ack_message_template": "✅ **{user_display_name}** ({username}) acil durumu gördü ve onayladı: **{title}**",
  "window_always_on_top": true,
  "disable_esc_key": true,
  "fullscreen_for_critical": false
}
```

> **Personal Access Token (PAT) Nasıl Alınır?**  
> Mattermost -> Account Settings -> Security -> Personal Access Tokens -> Save Token.

### 3. Uygulamayı Başlatın

```bash
python main.py
```

### 4. Test Modunda Çalıştırma

WebSocket bağlantısı olmadan popup ve ses testini hemen görmek için:

```bash
python main.py --test
```

---

## 📩 Tetikleme Örnekleri (Mattermost Mesajları)

### Yöntem A: Düz Metin / Komut Kullanımı

Mattermost'ta herhangi bir kanala veya `/acil` ile başlayan bir mesaj yazmanız yeterlidir:

```
/acil Sunucu Odası Yangın Alarmı: Duman algılandı, lütfen bina tahliye planını uygulayın!
```

veya

```
[ACIL] Sistem Çökmesi: Ana veritabanı erişilemez durumda!
```

---

### Yöntem B: Yapılandırılmış JSON Mesajı

Daha fazla detay ve öncelik seviyesi belirtmek isterseniz mesaj alanına JSON yazabilirsiniz:

```json
{
  "priority": "critical",
  "title": "Yangın Alarmı",
  "message": "Sunucu odasında duman ve yüksek sıcaklık algılandı.",
  "sender": "Sistem Alarm Botu"
}
```

Öncelik seviyeleri (`priority`):
- `normal` -> Mavi tema, ding sesi
- `warning` -> Sarı/Turuncu tema, ikaz sesi
- `critical` -> Kırmızı tema, siren sesi (Döngüsel çalar)
- `disaster` -> Derin Mor/Kırmızı tema, ağır afet ikaz sesi (Döngüsel çalar)

---

## 📦 Windows için Tek Parça (`.exe`) Dağıtımı Paketleme

Uygulama, klasör veya zip gerektirmeden **tek bir bağımsız `.exe` dosyası** (`--onefile`) olarak derlenmektedir:

```bash
python build_exe.py
```

- Derlenen uygulama doğrudan `dist/MattermostEmergencyClient.exe` dosyası olarak üretilir.
- GitHub Actions üzerinde build tamamlandığında doğrudan indirilebilir tek parça `.exe` olarak yayınlanır.
- `albay-logo.jpg` görseli otomatik olarak yüksek çözünürlüklü `.ico` simgesine dönüştürülüp masaüstü kısayolu, Windows görev çubuğu, sistem tepsi (System Tray) simgesi ve acil durum başlıklarında kullanılır.
- Windows başlangıcına (Startup folder: `shell:startup`) ekleyerek PC açılışında otomatik çalışmasını sağlayabilirsiniz.
