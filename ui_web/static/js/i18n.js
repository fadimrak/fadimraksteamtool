/**
 * Internationalization (i18n) Engine for Fadimrak Steam Tool
 * Supports English ('en') and Turkish ('tr')
 */

const I18N = {
  tr: {
    // ── Navigation & Sidebar ──
    'nav.library': 'Kütüphane',
    'nav.add_game': 'Oyun Ekle',
    'nav.onlinefix': 'Online Fix',
    'nav.sam': 'Başarımlar',
    'nav.idle': 'Kart & Saat Kasma',
    'nav.dlc': 'DLC Unlocker',
    'nav.account': 'Steam Hesabı',
    'nav.settings': 'Ayarlar',
    'nav.restart_steam': "Steam'i Yeniden Başlat",
    'nav.minimize_tray': "Tray'e Küçült",
    'nav.dll_checking': 'DLL Kontrol…',
    'nav.dll_active': 'DLL Aktif',
    'nav.dll_missing': 'DLL Eksik',
    'nav.steam_missing': 'Steam Yok',

    // ── Splash & Update ──
    'splash.credits': 'fadimrak tarafından yapılmıştır. İyi kullanımlar!',
    'update.banner': 'Yeni bir sürüm mevcut!',
    'update.download': 'İndir',

    // ── Library ──
    'library.title': 'Kütüphane',
    'library.search_placeholder': 'Kütüphanede ara…',
    'library.restart_btn': "↺ Steam'i Yeniden Başlat",
    'library.guide_title': 'Kütüphane Kullanım Rehberi',
    'library.guide_desc': 'Eklediğiniz oyunlar Steam istemcinize otomatik olarak bağlanır. Oyun kartlarına tıklayarak başarımlarını yönetebilir, sağ tıklayarak SteamDB sayfasına gidebilir veya App ID kopyalayabilirsiniz.',
    'library.empty_title': 'Henüz oyun eklenmedi',
    'library.empty_desc': 'Oyun Ekle sekmesinden mağazayı arayarak veya dosya yükleyerek ekleyebilirsiniz.',
    'library.add_btn': 'Oyun Ekle →',
    'library.remove_btn': 'Kaldır',
    'library.count': '{count} oyun',
    'library.confirm_remove_title': 'Oyunu Kaldır',
    'library.confirm_remove_msg': '"{name}" Steam kütüphanenizden ve yerel yapılandırmadan kaldırılacak.',
    'library.toast_removed': 'Oyun Kaldırıldı',

    // ── Add Game ──
    'add.title': 'Oyun Ekle',
    'add.guide_title': 'Oyun Ekleme Rehberi',
    'add.guide_desc_search': 'Steam mağazasındaki tüm oyunları arayabilir ve tek tıkla Lua / Manifest dosyalarını indirebilirsiniz.',
    'add.guide_desc_files': 'İndirdiğiniz .lua, .manifest veya .zip dosyalarını doğrudan Steam klasörünüze aktarabilirsiniz.',
    'add.guide_desc_appid': "SteamDB'den bulduğunuz App ID ile anında indirme başlatabilirsiniz.",
    'add.tab_search': 'Mağazada Ara',
    'add.tab_files': 'Dosya Yükle',
    'add.tab_appid': 'App ID ile Ekle',
    'add.search_placeholder': 'Oyun adı veya App ID…',
    'add.popular_games': 'Popüler Oyunlar',
    'add.results_count': '{count} sonuç',
    'add.no_results': 'Sonuç bulunamadı.',
    'add.btn_download': 'İndir',
    'add.btn_downloading': 'İndiriliyor…',
    'add.btn_installing': 'Kuruluyor…',
    'add.btn_installed': 'Yüklendi',
    'add.drop_title': 'Dosyaları Buraya Sürükleyin',
    'add.drop_desc': '.manifest, .lua veya .zip dosyalarını sürükleyin ya da tıklayarak seçin.',
    'add.btn_choose_files': 'Dosya Seç',
    'add.sources_title': 'Dosya ve Manifest İndirebileceğiniz Güvenilir Kaynaklar:',
    'add.appid_title': 'Doğrudan App ID Girişi',
    'add.appid_desc': "SteamDB veya Steam mağazasındaki oyunun App ID'sini girerek doğrudan indirme başlatabilirsiniz.",
    'add.appid_placeholder': 'Örn: 730',
    'add.btn_download_install': 'İndir & Kur',
    'add.warn_invalid_appid': 'Lütfen geçerli bir App ID girin.',
    'add.toast_files_loaded': 'Dosyalar Yüklendi',
    'add.toast_files_count': '{lua} Lua, {manifests} Manifest eklendi.',
    'add.toast_installed': 'Kuruldu',
    'add.toast_install_err': 'Kurulum Hatası',
    'add.toast_err_unavailable': 'Mevcut değil — Dosya Yükle sekmesinden ekleyin.',

    // ── Online Fix ──
    'onlinefix.title': 'Online Fix Yükleyici',
    'onlinefix.site_link': 'online-fix.me Sitesi ↗',
    'onlinefix.guide_title': 'Online Fix Nedir ve Nasıl Çalışır?',
    'onlinefix.guide_desc': 'Online-Fix, oyunları arkadaşlarınızla resmi veya özel sunucularda çok oyunculu (multiplayer) oynamanızı sağlayan fix paketleridir.',
    'onlinefix.step1_desc': 'online-fix.me sitesinden indirdiğiniz fix arşivini (.rar, .zip, .7z) seçin.',
    'onlinefix.step2_desc': 'Oyunun ana kurulu olduğu klasörü (oyun .exe dosyasının bulunduğu dizin) seçin.',
    'onlinefix.step3_desc': '"Fix\'i Kur" butonuna basın. Arşiv otomatik olarak online-fix.me şifresiyle oyun klasörünüze çıkartılacaktır.',
    'onlinefix.step_important': 'Kurulum bittikten sonra Steam istemciniz açık olmalı ve oyunu doğrudan ana dizindeki exe dosyasından başlatmalısınız.',
    'onlinefix.warn_extractor_title': 'WinRAR veya 7-Zip Gerekli',
    'onlinefix.warn_extractor_desc': '.rar arşivlerini otomatik açabilmek için sisteminizde WinRAR veya 7-Zip kurulu olmalıdır.',
    'onlinefix.step1_title': 'Online-Fix Arşivini Seç (.rar / .zip / .7z)',
    'onlinefix.btn_select_archive': 'Arşiv Seç…',
    'onlinefix.step2_title': 'Hedef Oyun Klasörünü Seç (Exe\'nin olduğu klasör)',
    'onlinefix.btn_select_folder': 'Klasör Seç…',
    'onlinefix.btn_install': "Fix'i Kur",
    'onlinefix.btn_installing': 'Kuruluyor…',
    'onlinefix.btn_done': 'Tamamlandı',
    'onlinefix.label_starting': 'Başlatılıyor…',
    'onlinefix.label_installing_pct': 'Kuruluyor… %{pct}',
    'onlinefix.label_completing': 'Tamamlanıyor…',
    'onlinefix.label_done': 'Kurulum tamamlandı!',
    'onlinefix.toast_done': 'Fix Kuruldu',
    'onlinefix.toast_err': 'Fix Hatası',

    // ── SAM (Achievements) ──
    'sam.login_required_title': 'Steam Hesabı Gerekli',
    'sam.login_required_desc': 'Başarım yöneticisini kullanmak için Hesap sekmesinden Steam hesabınızı bağlamanız gerekiyor.',
    'sam.btn_go_to_account': 'Hesaba Git →',
    'sam.title': 'Başarım Yöneticisi (SAM)',
    'sam.game_count': '{count} oyun',
    'sam.search_placeholder': 'Oyun ara…',
    'sam.guide_title': 'Steam Achievement Manager',
    'sam.guide_desc': 'Bu listede yalnızca <b>başarımı olan oyunlar</b> listelenir. İstediğiniz oyunun kartına tıklayarak başarımlarını görüntüleyebilir, tek tek veya "Tümünü Aç" butonuyla hesabınıza işleyebilirsiniz.',
    'sam.no_games_title': 'Başarımı olan oyun bulunamadı',
    'sam.no_games_desc': 'Sadece başarımı olan oyunlar bu listede listelenir.',
    'sam.btn_achievements': 'Başarımlar →',
    'sam.btn_back': '← Oyun Seçimi',
    'sam.game_achievements_title': 'Oyun Başarımları',
    'sam.btn_unlock_all': 'Tümünü Aç',
    'sam.btn_lock_all': 'Tümünü Kilitle',
    'sam.btn_unlocking': 'Açılıyor…',
    'sam.btn_locking': 'Kilitleniyor…',
    'sam.stat_unlocked': 'Açılan Başarım',
    'sam.stat_total': 'Toplam Başarım',
    'sam.stat_lua': 'Aktif Yapılandırılan',
    'sam.filter_all': 'Tümü',
    'sam.filter_unlocked': 'Açık',
    'sam.filter_locked': 'Kilitli',
    'sam.search_ach_placeholder': 'Başarım ara…',
    'sam.no_ach_found': 'Sonuç bulunamadı.',
    'sam.global_pct': '%{pct} oyuncu',
    'sam.hidden_achievement': 'Gizli başarım',
    'sam.badge_unlocked': 'Açık',
    'sam.badge_lua': 'Açık (Lua)',
    'sam.badge_locked': 'Kilitli',
    'sam.btn_unlock': 'Kilidi Kaldır',
    'sam.btn_lock': 'Kilitle',
    'sam.loading_text': 'Başarımlar yükleniyor…',
    'sam.error_desc': 'Bu oyunun başarımı olmayabilir veya Steam API yanıt vermedi.',
    'sam.confirm_unlock_all_title': 'Tüm Başarımları Aç',
    'sam.confirm_unlock_all_msg': 'Bu oyuna ait {count} başarımın tümü açılacak. Onaylıyor musunuz?',
    'sam.confirm_lock_all_title': 'Tüm Başarımları Kilitle',
    'sam.confirm_lock_all_msg': 'Bu oyuna ait tüm başarımlar kilitlenecek. Onaylıyor musunuz?',
    'sam.toast_unlocked': 'Başarım Açıldı',
    'sam.toast_unlocked_lua': 'Başarım Açıldı (Lua)',
    'sam.toast_locked': 'Başarım Kilitlendi',
    'sam.toast_locked_lua': 'Başarım Kilitlendi (Lua)',
    'sam.toast_all_unlocked': 'Tümü Açıldı',
    'sam.toast_all_unlocked_msg': '{count} başarım başarıyla açıldı.',
    'sam.toast_all_locked': 'Tümü Kilitlendi',
    'sam.toast_all_locked_msg': '{count} başarım kilitlendi.',
    'sam.toast_err': 'SAM Hatası',

    // ── Idle Farmer ──
    'idle.title': 'Kart & Saat Kasma (Idle Farmer)',
    'idle.btn_refresh': '↺ Yenile',
    'idle.btn_stop_all': 'Tümünü Durdur',
    'idle.login_required_title': 'Steam Hesabı Gerekli',
    'idle.login_required_desc': 'Kart ve saat kasmak için Hesap sekmesinden Steam hesabınızı bağlamanız gerekiyor.',
    'idle.loading': 'Kütüphane yükleniyor…',
    'idle.guide_title': 'Kart ve Saat Kasma Rehberi',
    'idle.guide_desc': '<b>Nasıl Çalışır?</b> İstediğiniz oyunun yanındaki <b>Kas</b> butonuna bastığınızda, uygulama Steam istemciniz üzerinden oyunu arka planda "Oynuyor" sinyaliyle başlatır. Oyun yüklü olmasa bile oynama süresi artar ve kart düşürme hakkınız varsa kartlar envanterinize düşmeye başlar.<br><b>Kart Hakkı Kontrolü:</b> Aşağıdaki filtreden <i>"Kart Hakkı Olanlar"</i> seçeneğini seçerek yalnızca halen kart düşürme hakkınız bulunan oyunları listeleyebilirsiniz.',
    'idle.running_title': 'Şu An Kasılan Oyunlar',
    'idle.stat_idling': 'Kasılan Oyun',
    'idle.stat_active_proc': 'aktif işlem',
    'idle.stat_library': 'Kütüphane',
    'idle.stat_games': 'oyun',
    'idle.stat_tip_title': 'İpucu & Arka Plan',
    'idle.stat_tip_desc': "Pencereyi kapatabilir veya sol alttaki <b>Tray'e Küçült</b> butonuyla sistem tepsisinde sessizce çalışmasını sağlayabilirsiniz.",
    'idle.game_list_title': 'Oyun Listesi',
    'idle.filter_all': 'Tüm Oyunlar',
    'idle.filter_cards': 'Kart Hakkı Olanlar',
    'idle.search_placeholder': 'Oyun ara…',
    'idle.no_games': 'Oyun bulunamadı.',
    'idle.btn_idle': 'Kas',
    'idle.btn_stop': 'Durdur',
    'idle.label_idling': 'Kasılıyor',
    'idle.btn_starting': 'Başlatılıyor…',
    'idle.btn_stopping': 'Durduruluyor…',
    'idle.total_playtime': 'Toplam Süre: {time}',
    'idle.never_played': 'Oynanmadı',
    'idle.drops_remaining': '{count} kart hakkı',
    'idle.drops_ended': 'Kart hakkı bitti',
    'idle.no_drops': '— Kart hakkı yok',
    'idle.no_cards': '— Kart yok',
    'idle.has_cards': 'Kart var',
    'idle.confirm_stop_all_title': 'Tümünü Durdur',
    'idle.confirm_stop_all_msg': '{count} oyunun kasması durdurulacak.',
    'idle.toast_started': 'Kasma Başladı',
    'idle.toast_stopped': 'Kasma Durdu',
    'idle.toast_all_stopped': 'Tümü Durduruldu',
    'idle.toast_all_stopped_msg': '{count} oyun durduruldu.',
    'idle.toast_no_tray': 'pystray kurulu değil.',

    // ── Steam Account ──
    'account.title': 'Steam Hesabı',
    'account.btn_logout': 'Çıkış Yap',
    'account.guide_title': 'Steam Hesabı Entegrasyonu',
    'account.guide_desc': "Steam Web API Key'inizi bağladığınızda, gerçek Steam kütüphanenizdeki tüm oyunlar, rozetler ve kalan kart düşürme haklarınız otomatik olarak uygulamaya aktarılır.",
    'account.badge_connected': '● Bağlı',
    'account.lib_games_title': 'Kütüphanedeki Oyun',
    'account.lib_games_desc': 'Kart kasma ve Başarım yöneticisinde kullanılabilir.',
    'account.btn_refresh_lib': '↺ Kütüphaneyi Yenile',
    'account.form_title': 'Steam Web API ile Bağlan',
    'account.api_key_label': 'Steam Web API Key',
    'account.api_key_placeholder': '32 haneli API key',
    'account.api_key_hint': "API key'inizi {link} adresinden ücretsiz alabilirsiniz.",
    'account.steamid_label': 'Steam64 ID veya Profil Linki',
    'account.steamid_placeholder': '7656119... veya profil URL',
    'account.btn_connect': 'Bağlan',
    'account.btn_connecting': 'Bağlanıyor…',
    'account.err_missing_fields': 'API key ve Steam ID gereklidir.',
    'account.confirm_logout_title': 'Oturumu Kapat',
    'account.confirm_logout_msg': 'Steam hesap bağlantısı kaldırılacak.',
    'account.toast_connected': 'Hesap Bağlandı',
    'account.toast_logged_out': 'Çıkış Yapıldı',
    'account.toast_refreshing': 'Steam kütüphanesi güncelleniyor.',

    // ── DLC Unlocker ──
    'dlc.title': 'DLC Unlocker',
    'dlc.guide_title': 'DLC Unlocker Nasıl Çalışır?',
    'dlc.guide_desc': 'Steam oyununun App ID\'sini girin. Uygulama, Steam mağazasından o oyuna ait tüm DLC\'leri çeker ve listeleyerek seçtiklerinizi <code>marcellus.lua</code> dosyasına ekler. Steam yeniden başlatıldığında DLC\'ler aktif olur.<br><b>Not:</b> Bu özellik yalnızca Lua crack yüklü oyunlar için çalışır.',
    'dlc.search_title': "Oyun App ID'si ile Ara",
    'dlc.search_desc': "SteamDB veya Steam mağaza URL'sinden oyunun App ID'sini bulabilirsiniz.",
    'dlc.appid_placeholder': 'Örn: 1091500',
    'dlc.btn_fetch': 'DLC Listesini Getir',
    'dlc.btn_back': '← Geri',
    'dlc.list_title': 'DLC Listesi',
    'dlc.btn_unlock_all': 'Tümünü Aç',
    'dlc.btn_lock_all': 'Tümünü Kilitle',
    'dlc.stat_total': 'Toplam DLC',
    'dlc.stat_unlocked': 'Açık',
    'dlc.stat_locked': 'Kilitli',
    'dlc.filter_all': 'Tümü',
    'dlc.filter_unlocked': 'Açık',
    'dlc.filter_locked': 'Kilitli',
    'dlc.search_placeholder': 'DLC ara...',
    'dlc.no_results': 'DLC bulunamadı.',
    'dlc.badge_unlocked': 'Açık',
    'dlc.badge_locked': 'Kilitli',
    'dlc.btn_unlock': 'Aç',
    'dlc.btn_lock': 'Kilitle',
    'dlc.loading_text': 'DLC listesi yükleniyor...',
    'dlc.confirm_unlock_all_title': "Tüm DLC'leri Aç",
    'dlc.confirm_unlock_all_msg': '{game} oyununa ait {count} DLC açılacak.',
    'dlc.confirm_lock_all_title': "Tüm DLC'leri Kilitle",
    'dlc.confirm_lock_all_msg': '{count} açık DLC kilitlenecek.',
    'dlc.toast_unlocked': 'Açıldı',
    'dlc.toast_locked': 'Kilitlendi',
    'dlc.toast_all_unlocked': 'Tümü Açıldı',
    'dlc.toast_all_unlocked_msg': '{count} DLC açıldı.',
    'dlc.toast_all_locked': 'Tümü Kilitlendi',
    'dlc.toast_all_locked_msg': '{count} DLC kilitlendi.',
    'dlc.toast_none_found': '{game} için kayıtlı DLC yok.',
    'dlc.toast_already_unlocked': "Tüm DLC'ler zaten açık.",
    'dlc.toast_none_unlocked': 'Açık DLC yok.',
    'dlc.toast_err': 'DLC Hatası',

    // ── Settings ──
    'settings.title': 'Ayarlar',
    'settings.lang_section': 'Dil / Language',
    'settings.lang_label': 'Arayüz Dili',
    'settings.path_section': 'Steam Yolu',
    'settings.path_label': 'Klasör',
    'settings.btn_browse': 'Gözat',
    'settings.btn_autodetect': 'Otomatik',
    'settings.btn_save': 'Kaydet',
    'settings.controls_section': 'Steam Kontrolleri',
    'settings.btn_restart': '↺ Yeniden Başlat',
    'settings.btn_download_dll': '⬇ DLL Kur',
    'settings.btn_remove_dll': '✕ DLL Kaldır',
    'settings.btn_tray': "▼ Tray'e Küçült",
    'settings.about_section': 'Hakkında',
    'settings.developer_label': 'Geliştirici',
    'settings.dlls_label': "DLL'ler",
    'settings.web_label': 'Web',
    'settings.version_label': 'Versiyon',
    'settings.confirm_remove_dll_title': 'DLL Kaldır',
    'settings.confirm_remove_dll_msg': 'Crack DLL dosyaları Steam dizininden kaldırılacak.',
    'settings.toast_detected': 'Bulundu',
    'settings.toast_not_detected': 'Steam otomatik tespit edilemedi.',
    'settings.toast_saved': 'Kaydedildi',
    'settings.toast_save_err': 'Kaydedilemedi.',
    'settings.toast_restarting': 'Steam kapatılıp tekrar açılıyor.',
    'settings.toast_restarted': 'Steam yeniden başlatıldı.',
    'settings.toast_downloading_dll': 'DLL dosyaları yükleniyor.',
    'settings.toast_dll_installed': 'DLL dosyaları kuruldu.',
    'settings.toast_dll_removed': '{count} DLL dosyası silindi.',

    // ── Context Menu & Modals ──
    'ctx.steamdb': "SteamDB'de Aç",
    'ctx.copy_appid': 'App ID Kopyala',
    'ctx.remove_game': 'Oyunu Kaldır',
    'ctx.toast_copied': 'Kopyalandı',
    'modal.are_you_sure': 'Emin misiniz?',
    'modal.cancel': 'İptal',
    'modal.confirm': 'Onayla',

    // ── Legal Modal ──
    'legal.title': 'Fadimrak Steam Tool — Yasal Uyarı',
    'legal.terms_title': 'Kullanım Şartları',
    'legal.terms_text': 'Bu uygulama yalnızca <strong>eğitim ve araştırma amaçlıdır</strong>. Geliştirici kötüye kullanımdan sorumlu tutulamaz.',
    'legal.copyright_title': 'Telif Hakkı',
    'legal.copyright_text': "Steam, Valve Corporation'ın tescilli markasıdır. Bu uygulama Valve ile bağlantılı değildir.",
    'legal.disclaimer_title': 'Sorumluluk Reddi',
    'legal.disclaimer_text': 'Uygulama "olduğu gibi" sunulmaktadır. Kullanımdan doğan her türlü sorumluluk kullanıcıya aittir.',
    'legal.checkbox_label': 'Yasal uyarıyı okudum ve kabul ediyorum.',
    'legal.btn_reject': 'Reddet & Çıkış',
    'legal.btn_accept': 'Kabul Et',

    // ── General Toasts ──
    'toast.success': 'Başarılı',
    'toast.error': 'Hata',
    'toast.info': 'Bilgi',
    'toast.warn': 'Uyarı',
    'toast.downloading': 'İndiriliyor…',
    'toast.restarting': 'Yeniden Başlatılıyor…',
    'toast.completed': 'Tamamlandı',
    'toast.removed': 'Kaldırıldı',
  },

  en: {
    // ── Navigation & Sidebar ──
    'nav.library': 'Library',
    'nav.add_game': 'Add Game',
    'nav.onlinefix': 'Online Fix',
    'nav.sam': 'Achievements',
    'nav.idle': 'Card & Time Idle',
    'nav.dlc': 'DLC Unlocker',
    'nav.account': 'Steam Account',
    'nav.settings': 'Settings',
    'nav.restart_steam': 'Restart Steam',
    'nav.minimize_tray': 'Minimize to Tray',
    'nav.dll_checking': 'Checking DLL…',
    'nav.dll_active': 'DLL Active',
    'nav.dll_missing': 'DLL Missing',
    'nav.steam_missing': 'Steam Not Found',

    // ── Splash & Update ──
    'splash.credits': 'Created by fadimrak. Enjoy!',
    'update.banner': 'A new version is available!',
    'update.download': 'Download',

    // ── Library ──
    'library.title': 'Library',
    'library.search_placeholder': 'Search library…',
    'library.restart_btn': '↺ Restart Steam',
    'library.guide_title': 'Library User Guide',
    'library.guide_desc': 'Added games automatically link to your Steam client. Click a game card to manage its achievements, right-click to open its SteamDB page or copy its App ID.',
    'library.empty_title': 'No games added yet',
    'library.empty_desc': 'You can add games by searching the store or uploading files in the Add Game tab.',
    'library.add_btn': 'Add Game →',
    'library.remove_btn': 'Remove',
    'library.count': '{count} games',
    'library.confirm_remove_title': 'Remove Game',
    'library.confirm_remove_msg': '"{name}" will be removed from your Steam library and local configuration.',
    'library.toast_removed': 'Game Removed',

    // ── Add Game ──
    'add.title': 'Add Game',
    'add.guide_title': 'Game Adding Guide',
    'add.guide_desc_search': 'Search all games on the Steam store and download Lua / Manifest files with a single click.',
    'add.guide_desc_files': 'Transfer downloaded .lua, .manifest, or .zip files directly into your Steam folder.',
    'add.guide_desc_appid': 'Start downloading immediately using the App ID from SteamDB or Steam store.',
    'add.tab_search': 'Search Store',
    'add.tab_files': 'Upload Files',
    'add.tab_appid': 'Add via App ID',
    'add.search_placeholder': 'Game name or App ID…',
    'add.popular_games': 'Popular Games',
    'add.results_count': '{count} results',
    'add.no_results': 'No results found.',
    'add.btn_download': 'Download',
    'add.btn_downloading': 'Downloading…',
    'add.btn_installing': 'Installing…',
    'add.btn_installed': 'Installed',
    'add.drop_title': 'Drag & Drop Files Here',
    'add.drop_desc': 'Drag .manifest, .lua or .zip files or click to browse.',
    'add.btn_choose_files': 'Choose Files',
    'add.sources_title': 'Reliable Sources to Download Files and Manifests:',
    'add.appid_title': 'Direct App ID Input',
    'add.appid_desc': 'Enter the App ID from SteamDB or Steam store to start downloading directly.',
    'add.appid_placeholder': 'e.g. 730',
    'add.btn_download_install': 'Download & Install',
    'add.warn_invalid_appid': 'Please enter a valid App ID.',
    'add.toast_files_loaded': 'Files Loaded',
    'add.toast_files_count': '{lua} Lua, {manifests} Manifest files added.',
    'add.toast_installed': 'Installed',
    'add.toast_install_err': 'Installation Error',
    'add.toast_err_unavailable': 'Not available — please add via Upload Files tab.',

    // ── Online Fix ──
    'onlinefix.title': 'Online Fix Installer',
    'onlinefix.site_link': 'online-fix.me Site ↗',
    'onlinefix.guide_title': 'What is Online Fix and How Does It Work?',
    'onlinefix.guide_desc': 'Online-Fix packages enable multiplayer gaming on official or custom servers with friends for cracked games.',
    'onlinefix.step1_desc': 'Select the fix archive (.rar, .zip, .7z) downloaded from online-fix.me.',
    'onlinefix.step2_desc': 'Select the root folder of the installed game (the directory where game .exe is located).',
    'onlinefix.step3_desc': 'Click "Install Fix". The archive will be extracted into your game directory using the password online-fix.me.',
    'onlinefix.step_important': 'After installation, Steam must be running and you should launch the game directly from its main directory .exe file.',
    'onlinefix.warn_extractor_title': 'WinRAR or 7-Zip Required',
    'onlinefix.warn_extractor_desc': 'WinRAR or 7-Zip must be installed on your system to automatically extract .rar archives.',
    'onlinefix.step1_title': 'Select Online-Fix Archive (.rar / .zip / .7z)',
    'onlinefix.btn_select_archive': 'Select Archive…',
    'onlinefix.step2_title': 'Select Target Game Directory (Folder with .exe)',
    'onlinefix.btn_select_folder': 'Select Directory…',
    'onlinefix.btn_install': 'Install Fix',
    'onlinefix.btn_installing': 'Installing…',
    'onlinefix.btn_done': 'Completed',
    'onlinefix.label_starting': 'Starting…',
    'onlinefix.label_installing_pct': 'Installing… %{pct}',
    'onlinefix.label_completing': 'Completing…',
    'onlinefix.label_done': 'Installation completed!',
    'onlinefix.toast_done': 'Fix Installed',
    'onlinefix.toast_err': 'Fix Error',

    // ── SAM (Achievements) ──
    'sam.login_required_title': 'Steam Account Required',
    'sam.login_required_desc': 'To use the achievement manager, you need to connect your Steam account from the Account tab.',
    'sam.btn_go_to_account': 'Go to Account →',
    'sam.title': 'Achievement Manager (SAM)',
    'sam.game_count': '{count} games',
    'sam.search_placeholder': 'Search games…',
    'sam.guide_title': 'Steam Achievement Manager',
    'sam.guide_desc': 'Only <b>games with achievements</b> are listed here. Click on any game card to view achievements, then unlock them individually or all at once with "Unlock All".',
    'sam.no_games_title': 'No games with achievements found',
    'sam.no_games_desc': 'Only games with registered achievements are shown in this list.',
    'sam.btn_achievements': 'Achievements →',
    'sam.btn_back': '← Select Game',
    'sam.game_achievements_title': 'Game Achievements',
    'sam.btn_unlock_all': 'Unlock All',
    'sam.btn_lock_all': 'Lock All',
    'sam.btn_unlocking': 'Unlocking…',
    'sam.btn_locking': 'Locking…',
    'sam.stat_unlocked': 'Unlocked Achievements',
    'sam.stat_total': 'Total Achievements',
    'sam.stat_lua': 'Active Configured',
    'sam.filter_all': 'All',
    'sam.filter_unlocked': 'Unlocked',
    'sam.filter_locked': 'Locked',
    'sam.search_ach_placeholder': 'Search achievements…',
    'sam.no_ach_found': 'No results found.',
    'sam.global_pct': '{pct}% of players',
    'sam.hidden_achievement': 'Hidden achievement',
    'sam.badge_unlocked': 'Unlocked',
    'sam.badge_lua': 'Unlocked (Lua)',
    'sam.badge_locked': 'Locked',
    'sam.btn_unlock': 'Unlock',
    'sam.btn_lock': 'Lock',
    'sam.loading_text': 'Loading achievements…',
    'sam.error_desc': 'This game might not have achievements or Steam API did not respond.',
    'sam.confirm_unlock_all_title': 'Unlock All Achievements',
    'sam.confirm_unlock_all_msg': 'All {count} achievements for this game will be unlocked. Do you wish to proceed?',
    'sam.confirm_lock_all_title': 'Lock All Achievements',
    'sam.confirm_lock_all_msg': 'All achievements for this game will be locked. Do you wish to proceed?',
    'sam.toast_unlocked': 'Achievement Unlocked',
    'sam.toast_unlocked_lua': 'Achievement Unlocked (Lua)',
    'sam.toast_locked': 'Achievement Locked',
    'sam.toast_locked_lua': 'Achievement Locked (Lua)',
    'sam.toast_all_unlocked': 'All Unlocked',
    'sam.toast_all_unlocked_msg': '{count} achievements successfully unlocked.',
    'sam.toast_all_locked': 'All Locked',
    'sam.toast_all_locked_msg': '{count} achievements locked.',
    'sam.toast_err': 'SAM Error',

    // ── Idle Farmer ──
    'idle.title': 'Card & Time Idle Farmer',
    'idle.btn_refresh': '↺ Refresh',
    'idle.btn_stop_all': 'Stop All',
    'idle.login_required_title': 'Steam Account Required',
    'idle.login_required_desc': 'To idle cards and playtime, you need to connect your Steam account from the Account tab.',
    'idle.loading': 'Loading library…',
    'idle.guide_title': 'Card & Playtime Idling Guide',
    'idle.guide_desc': '<b>How It Works:</b> Clicking <b>Idle</b> sends an in-game signal via your Steam client in the background. Playtime increases and trading cards drop to your inventory without launching game binaries.<br><b>Card Drops Filter:</b> Select <i>"Card Drops Available"</i> below to filter games with remaining card drops.',
    'idle.running_title': 'Currently Idling Games',
    'idle.stat_idling': 'Idling Games',
    'idle.stat_active_proc': 'active processes',
    'idle.stat_library': 'Library',
    'idle.stat_games': 'games',
    'idle.stat_tip_title': 'Tip & Background Running',
    'idle.stat_tip_desc': 'You can close the window or click <b>Minimize to Tray</b> on the bottom left to keep it running silently in the system tray.',
    'idle.game_list_title': 'Game List',
    'idle.filter_all': 'All Games',
    'idle.filter_cards': 'Card Drops Available',
    'idle.search_placeholder': 'Search games…',
    'idle.no_games': 'No games found.',
    'idle.btn_idle': 'Idle',
    'idle.btn_stop': 'Stop',
    'idle.label_idling': 'Idling',
    'idle.btn_starting': 'Starting…',
    'idle.btn_stopping': 'Stopping…',
    'idle.total_playtime': 'Total Time: {time}',
    'idle.never_played': 'Never played',
    'idle.drops_remaining': '{count} card drops remaining',
    'idle.drops_ended': 'No drops remaining',
    'idle.no_drops': '— No card drops',
    'idle.no_cards': '— No cards',
    'idle.has_cards': 'Cards available',
    'idle.confirm_stop_all_title': 'Stop All Idling',
    'idle.confirm_stop_all_msg': 'Idling for {count} games will be stopped.',
    'idle.toast_started': 'Idling Started',
    'idle.toast_stopped': 'Idling Stopped',
    'idle.toast_all_stopped': 'All Stopped',
    'idle.toast_all_stopped_msg': '{count} games stopped.',
    'idle.toast_no_tray': 'pystray is not installed.',

    // ── Steam Account ──
    'account.title': 'Steam Account',
    'account.btn_logout': 'Log Out',
    'account.guide_title': 'Steam Account Integration',
    'account.guide_desc': 'When you connect your Steam Web API Key, all games, badges, and card drops from your real Steam library are imported automatically.',
    'account.badge_connected': '● Connected',
    'account.lib_games_title': 'Games in Library',
    'account.lib_games_desc': 'Available for Card Idle and Achievement Manager.',
    'account.btn_refresh_lib': '↺ Refresh Library',
    'account.form_title': 'Connect with Steam Web API',
    'account.api_key_label': 'Steam Web API Key',
    'account.api_key_placeholder': '32-digit API key',
    'account.api_key_hint': 'You can get your API key for free at {link}.',
    'account.steamid_label': 'Steam64 ID or Profile Link',
    'account.steamid_placeholder': '7656119... or profile URL',
    'account.btn_connect': 'Connect',
    'account.btn_connecting': 'Connecting…',
    'account.err_missing_fields': 'API key and Steam ID are required.',
    'account.confirm_logout_title': 'Log Out',
    'account.confirm_logout_msg': 'Your Steam account connection will be removed.',
    'account.toast_connected': 'Account Connected',
    'account.toast_logged_out': 'Logged Out',
    'account.toast_refreshing': 'Updating Steam library.',

    // ── DLC Unlocker ──
    'dlc.title': 'DLC Unlocker',
    'dlc.guide_title': 'How Does DLC Unlocker Work?',
    'dlc.guide_desc': 'Enter the game\'s App ID. The app fetches all store DLCs and writes your selected DLCs into <code>marcellus.lua</code>. Restarting Steam will activate the DLCs.<br><b>Note:</b> This feature works for games installed with Lua crack.',
    'dlc.search_title': 'Search by Game App ID',
    'dlc.search_desc': 'You can find the App ID from SteamDB or the Steam store URL.',
    'dlc.appid_placeholder': 'e.g. 1091500',
    'dlc.btn_fetch': 'Fetch DLC List',
    'dlc.btn_back': '← Back',
    'dlc.list_title': 'DLC List',
    'dlc.btn_unlock_all': 'Unlock All',
    'dlc.btn_lock_all': 'Lock All',
    'dlc.stat_total': 'Total DLCs',
    'dlc.stat_unlocked': 'Unlocked',
    'dlc.stat_locked': 'Locked',
    'dlc.filter_all': 'All',
    'dlc.filter_unlocked': 'Unlocked',
    'dlc.filter_locked': 'Locked',
    'dlc.search_placeholder': 'Search DLCs...',
    'dlc.no_results': 'No DLCs found.',
    'dlc.badge_unlocked': 'Unlocked',
    'dlc.badge_locked': 'Locked',
    'dlc.btn_unlock': 'Unlock',
    'dlc.btn_lock': 'Lock',
    'dlc.loading_text': 'Loading DLC list...',
    'dlc.confirm_unlock_all_title': 'Unlock All DLCs',
    'dlc.confirm_unlock_all_msg': '{count} DLCs for {game} will be unlocked.',
    'dlc.confirm_lock_all_title': 'Lock All DLCs',
    'dlc.confirm_lock_all_msg': '{count} unlocked DLCs will be locked.',
    'dlc.toast_unlocked': 'Unlocked',
    'dlc.toast_locked': 'Locked',
    'dlc.toast_all_unlocked': 'All Unlocked',
    'dlc.toast_all_unlocked_msg': '{count} DLCs unlocked.',
    'dlc.toast_all_locked': 'All Locked',
    'dlc.toast_all_locked_msg': '{count} DLCs locked.',
    'dlc.toast_none_found': 'No registered DLCs found for {game}.',
    'dlc.toast_already_unlocked': 'All DLCs are already unlocked.',
    'dlc.toast_none_unlocked': 'No unlocked DLCs.',
    'dlc.toast_err': 'DLC Error',

    // ── Settings ──
    'settings.title': 'Settings',
    'settings.lang_section': 'Dil / Language',
    'settings.lang_label': 'Interface Language',
    'settings.path_section': 'Steam Path',
    'settings.path_label': 'Folder',
    'settings.btn_browse': 'Browse',
    'settings.btn_autodetect': 'Auto Detect',
    'settings.btn_save': 'Save',
    'settings.controls_section': 'Steam Controls',
    'settings.btn_restart': '↺ Restart Steam',
    'settings.btn_download_dll': '⬇ Install DLL',
    'settings.btn_remove_dll': '✕ Remove DLL',
    'settings.btn_tray': '▼ Minimize to Tray',
    'settings.about_section': 'About',
    'settings.developer_label': 'Developer',
    'settings.dlls_label': 'DLLs',
    'settings.web_label': 'Web',
    'settings.version_label': 'Version',
    'settings.confirm_remove_dll_title': 'Remove DLL',
    'settings.confirm_remove_dll_msg': 'Crack DLL files will be removed from the Steam directory.',
    'settings.toast_detected': 'Found',
    'settings.toast_not_detected': 'Steam could not be automatically detected.',
    'settings.toast_saved': 'Saved',
    'settings.toast_save_err': 'Could not be saved.',
    'settings.toast_restarting': 'Closing and restarting Steam.',
    'settings.toast_restarted': 'Steam restarted successfully.',
    'settings.toast_downloading_dll': 'Installing DLL files.',
    'settings.toast_dll_installed': 'DLL files installed successfully.',
    'settings.toast_dll_removed': '{count} DLL file(s) removed.',

    // ── Context Menu & Modals ──
    'ctx.steamdb': 'Open in SteamDB',
    'ctx.copy_appid': 'Copy App ID',
    'ctx.remove_game': 'Remove Game',
    'ctx.toast_copied': 'Copied',
    'modal.are_you_sure': 'Are you sure?',
    'modal.cancel': 'Cancel',
    'modal.confirm': 'Confirm',

    // ── Legal Modal ──
    'legal.title': 'Fadimrak Steam Tool — Legal Notice',
    'legal.terms_title': 'Terms of Use',
    'legal.terms_text': 'This application is strictly for <strong>educational and research purposes</strong>. The developer cannot be held responsible for any misuse.',
    'legal.copyright_title': 'Copyright Notice',
    'legal.copyright_text': 'Steam is a registered trademark of Valve Corporation. This tool is not affiliated with or endorsed by Valve.',
    'legal.disclaimer_title': 'Disclaimer',
    'legal.disclaimer_text': 'The application is provided "as-is". Any liability arising from the use of this software rests entirely with the user.',
    'legal.checkbox_label': 'I have read and agree to the terms and legal notice.',
    'legal.btn_reject': 'Reject & Exit',
    'legal.btn_accept': 'Accept',

    // ── General Toasts ──
    'toast.success': 'Success',
    'toast.error': 'Error',
    'toast.info': 'Info',
    'toast.warn': 'Warning',
    'toast.downloading': 'Downloading…',
    'toast.restarting': 'Restarting…',
    'toast.completed': 'Completed',
    'toast.removed': 'Removed',
  }
};

