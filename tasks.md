# Implementation Plan: Denuvo / DRM Simülasyon Modülü

## Overview

Bu plan, `fadimraksteamtool` uygulamasına Denuvo / DRM simülasyon modülünü ekler. Uygulama sırası şöyledir: önce motor katmanı (`core/drm_engine.py`) oluşturulur, ardından köprü katmanı (`bridge.py`) genişletilir, son olarak ön yüz bileşenleri (`index.html`, `drm.js`, `style.css`) entegre edilir.

## Tasks

- [ ] 1. Motor Katmanı: Temel Veri Yapıları ve HWID Alt Sistemi
  - [ ] 1.1 `core/drm_engine.py` dosyasını oluştur — sabitler, yardımcı fonksiyonlar ve HWID alt sistemi
    - `TOKEN_SECRET` ve `DEFAULT_TTL` sabitlerini tanımla
    - Windows için `wmic` komutu, Linux için `/proc/cpuinfo` kullanan `_read_cpu_serial()` fonksiyonunu yaz; okunamazsa `"UNKNOWN"` döndür
    - `wmic diskdrive` veya `lsblk` kullanan `_read_disk_serial()` fonksiyonunu yaz; okunamazsa `"UNKNOWN"` döndür
    - `uuid.getnode()` kullanan `_read_mac_address()` fonksiyonunu yaz; okunamazsa `"UNKNOWN"` döndür
    - `cpu + disk + mac` birleşimini SHA-256 ile 64 karakterlik onaltılık dizeye dönüştüren **saf** `compute_hwid(cpu, disk, mac)` fonksiyonunu yaz
    - `_read_*()` fonksiyonlarını çağırıp `compute_hwid()`'e ileten `derive_hwid()` fonksiyonunu yaz
    - `hwid[:8] + "..." + hwid[-8:]` formatında döndüren `mask_hwid(hwid)` yardımcısını yaz
    - `max(0, expires_at - int(time.time()))` döndüren `get_remaining_ttl(expires_at)` yardımcısını yaz
    - _Gereksinimler: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 6.1_

  - [ ]* 1.2 `compute_hwid` için özellik testi yaz
    - **Özellik 1: HWID Hesaplama Deterministik ve Biçim Uyumludur** — `st.text()` üçlüsü; aynı girdi her seferinde 64 char hex döndürmeli
    - **Özellik 2: HWID Ham Girdi İçermez** — `st.text()` üçlüsü; çıktı `cpu`, `disk`, `mac` ham değerlerinin hiçbirini içermemeli
    - **Özellik 10: HWID Maskeleme Biçimi** — `st.from_regex(r'[0-9a-f]{64}')` → `mask_hwid` çıktısı `hwid[:8] + "..." + hwid[-8:]` olmalı
    - **Validates: Gereksinimler 2.3, 2.4, 2.6, 6.1**

- [ ] 2. Motor Katmanı: Jeton Üretimi ve Doğrulama
  - [ ] 2.1 `generate_token(hwid, ttl)` fonksiyonunu yaz
    - HWID'i `r'[0-9a-f]{64}'` regex ile doğrula; eşleşmiyorsa `{"ok": False, "error": "Geçersiz HWID biçimi: 64 onaltılık karakter bekleniyor"}` döndür
    - `session_id = uuid.uuid4().hex`, `issued_at = int(time.time())`, `expires_at = issued_at + ttl` hesapla
    - `HMAC-SHA256(hwid + session_id + str(issued_at), TOKEN_SECRET)` ile `signature` üret
    - Başarıda `{"ok": True, "session_id", "hwid", "issued_at", "expires_at", "signature"}` döndür
    - _Gereksinimler: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ] 2.2 `verify_token(token_payload, client_hwid)` fonksiyonunu yaz
    - Önce TTL denetle: `int(time.time()) > expires_at` → `{"ok": False, "error": "Jeton süresi doldu"}`
    - Sonra HWID denetle: `token_payload["hwid"] != client_hwid` → `{"ok": False, "error": "Donanım uyuşmazlığı"}`
    - Son olarak HMAC denetle: yeniden hesaplanan imza eşleşmiyorsa → `{"ok": False, "error": "Geçersiz jeton imzası"}`
    - Başarıda `{"ok": True, "session_id": ..., "remaining_ttl": ...}` döndür
    - _Gereksinimler: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 2.3 `generate_token` ve `verify_token` için özellik testleri yaz
    - **Özellik 3: Jeton İmzası Doğrulanabilir** — `st.from_regex(r'[0-9a-f]{64}')` HWID + `st.integers(min_value=60)` TTL; üretilen imza yeniden hesaplamayla eşleşmeli
    - **Özellik 4: Session ID'ler Benzersizdir** — İki ardışık `generate_token` çağrısı; `session_id` değerleri farklı olmalı
    - **Özellik 5: Geçersiz HWID Reddedilir** — `st.text()` için `[0-9a-f]{64}` dışındaki her string `ok: False` döndürmeli
    - **Özellik 6: HWID Uyuşmazlığı Reddedilir** — İki farklı geçerli HWID; çapraz doğrulama `{"ok": False, "error": "Donanım uyuşmazlığı"}` döndürmeli
    - **Özellik 7: Kalan TTL Doğru Hesaplanır** — `st.integers(min_value=1, max_value=7200)` TTL; `get_remaining_ttl` `t - e` döndürmeli (±1s tolerans)
    - **Validates: Gereksinimler 3.2, 3.3, 3.5, 4.5, 4.7**

