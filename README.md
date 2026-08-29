# Fadimrak Steam Tool

Fadimrak Steam Tool, Steam istemcisi icin gelistirilmis kapsamli bir kutuphane, basarim, DLC ve hesap yonetim aracidir. Python tabanli asenkron arka plan mimarisi ve PyWebView destekli modern arayuzu ile kullanicilara hizli ve moduler bir deneyim sunar.

---

## Ozellikler

- **Oyun ve Manifest Yonetimi:** ManifestHub kaynaklari uzerinden secilen oyunlarin depot ve manifest yapilandirmalarini otomatik olarak cozumler ve kutuphaneye entegre eder.
- **DLC Unlocker Entegrasyonu:** SmokeAPI, ScreamAPI ve Koaloader yapilandirmalarini otomatik olarak algilar, oyun dizinlerine uygular ve yonetir.
- **Steam Basarim Yoneticisi (SAM):** `steam_api64.dll` uzerinden Steamworks API ile dogrudan iletisim kurarak oyun basarimlarini ve istatistiklerini goruntuleme, tek tek veya toplu olarak acma/kilitleme imkani saglar.
- **Kart ve Saat Kasici (Idle Farmer):** Arka planda calisan izole alt surecler (subprocess) uzerinden oyunlari calistirmadan takas karti dusurme ve oyun suresi kasma islemlerini yonetir. Sistem tepsisi (System Tray) destegiyle arka planda sessizce calisabilir.
- **Online-Fix Entegrasyonu:** Desteklenen oyunlar icin multiplayer ve network bypass yamalarini otomatik indirip oyun dizinlerine konumlandirir.
- **Coklu Hesap Yoneticisi:** Sistemde kayitli Steam hesaplari arasinda hizli gecis yapilmasini saglar.
- **Modern Web Arayuzu:** Chromium / Edge-WebView2 motoru uzerinde calisan, donanim hizlandirmali ve asenkron IPC koprusu ile iletisim kuran responsive UI.

---

## Mimari ve Calisma Mantigi

Uygulama iki ana katmandan olusur:

1. **Frontend (Arayuz):** PyWebView uzerinde calisan HTML, CSS ve JavaScript tabanli arayuz. Backend ile asenkron REST/JS API koprusu (`ui_web/bridge.py`) uzerinden iletisim kurar.
2. **Backend & Core Motoru:**
   - `core/installer.py`: Manifest indirme, arsiv acma ve dosya yonetimi.
   - `core/achievement_manager.py`: Steamworks API entegrasyonu ile basarim yonetimi.
   - `core/idle_farmer.py`: Ctypes ve subprocess tabanli idle farming motoru.
   - `core/dlc_unlocker.py`: SmokeAPI / ScreamAPI konfigurasyon uretimi.
   - `core/onlinefix.py`: Online fix arsiv yonetimi ve dosya patchleme.
   - `core/steam_account.py`: VDF ve registry tabanli hesap tespit/degistirme modulu.
   - `core/tray_manager.py`: Windows System Tray bildirim ve arka plan calisma yoneticisi.

---

## Kurulum ve Kaynak Koddan Calistirma

### Gereksinimler

- Windows 10 veya Windows 11 (x64)
- Python 3.10 veya daha yeni bir surum
- Steam istemcisi

### Adimlar

1. Depoyu klonlayin:
```bash
git clone https://github.com/fadimrak/fadimraksteamtool.git
cd fadimraksteamtool
```

2. Gerekli Python paketlerini yukleyin:
```bash
pip install -r requirements.txt
```

3. Uygulamayi baslatin:
```bash
python main.py
```

---

## Derleme (Build & Packaging)

Projeyi tek bir bagimsiz `.exe` dosyasina veya Inno Setup kurulum paketine donusturmek icin hazir derleme scripti bulunmaktadir.

### Gereksinimler

- `pyinstaller`
- Inno Setup 6 (Opsiyonel, Setup dosyasi olusturmak icin)

### Derleme Islemi

`build.bat` dosyasini calistirarak otomatik derleme surecini baslatabilirsiniz:

```bat
build.bat
```

Script su adimlari otomatik olarak gerceklestirir:
1. Gerekli bagimliliklari kontrol eder.
2. `fadimrak.spec` dosyasini kullanarak `dist/FadimrakSteamTool.exe` ciktisini olusturur.
3. Sistemde Inno Setup kuruluysa `installer.iss` dosyasini derleyerek `output/` dizininde kurulum paketini hazirlar.

---

## Proje Yapisi

```text
fadimraksteamtool/
├── core/
│   ├── achievement_manager.py  # Basarim yonetimi ve Steamworks entegrasyonu
│   ├── dlc_unlocker.py         # DLC unlocker yapilandirma modulu
│   ├── game_manager.py         # Yuklu oyunlarin kayit ve durumu
│   ├── idle_farmer.py          # Kart dusurme ve sure kasma motoru
│   ├── installer.py            # Manifest indirme ve kurulum servisi
│   ├── onlinefix.py            # Multiplayer yama entegrasyonu
│   ├── steam_account.py        # Steam hesap yoneticisi
│   ├── steam_utils.py          # Steam dizin ve surec araclari
│   └── tray_manager.py         # Sistem tepsisi (Tray) yonetimi
├── ui_web/
│   ├── bridge.py               # Python - JS haberlesme koprusu
│   ├── window.py               # PyWebView pencere yapilandirmasi
│   └── static/                 # Frontend arayuz dosyalari (HTML/CSS/JS/Assets)
├── build.bat                   # Otomatik derleme scripti
├── config.py                   # Uygulama genel yapilandirmasi
├── fadimrak.spec               # PyInstaller spec tanimi
├── installer.iss               # Inno Setup yukleyici tanimi
├── main.py                     # Uygulama giris noktasi
├── requirements.txt            # Python bagimliliklari
├── steam_api.py                # Steam Web API ve liste yoneticisi
├── steam_api64.dll             # Steamworks 64-bit API kutuphanesi
└── verison                     # Surum bilgisi
```

---

## Sorumluluk Reddi (Disclaimer)

Bu yazilim yalnizca egitim, tersine muhendislik analizleri, API calisma prensiplerinin incelenmesi ve guvenlik arastirmalari amaciyla gelistirilmistir. Yazilimin amaci disinda kullanimindan kaynaklanabilecek hesap kisitlamalari (VAC/Game Ban) veya diger sorumluluklar kullaniciya aittir. Orijinal oyun ve yazilim gelistiricilerini desteklemek icin lisansli urunleri tercih ediniz.

---

## Lisans

Bu proje GNU General Public License v3.0 (GPL-3.0) kapsaminda lisanslanmistir. Ayrintilar icin `LICENSE` dosyasini inceleyebilirsiniz.