let currentLang = 'tr';

/**
 * Get translated string by key, with optional parameter substitution
 * e.g. t('library.count', { count: 5 }) -> "5 games"
 */
function t(key, params = {}) {
  const dict = I18N[currentLang] || I18N['tr'];
  let text = dict[key] || I18N['tr'][key] || key;
  if (params && typeof params === 'object') {
    Object.entries(params).forEach(([k, v]) => {
      text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), v);
    });
  }
  return text;
}

function getCurrentLang() {
  return currentLang;
}

/**
 * Set active language ('tr' or 'en') and update all DOM elements and active page
 */
function setLanguage(lang, saveToBackend = true) {
  if (lang !== 'tr' && lang !== 'en') lang = 'tr';
  currentLang = lang;
  document.documentElement.lang = lang;

  // Update static elements with data-i18n attributes
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) el.innerHTML = t(key);
  });

  // Update placeholder attributes
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key) el.placeholder = t(key);
  });

  // Update title attributes
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    if (key) el.title = t(key);
  });

  // Update language toggle buttons in settings / header
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });

  const langSelect = document.getElementById('setting-lang-select');
  if (langSelect) langSelect.value = lang;

  // Re-render dynamic active views if needed
  if (window.installedGames && currentPage === 'library') {
    renderLibrary(window.installedGames);
  }
  if (currentPage === 'idle' && typeof _idleRenderGrid === 'function') {
    _idleRenderGrid();
  }
  if (currentPage === 'sam') {
    if (typeof _samRenderGameGrid === 'function') _samRenderGameGrid();
    if (typeof _samRenderList === 'function') _samRenderList();
  }
  if (currentPage === 'dlc' && typeof _dlcRenderList === 'function') {
    _dlcRenderList();
  }

  // Save preference to backend
  if (saveToBackend && window.pywebview && window.pywebview.api) {
    try {
      pywebview.api.set_language(lang);
    } catch (e) {
      pywebview.api.save_all_settings({ lang });
    }
  }
}