- [ ] 3. Motor Katmanı: DRMSession ve DRMLogger Sınıfları
  - [ ] 3.1 Thread-safe `DRMSession` sınıfını yaz
    - `threading.Lock()` ile iş parçacığı güvenliği sağla
    - `start(token_payload)`, `end()` metodlarını; `is_active` property'sini; `info` property'sini (`session_id`, `hwid_masked`, `expires_at`, `remaining_ttl`) uygula
    - `refresh_ttl()`: kalan saniyeyi döndür; 0 ise `end()` çağır
    - Kalıcı depolama YOKTUR — tüm durum yalnızca bellekte tutulur
    - _Gereksinimler: 4.7, 6.1, 6.2, 6.3, 6.4, 8.5_

  - [ ] 3.2 `DRMLogger` sınıfını yaz
    - `MAX_ENTRIES = 100` olan FIFO `collections.deque` tamponu kullan
    - `add(event_type, message, session_id)`: ISO 8601 zaman damgalı `LogEntry` dict oluştur, tampona ekle, 101. girişte en eskiyi sil
    - `clear()`, `entries()` metodlarını uygula
    - `css_class(event_type)` statik metodunu uygula: `"success" → "log-success"`, `"error" → "log-error"`, `"info" → "log-info"`, bilinmeyen → `"log-info"`
    - _Gereksinimler: 7.1, 7.2, 7.3, 7.5, 7.6_

  - [ ]* 3.3 `DRMSession` ve `DRMLogger` için özellik ve birim testleri yaz
    - **Özellik 11: Günlük Kapasitesi Aşılmaz** — `st.integers(min_value=1, max_value=200)` N girdi ekle; `len(entries()) == min(N, 100)` olmalı
    - **Özellik 12: Olay Türüne Göre CSS Sınıfı** — `st.sampled_from(["success","error","info","unknown"])` → doğru css_class döndürmeli
    - `DRMSession.start/end/is_active` durum geçişleri için birim testi yaz
    - **Validates: Gereksinimler 7.1, 7.3, 7.5**

- [ ] 4. Kontrol Noktası — Motor Katmanını Doğrula
  - Tüm testlerin geçtiğini doğrula, sorularınız varsa kullanıcıya sorun.

- [ ] 5. Köprü Katmanı: DRM API Metodları
  - [ ] 5.1 `bridge.py`'deki `API` sınıfına DRM modülü import'u ve singleton'larını ekle
    - `from core import drm_engine` import'u ekle
    - `__init__` içinde `self._drm_session = drm_engine.DRMSession()` ve `self._drm_logger = drm_engine.DRMLogger()` oluştur
    - _Gereksinimler: 8.1, 8.5_

  - [ ] 5.2 `drm_start_flow()`, `drm_get_status()`, `drm_end_session()` public metodlarını yaz
    - `drm_start_flow()`: açık oturum varsa önce `_drm_session.end()` çağır; yeni daemon thread'de `_drm_flow_thread()` başlat; hemen `{"ok": True}` döndür
    - `drm_get_status()`: `{"active": self._drm_session.is_active, "info": self._drm_session.info}` senkron döndür
    - `drm_end_session()`: `_drm_session.end()` çağır; `self._push("drm_session_ended", {})` push et; `{"ok": True}` döndür
    - _Gereksinimler: 8.1, 8.2, 8.3, 6.2, 6.5_

  - [ ] 5.3 `_drm_flow_thread()` ve `_drm_push_log()` özel metodlarını yaz
    - `_drm_flow_thread()`: üç adımı (`hwid`, `token`, `verify`) sırasıyla çalıştır; her adım öncesi `elapsed_ms` ölçümü başlat; her adım sonrası `drm_step_update` eventi push et; adım başarısız olursa sonraki adımı atlayarak dur
    - Her adım tamamlandıktan sonra logger'a kayıt ekle ve `_drm_push_log()` ile JS'e ilet
    - Tüm akış başarıyla tamamlandığında `drm_flow_done` push et; `_drm_session.start(token_payload)` çağır; TTL ticker thread'ini başlat
    - Beklenmedik istisna varsa `drm_error` push et
    - `_drm_push_log(entry)`: `self._push("drm_log_entry", entry)` çağır
    - _Gereksinimler: 5.1, 5.2, 5.3, 5.4, 5.5, 8.2, 8.3, 8.4_

  - [ ] 5.4 TTL ticker yardımcısını (`_drm_ttl_ticker_thread`) yaz
    - `_drm_session.is_active` olduğu sürece her saniye `_drm_session.refresh_ttl()` çağır
    - Sonucu `drm_ttl_tick` eventi ile push et: `{"remaining_ttl": int}`
    - TTL 0'a ulaşınca logger'a `"info"` kaydı ekle ve `drm_session_ended` push et
    - _Gereksinimler: 6.3, 6.7_

  - [ ]* 5.5 Bridge entegrasyon testleri yaz
    - Mock `_push` ile `drm_start_flow → drm_get_status → drm_end_session` tam akışını doğrula
    - Bridge metodlarının `daemon=True` thread başlattığını doğrula
    - Oturum verisinin `tsc_settings.json`'a yazılmadığını doğrula
    - **Özellik 8: Akış Fail-Fast Davranışı** — `i`. adımda hata oluşunca `i+1` ve sonraki adımların çalışmadığını doğrula
    - **Özellik 9: Adım Süresi Negatif Olamaz** — her `StepResult`'ta `elapsed_ms >= 0` olmalı
    - **Validates: Gereksinimler 5.3, 5.5, 8.3, 8.5**

- [ ] 6. Kontrol Noktası — Köprü Katmanını Doğrula
  - Tüm testlerin geçtiğini doğrula, sorularınız varsa kullanıcıya sorun.

- [ ] 7. Ön Yüz: CSS Genişletmesi
  - [ ] 7.1 `ui_web/static/css/style.css` dosyasına DRM modülü CSS kurallarını ekle
    - Adım kartları için `.drm-step-card`, `.drm-step-header`, `.drm-step-icon`, `.drm-step-body` stillerini yaz; `--bg2`, `--border`, `--radius` değişkenlerini kullan
    - Adım durumu renklendirmesi: `.drm-step-card.ok { border-left: 3px solid var(--success); }`, `.drm-step-card.error { border-left: 3px solid var(--danger); }`, `.drm-step-card.running { border-left: 3px solid var(--warn); }`
    - Oturum bilgi paneli için `.drm-session-panel`, `.drm-session-row`, `.drm-session-val` stillerini yaz
    - Olay günlüğü için `.drm-log-list`, `.drm-log-entry`, `.drm-log-entry.log-success`, `.drm-log-entry.log-error`, `.drm-log-entry.log-info` stillerini yaz
    - `.drm-ttl-bar` ve `.drm-ttl-fill` ile TTL geri sayım çubuğu stillerini yaz
    - _Gereksinimler: 9.1, 9.3, 9.4_

- [ ] 8. Ön Yüz: HTML — Sidebar ve page-drm Bölümü
  - [ ] 8.1 `index.html` sidebar'ına "Denuvo / DRM" navigasyon öğesini ekle
    - `page-account` butonunun hemen üstüne `data-page="drm"` olan `<button class="nav-item">` ekle
    - `src="drm.png"` olan `nav-icon` img ve `data-i18n="nav.drm"` span içer
    - _Gereksinimler: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 8.2 `index.html` içine `id="page-drm"` olan `<section class="page">` bölümünü ekle
    - **Bilgi Notu**: `info-callout` bileşeniyle tez amacı açıklaması; `data-i18n="drm.info_note"` attribute
    - **Akış Paneli**: `page-header` içinde "Denuvo / DRM Simülasyonu" başlığı ve `id="drm-start-btn"` olan "Doğrulamayı Başlat" butonu
    - Üç adım kartı: `id="drm-step-hwid"`, `id="drm-step-token"`, `id="drm-step-verify"`; her kart `.drm-step-card` sınıfı, başlık alanı ve `id="drm-detail-hwid"` vb. detay alanı içermeli
    - **Oturum Paneli**: `id="drm-session-panel"` ile `hidden` sınıflı; `session_id`, maskeli HWID, TTL çubuğu ve kalan süre, "Oturumu Kapat" butonu (`id="drm-end-btn"`) alanları içermeli
    - **Olay Günlüğü**: `id="drm-log-section"`; başlığı, "Günlüğü Temizle" butonu (`id="drm-clear-log-btn"`) ve `id="drm-log-list"` liste konteyneri içermeli
    - _Gereksinimler: 1.3, 5.2, 6.1, 7.2, 9.2, 9.5, 9.6_

- [ ] 9. Ön Yüz: JavaScript — drm.js
  - [ ] 9.1 `ui_web/static/js/drm.js` dosyasını oluştur — başlatma ve buton işleyicileri
    - `drmInit()`: sayfa ilk aktif olduğunda çağrılır; `drm_get_status` ile mevcut durumu yükler; eğer oturum aktifse paneli göster
    - `drmStartFlow()`: `drm-start-btn`'ı devre dışı bırak; adım kartlarını "pending" durumuna sıfırla; `pywebview.api.drm_start_flow()` çağır
    - `drmEndSession()`: `pywebview.api.drm_end_session()` çağır
    - `drmClearLog()`: `pywebview.api` üzerinden logger'ı temizle veya sadece DOM'dan log girişlerini sil; `drm-log-list` içeriğini boşalt
    - _Gereksinimler: 5.1, 6.2, 7.4, 8.1_

  - [ ] 9.2 `onPythonEvent` olay işleyicilerini yaz ve `core.js` ile bağla
    - `_drmOnStepUpdate(data)`: ilgili `drm-step-{step}` kartını güncelle; duruma göre `ok`/`error`/`running` sınıfı uygula; spin göstergesini göster/gizle; `elapsed_ms` değerini kart üzerinde göster; `detail` metnini yaz
    - `_drmOnFlowDone(data)`: `drm-start-btn`'ı yeniden etkinleştir; oturum panelini (`drm-session-panel`) görünür yap; `session_id`, maskeli HWID alanlarını doldur
    - `_drmOnSessionEnded()`: oturum panelini gizle; adım kartlarını sıfırla; "Doğrulamayı Başlat" butonunu yeniden etkinleştir
    - `_drmOnTtlTick(data)`: TTL çubuğunu ve kalan süre metnini güncelle; TTL 0 olunca uyarı tostu göster
    - `_drmOnLogEntry(data)`: `drm-log-list` başına yeni log satırı ekle; `css_class` ile renklendirme uygula; 100 girdide en eski satırı DOM'dan sil
    - `_drmOnError(data)`: `toast('error', ...)` göster; "Doğrulamayı Başlat" butonunu yeniden etkinleştir; log listesine kırmızı hata girişi ekle
    - `core.js`'teki `window.onPythonEvent` switch bloğuna tüm `drm_*` olay dallarını ekle
    - `core.js`'teki `navigateTo` fonksiyonuna `if (page === 'drm') drmInit()` satırını ekle
    - _Gereksinimler: 5.2, 5.3, 5.4, 5.5, 5.6, 6.1, 6.3, 7.2, 7.5, 8.2, 9.3, 9.4_

  - [ ] 9.3 `index.html` script bloğuna `drm.js` referansını ekle
    - `<script src="js/drm.js"></script>` satırını mevcut script taglarının sonuna ekle
    - _Gereksinimler: 8.1_

- [ ] 10. Son Kontrol Noktası — Tüm Bütünleşmeyi Doğrula
  - Tüm testlerin geçtiğini doğrula; manual smoke test senaryolarını çalıştır (sidebar görünürlüğü, adım kartı animasyonları, TTL geri sayımı, Günlük Temizle butonu), sorularınız varsa kullanıcıya sorun.

## Notes

- `*` ile işaretli görevler isteğe bağlıdır; hızlı MVP için atlanabilir
- Her görev, izlenebilirlik için ilgili gereksinimlere atıfta bulunur
- Kontrol noktaları artımlı doğrulama sağlar
- Özellik testleri `hypothesis` kütüphanesi ile en az 100 iterasyon çalıştırılır
- Birim testleri belirli örnekleri ve sınır durumları doğrular
- `DRMSession` hiçbir zaman `tsc_settings.json`'a veri yazmaz; tüm oturum durumu yalnızca bellekte tutulur
- HWID türetmesi `subprocess` / `wmic` ile gerçekleştirildiğinden Windows ve Linux davranışları farklı olabilir; `"UNKNOWN"` yer tutucusu her zaman güvenli geri dönüş sağlar
- `drm.png` adlı bir ikon dosyası sidebar'da kullanılacaktır; mevcut yoksa uygun bir ikon eklenmelidir

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "2.1"] },
    { "id": 2, "tasks": ["2.2", "2.3"] },
    { "id": 3, "tasks": ["3.1", "3.2"] },
    { "id": 4, "tasks": ["3.3", "5.1"] },
    { "id": 5, "tasks": ["5.2"] },
    { "id": 6, "tasks": ["5.3"] },
    { "id": 7, "tasks": ["5.4", "7.1"] },
    { "id": 8, "tasks": ["5.5", "8.1", "8.2"] },
    { "id": 9, "tasks": ["9.1"] },
    { "id": 10, "tasks": ["9.2"] },
    { "id": 11, "tasks": ["9.3"] }
  ]
}
```
