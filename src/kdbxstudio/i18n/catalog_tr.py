"""Turkish (tr) UI string catalog for KDBXStudio.

Maps English source UI strings (exact literals used in the app) to
İstanbul Turkish translations. Keys must match source text character-for-
character, including ellipsis (…), punctuation, and shortcut hints.
"""

from __future__ import annotations

TR_CATALOG: dict[str, str] = {
    # ── Menus (accelerators) ──────────────────────────────────────────
    "&File": "&Dosya",
    "&Entry": "&Kayıt",
    "&Group": "&Grup",
    "&Tools": "&Araçlar",
    "&View": "&Görünüm",
    "&Help": "&Yardım",
    # ── File menu ─────────────────────────────────────────────────────
    "Open…": "Aç…",
    "New Database…": "Yeni Veritabanı…",
    "Save": "Kaydet",
    "Export CSV…": "CSV Dışa Aktar…",
    "Import CSV…": "CSV İçe Aktar…",
    "Database Properties…": "Veritabanı Özellikleri…",
    "Change Master Password…": "Ana Şifreyi Değiştir…",
    "Close": "Kapat",
    "Open Recent": "Son Açılanlar",
    "Quit": "Çıkış",
    "No recent databases": "Son açılan veritabanı yok",
    "Clear Recent": "Son Açılanları Temizle",
    # ── Entry menu / context ──────────────────────────────────────────
    "Add Entry…": "Kayıt Ekle…",
    "New from Template…": "Şablondan Yeni…",
    "Move to Recycle Bin": "Çöp Kutusuna Taşı",
    "Delete Permanently": "Kalıcı Olarak Sil",
    "Auto-Type": "Otomatik Yazma",
    "Move to Group…": "Gruba Taşı…",
    "Fetch Favicon": "Favicon Getir",
    "Copy Username": "Kullanıcı Adını Kopyala",
    "Copy Password": "Şifreyi Kopyala",
    "Copy URL": "URL’yi Kopyala",
    "Copy TOTP": "TOTP Kodunu Kopyala",
    # ── Group menu / context ──────────────────────────────────────────
    "Add Group…": "Grup Ekle…",
    "Rename Group…": "Grubu Yeniden Adlandır…",
    "Move Group to Recycle Bin": "Grubu Çöp Kutusuna Taşı",
    "Empty Recycle Bin…": "Çöp Kutusunu Boşalt…",
    # ── Tools menu ────────────────────────────────────────────────────
    "Password Health…": "Şifre Sağlığı…",
    "Plugin Center": "Eklenti Merkezi",
    "Marketplace…": "Mağaza…",
    "Installed Plugins…": "Yüklü Eklentiler…",
    "Password Generator…": "Şifre Üretici…",
    "Merge Database…": "Veritabanı Birleştir…",
    "Emergency Sheet…": "Acil Durum Sayfası…",
    "Check for Updates…": "Güncellemeleri Denetle…",
    "Add Selected PEM to SSH Agent": "Seçili PEM’i SSH Agent’a Ekle",
    "Lock All Databases": "Tüm Veritabanlarını Kilitle",
    "Settings…": "Ayarlar…",
    # ── View / Help ───────────────────────────────────────────────────
    "Save Layout": "Düzeni Kaydet",
    "Reset Layout": "Düzeni Sıfırla",
    "Theme": "Tema",
    "Accent": "Vurgu rengi",
    "Teal": "Turkuaz",
    "Blue": "Mavi",
    "Purple": "Mor",
    "Green": "Yeşil",
    "Orange": "Turuncu",
    "Red": "Kırmızı",
    "Accent: {name}": "Vurgu: {name}",
    "Applies to Studio Dark / Light (and System)": (
        "Studio Koyu / Açık (ve Sistem) temalarına uygulanır"
    ),
    "Tints buttons, selection, and focus across all themes": (
        "Düğmeler, seçim ve odak halkasını tüm temalarda renklendirir"
    ),
    "Dark": "Koyu",
    "Light": "Açık",
    "System": "Sistem",
    "Studio Dark": "Studio Koyu",
    "Studio Light": "Studio Açık",
    "Nord": "Nord",
    "Dracula": "Dracula",
    "Tokyo Night": "Tokyo Night",
    "Catppuccin Mocha": "Catppuccin Mocha",
    "Catppuccin Latte": "Catppuccin Latte",
    "Solarized Dark": "Solarized Koyu",
    "One Dark": "One Dark",
    "Gruvbox Dark": "Gruvbox Koyu",
    "Theme: {name}": "Tema: {name}",
    "Theme: Dark": "Tema: Koyu",
    "Theme: Light": "Tema: Açık",
    "Theme: System": "Tema: Sistem",
    "Command Palette…": "Komut Paleti…",
    "About": "Hakkında",
    "Language": "Dil",
    "UI density": "Arayüz yoğunluğu",
    "UI scale": "Arayüz ölçeği",
    "Font size": "Yazı tipi boyutu",
    "Menu size": "Menü boyutu",
    "Window resolution": "Pencere çözünürlüğü",
    "40% — Tiny": "40% — Çok küçük",
    "50% — Very small": "50% — Oldukça küçük",
    "60% — Small": "60% — Küçük",
    "70%": "70%",
    "80%": "80%",
    "90% — Compact": "90% — Kompakt",
    "100% — Default": "100% — Varsayılan",
    "110% — Comfortable": "110% — Rahat",
    "125% — Large": "125% — Büyük",
    "150% — Extra large": "150% — Çok büyük",
    "8 px — Tiny": "8 px — Çok küçük",
    "9 px": "9 px",
    "10 px — Very small": "10 px — Oldukça küçük",
    "11 px — Small": "11 px — Küçük",
    "12 px": "12 px",
    "13 px — Default": "13 px — Varsayılan",
    "14 px": "14 px",
    "15 px": "15 px",
    "16 px — Large": "16 px — Büyük",
    "18 px — Extra large": "18 px — Çok büyük",
    "Auto — Fit screen": "Otomatik — Ekrana sığdır",
    "1024 × 640 — Compact": "1024 × 640 — Kompakt",
    "1280 × 720 — HD": "1280 × 720 — HD",
    "1280 × 800 — Default": "1280 × 800 — Varsayılan",
    "1440 × 900": "1440 × 900",
    "1600 × 900 — Large": "1600 × 900 — Büyük",
    "1920 × 1080 — Full HD": "1920 × 1080 — Full HD",
    "Small": "Küçük",
    "Medium — Default": "Orta — Varsayılan",
    "Large": "Büyük",
    "Compact": "Kompakt",
    "Comfortable": "Rahat",
    # ── Tray ──────────────────────────────────────────────────────────
    "Show": "Göster",
    "Lock": "Kilitle",
    # ── Toolbar tooltips ──────────────────────────────────────────────
    "Main": "Ana",
    "Open database": "Veritabanını aç",
    "Save database": "Veritabanını kaydet",
    "Add entry": "Kayıt ekle",
    "Command palette": "Komut paleti",
    "Password Health": "Şifre Sağlığı",
    "Plugin marketplace": "Eklenti mağazası",
    "Lock all databases": "Tüm veritabanlarını kilitle",
    # ── Tabs / docks / search ─────────────────────────────────────────
    "Groups": "Gruplar",
    "Entry": "Kayıt",
    "TOTP": "TOTP",
    "History": "Geçmiş",
    "Attachments": "Ekler",
    "Certificates / SSH": "Sertifikalar / SSH",
    "Search entries…": "Kayıtlarda ara…",
    "Universal search": "Evrensel arama",
    "Ready": "Hazır",
    # ── Status bar (short chrome) ─────────────────────────────────────
    "Username copied": "Kullanıcı adı kopyalandı",
    "Password copied (clears in {secs}s)": (
        "Şifre kopyalandı ({secs} sn sonra temizlenir)"
    ),
    "URL copied": "URL kopyalandı",
    "TOTP code copied": "TOTP kodu kopyalandı",
    "Settings saved": "Ayarlar kaydedildi",
    "Database saved": "Veritabanı kaydedildi",
    "Database closed": "Veritabanı kapatıldı",
    "Layout saved": "Düzen kaydedildi",
    "Layout reset": "Düzen sıfırlandı",
    "Group moved to Recycle Bin": "Grup Çöp Kutusuna taşındı",
    "Focus target window… Auto-Type starting": (
        "Hedef pencereye odaklanın… Otomatik yazma başlıyor"
    ),
    "Identity added to SSH agent": "Kimlik SSH agent’a eklendi",
    "{n} result(s)": "{n} sonuç",
    # ── Empty workspace ───────────────────────────────────────────────
    "KDBXStudio": "KDBXStudio",
    "Open or create a database to get started.": (
        "Başlamak için bir veritabanı açın veya oluşturun."
    ),
    "Open Database…": "Veritabanı Aç…",
    "Create Database…": "Veritabanı Oluştur…",
    "Command Palette (Ctrl+K)": "Komut Paleti (Ctrl+K)",
    "Recent databases": "Son açılan veritabanları",
    # ── Settings dialog ───────────────────────────────────────────────
    "Settings": "Ayarlar",
    "Enable idle auto-lock": "Boşta kalınca otomatik kilitlemeyi etkinleştir",
    "Clear clipboard on lock": "Kilitlenince panoyu temizle",
    "Minimize window on lock": "Kilitlenince pencereyi küçült",
    "Check passwords against Have I Been Pwned (k-anonymity)": (
        "Şifreleri Have I Been Pwned ile kontrol et (k-anonimlik)"
    ),
    "Check passwords with HIBP": "Şifreleri HIBP ile kontrol et",
    "Uses the Have I Been Pwned k-anonymity password service": (
        "Have I Been Pwned k-anonimlik şifre hizmetini kullanır"
    ),
    "Download site icons automatically": "Site simgelerini otomatik indir",
    "Privacy: sends entry URL domains to Google for favicon lookup": (
        "Gizlilik: favicon araması için kayıt URL alan adlarını Google'a gönderir"
    ),
    "Privacy: enabled lookups send URL domains to Google": (
        "Gizlilik: etkin aramalar URL alan adlarını Google'a gönderir"
    ),
    "Check for updates on startup": "Başlangıçta güncellemeleri denetle",
    "Start minimized to tray": "Sistem tepsisine küçültülmüş başlat",
    "Open databases in read-only mode": "Veritabanlarını salt okunur aç",
    "Clipboard clear after": "Panoyu temizleme süresi",
    "Auto-lock after": "Otomatik kilitleme süresi",
    "Auto-Type sequence": "Otomatik yazma dizisi",
    "Watch open database files for external changes": (
        "Açık veritabanı dosyalarını dış değişiklikler için izle"
    ),
    "Enable KeePassXC-Browser integration": (
        "KeePassXC-Browser entegrasyonunu etkinleştir"
    ),
    "Install browser host manifests…": "Tarayıcı host bildirimlerini kur…",
    "Browser host": "Tarayıcı host",
    "Could not install native messaging manifests:\n{err}": (
        "Native messaging bildirimleri kurulamadı:\n{err}"
    ),
    "Installed KeePassXC-Browser native messaging manifests:\n{paths}\n\n"
    "Unlock a database in KDBXStudio, then Connect in the extension.\n"
    "If KeePassXC is also installed, disable its browser integration "
    "to avoid conflicting manifests.": (
        "KeePassXC-Browser native messaging bildirimleri kuruldu:\n{paths}\n\n"
        "KDBXStudio’da bir veritabanının kilidini açın, ardından eklentide "
        "Connect’e basın.\n"
        "KeePassXC de yüklüyse, çakışan bildirimleri önlemek için onun "
        "tarayıcı entegrasyonunu kapatın."
    ),
    "Browser integration ready (KeePassXC-Browser)": (
        "Tarayıcı entegrasyonu hazır (KeePassXC-Browser)"
    ),
    "Browser association": "Tarayıcı eşleştirmesi",
    "KeePassXC-Browser wants to connect to:\n{db}\n\n"
    "Give this connection a name (for example: firefox-laptop):": (
        "KeePassXC-Browser şuna bağlanmak istiyor:\n{db}\n\n"
        "Bu bağlantıya bir ad verin (örnek: firefox-laptop):"
    ),
    "Browser associated — remember to Save": (
        "Tarayıcı eşleştirildi — Kaydetmeyi unutmayın"
    ),
    "Hardware keys (YubiKey challenge-response) are not supported yet "
    "by the underlying KeePass library.": (
        "Donanım anahtarları (YubiKey challenge-response) henüz "
        "altta yatan KeePass kütüphanesi tarafından desteklenmiyor."
    ),
    # Language (settings / messages used by i18n wiring)
    " s": " sn",
    " min": " dk",
    "Restart required": "Yeniden başlatma gerekli",
    "Language changes take effect after restart.": (
        "Dil değişiklikleri yeniden başlatmadan sonra uygulanır."
    ),
    "Language changed": "Dil değiştirildi",
    "Some remaining labels may need an application restart to update.": (
        "Bazı etiketlerin güncellenmesi için uygulamanın yeniden "
        "başlatılması gerekebilir."
    ),
    "The interface language was updated. Some labels refresh immediately; "
    "restart the app if anything still looks wrong.": (
        "Arayüz dili güncellendi. Bazı etiketler hemen yenilenir; bir şeyler "
        "hâlâ önceki dilde görünüyorsa uygulamayı yeniden başlatın."
    ),
    "(unnamed)": "(adsız)",
    "(untitled)": "(başlıksız)",
    "(no field changes)": "(alan değişikliği yok)",
    " and ": " ve ",
    "<b>{n}</b> expired": "<b>{n}</b> süresi dolmuş",
    "<b>{n}</b> expiring soon": "<b>{n}</b> yakında sona erecek",
    "⚠ {parts} entry/entries need attention": ("⚠ {parts} kayıt dikkat gerektiriyor"),
    "<b>{entries}</b> entries across <b>{groups}</b> groups": (
        "<b>{entries}</b> kayıt, <b>{groups}</b> grupta"
    ),
    "🌐 {n} with URLs": "🌐 {n} URL’li",
    "🔑 {n} with TOTP": "🔑 {n} TOTP’li",
    "🏷 {n} with tags": "🏷 {n} etiketli",
    "📎 {n} with attachments": "📎 {n} ekli",
    "📋 {n} with custom fields": "📋 {n} özel alanlı",
    # ── New entry dialog ──────────────────────────────────────────────
    "New Entry": "Yeni Kayıt",
    "Required": "Zorunlu",
    "https://": "https://",
    "Comma-separated tags": "Virgülle ayrılmış etiketler",
    "otpauth://… or base32 secret": "otpauth://… veya base32 gizli anahtar",
    "Notes": "Notlar",
    "Never expires": "Süresi dolmaz",
    "Expires on": "Belirli tarihte",
    "Hide": "Gizle",
    "Generate": "Oluştur",
    "Group": "Grup",
    "Title": "Başlık",
    "Username": "Kullanıcı adı",
    "Password": "Şifre",
    "URL": "URL",
    "Tags": "Etiketler",
    "Expiry": "Son kullanma",
    "Expiry date": "Bitiş tarihi",
    "Create": "Oluştur",
    "Title is required.": "Başlık zorunludur.",
    # ── Entry detail ──────────────────────────────────────────────────
    "Strength": "Güç",
    "Custom fields": "Özel alanlar",
    "Key": "Anahtar",
    "Value": "Değer",
    "Copy": "Kopyala",
    "Copy password": "Şifreyi kopyala",
    "Add field": "Alan ekle",
    "Remove field": "Alanı kaldır",
    "Save entry": "Kaydı kaydet",
    "Copy key": "Anahtarı kopyala",
    "Copy value": "Değeri kopyala",
    "Empty": "Boş",
    "Strong": "Güçlü",
    "Good": "İyi",
    "Fair": "Orta",
    "Weak": "Zayıf",
    "Very Weak": "Çok Zayıf",
    "⚠ Expires today!": "⚠ Bugün sona eriyor!",
    "⚠ Expired {days} day(s) ago": "⚠ {days} gün önce süresi doldu",
    "⏰ Expires in {days} day(s)": "⏰ {days} gün içinde sona eriyor",
    "📅 Expires in {days} day(s)": "📅 {days} gün içinde sona eriyor",
    "✓ Expires in {days} day(s)": "✓ {days} gün içinde sona eriyor",
    "API key / token": "API anahtarı / jeton",
    "Passphrase (optional)": "Parola (isteğe bağlı)",
    "Card number": "Kart numarası",
    "Wi-Fi password": "Wi-Fi şifresi",
    "Key passphrase": "Anahtar parolası",
    "Database password": "Veritabanı şifresi",
    "Email address": "E-posta adresi",
    "SSH user / comment": "SSH kullanıcısı / açıklama",
    "Cardholder name": "Kart sahibi adı",
    "Client id (optional)": "İstemci kimliği (isteğe bağlı)",
    # ── Unlock / create database ──────────────────────────────────────
    "Create Database": "Veritabanı Oluştur",
    "Unlock Database": "Veritabanının Kilidini Aç",
    "Browse…": "Gözat…",
    "Master password": "Ana şifre",
    "Confirm password": "Şifreyi onayla",
    "Optional key file": "İsteğe bağlı anahtar dosyası",
    "…": "…",
    "Show password": "Şifreyi göster",
    "Database": "Veritabanı",
    "Confirm": "Onayla",
    "Key file": "Anahtar dosyası",
    "Unlock": "Kilidi Aç",
    "Create KDBX Database": "KDBX Veritabanı Oluştur",
    "Open KDBX Database": "KDBX Veritabanı Aç",
    "KeePass Database (*.kdbx)": "KeePass Veritabanı (*.kdbx)",
    "Select Key File": "Anahtar Dosyası Seç",
    "All Files (*)": "Tüm Dosyalar (*)",
    "Missing path": "Eksik yol",
    "Choose a database path.": "Bir veritabanı yolu seçin.",
    "Missing credentials": "Eksik kimlik bilgileri",
    "Provide a password and/or a key file.": (
        "Bir şifre ve/veya anahtar dosyası sağlayın."
    ),
    "Password mismatch": "Şifre uyuşmazlığı",
    "Passwords do not match.": "Şifreler eşleşmiyor.",
    # ── Filter bar ────────────────────────────────────────────────────
    "Filter": "Filtre",
    "Group contains…": "Grup içerir…",
    "Group path filter": "Grup yolu filtresi",
    "Tag…": "Etiket…",
    "Tag filter": "Etiket filtresi",
    "Custom/OTP": "Özel/OTP",
    "Dupes": "Yinelenenler",
    "Expired": "Süresi dolmuş",
    "Expiring": "Süresi dolacak",
    "Recycle": "Çöp",
    "Has URL": "URL var",
    "Has custom fields or OTP": "Özel alanlar veya OTP var",
    "Weak passwords": "Zayıf şifreler",
    "Empty passwords": "Boş şifreler",
    "Duplicates": "Yinelenenler",
    "Past expiry date": "Son kullanma tarihi geçmiş",
    "Expiring within 30 days": "30 gün içinde sona erecek",
    "Recycle Bin only": "Yalnızca Çöp Kutusu",
    "Apply": "Uygula",
    "Clear": "Temizle",
    # ── Password Health / Security Dashboard ──────────────────────────
    "No database open": "Açık veritabanı yok",
    "Health: %p%": "Sağlık: %p%",
    "Severity": "Önem",
    "Finding": "Bulgu",
    "Refresh audit": "Denetimi yenile",
    "Refresh password audit": "Şifre denetimini yenile",
    "Refresh": "Yenile",
    "Refresh security dashboard": "Güvenlik panosunu yenile",
    "Security Dashboard": "Güvenlik Panosu",
    "Security Dashboard…": "Güvenlik Panosu…",
    "Security Score": "Güvenlik Skoru",
    "Password Statistics": "Parola İstatistikleri",
    "Duplicate Password Report": "Yinelenen Parola Raporu",
    "Password Age": "Parola Yaşı",
    "Expired Passwords": "Süresi Dolan Parolalar",
    "Entropy Analysis": "Entropi Analizi",
    "Password Length Distribution": "Parola Uzunluk Dağılımı",
    "Category Analysis": "Kategori Analizi",
    "OTP Analysis": "OTP Analizi",
    "Tags Analysis": "Etiket Analizi",
    "Username Analysis": "Kullanıcı Adı Analizi",
    "URL Analysis": "URL Analizi",
    "Certificate Analysis": "Sertifika Analizi",
    "SSH Analysis": "SSH Analizi",
    "Favorites": "Favoriler",
    "Database Health": "Veritabanı Sağlığı",
    "Risk Matrix": "Risk Matrisi",
    "Recommendations": "Öneriler",
    "Excellent": "Mükemmel",
    "Needs Attention": "Dikkat Gerekli",
    "High": "Yüksek",
    "Medium": "Orta",
    "Low": "Düşük",
    "With OTP": "OTP var",
    "Without OTP": "OTP yok",
    "Critical without OTP": "Kritik kayıtlarda OTP yok",
    "Untagged": "Etiketsiz",
    "Reused passwords": "Yeniden kullanılan parolalar",
    "Most reused": "En çok kullanılan",
    "Total reuses": "Toplam yeniden kullanım",
    "Passphrase protected": "Parola korumalı",
    "Total files": "Toplam dosya",
    "Tagged favorites": "Etiketli favoriler",
    "Recently accessed": "Son erişilenler",
    "No favorites tagged": "Favori etiketi yok",
    "No recent access data": "Son erişim verisi yok",
    "No duplicate passwords detected.": "Yinelenen parola bulunamadı.",
    "Entries": "Kayıtlar",
    "OTP": "OTP",
    "Certificates": "Sertifikalar",
    "SSH keys": "SSH anahtarları",
    "Average": "Ortalama",
    "Minimum": "Minimum",
    "Maximum": "Maksimum",
    "Expiring soon": "Yakında dolacak",
    "Total": "Toplam",
    "Other": "Diğer",
    "Admin": "Admin",
    "Reused": "Yeniden kullanılan",
    "OTP coverage": "OTP kapsamı",
    "Open entry": "Kaydı aç",
    "Open the selected finding's entry": "Seçili bulgunun kaydını aç",
    "Fix next": "Sonrakini düzelt",
    "Critical: {critical}  ·  Warning: {warning}  ·  Info: {info}  ·  Healthy: {ok}": (
        "Kritik: {critical}  ·  Uyarı: {warning}  ·  Bilgi: {info}  ·  Sağlıklı: {ok}"
    ),
    "Entries: {total} · Empty: {empty} · Weak: {weak} · "
    "Low entropy: {entropy} · Duplicates: {dupes} · Findings: {findings}": (
        "Kayıtlar: {total} · Boş: {empty} · Zayıf: {weak} · "
        "Düşük entropi: {entropy} · Yinelenen: {dupes} · Bulgular: {findings}"
    ),
    # ── Attachments ───────────────────────────────────────────────────
    "No attachment selected": "Ek seçilmedi",
    "Add…": "Ekle…",
    "Remove": "Kaldır",
    "Save as…": "Farklı kaydet…",
    "Attachments (drop files here)": "Ekler (dosyaları buraya bırakın)",
    "Save attachment": "Eki kaydet",
    "Save failed": "Kaydetme başarısız",
    "Binary attachment (hex preview):\n": "İkili ek (hex önizleme):\n",
    # ── History ───────────────────────────────────────────────────────
    "No history for this entry.": "Bu kayıt için geçmiş yok.",
    "Restore selected revision": "Seçili sürümü geri yükle",
    "Reveal secrets": "Gizlileri göster",
    "Hide secrets": "Gizlileri gizle",
    "Revisions": "Sürümler",
    "Snapshot / diff vs newer": "Anlık görüntü / yenisiyle fark",
    "Revision {index}": "Sürüm {index}",
    "Diff vs newer revision:": "Daha yeni sürümle fark:",
    "Modified:": "Değiştirilme:",
    "OTP:": "OTP:",
    "Notes:": "Notlar:",
    # ── Common QMessageBox titles ─────────────────────────────────────
    "Missing file": "Dosya bulunamadı",
    "Unlock failed": "Kilit açma başarısız",
    "Invalid password or key file.": "Geçersiz şifre veya anahtar dosyası.",
    "Open failed": "Açma başarısız",
    "Create failed": "Oluşturma başarısız",
    "Import": "İçe aktar",
    "Import failed": "İçe aktarma başarısız",
    "Export": "Dışa aktar",
    "Export failed": "Dışa aktarma başarısız",
    "Export CSV": "CSV Dışa Aktar",
    "Import CSV": "CSV İçe Aktar",
    "CSV Files (*.csv)": "CSV Dosyaları (*.csv)",
    "Credentials": "Kimlik bilgileri",
    "Credential change failed": "Kimlik bilgisi değişikliği başarısız",
    "Add group": "Grup ekle",
    "Add group failed": "Grup ekleme başarısız",
    "New Group": "Yeni Grup",
    "Group name:": "Grup adı:",
    "Rename Group": "Grubu Yeniden Adlandır",
    "New name:": "Yeni ad:",
    "Rename failed": "Yeniden adlandırma başarısız",
    "Recycle Bin": "Çöp Kutusu",
    "Move the selected group to the Recycle Bin?": (
        "Seçili grup Çöp Kutusuna taşınsın mı?"
    ),
    "Delete group failed": "Grup silme başarısız",
    "Properties": "Özellikler",
    "Restore revision": "Sürümü geri yükle",
    "Restore this historical revision? Current values are saved to history first.": (
        "Bu geçmiş sürüm geri yüklensin mi? Geçerli değerler önce geçmişe kaydedilir."
    ),
    "Restore failed": "Geri yükleme başarısız",
    "Read-only mode": "Salt okunur mod",
    "This session is read-only. Disable it in Security & Appearance.": (
        "Bu oturum salt okunur. Security & Appearance ayarlarından kapatın."
    ),
    "No database is open.": "Açık veritabanı yok.",
    "Open a database first.": "Önce bir veritabanı açın.",
    "Add failed": "Ekleme başarısız",
    "Template": "Şablon",
    "Template failed": "Şablon başarısız",
    "Delete permanently": "Kalıcı olarak sil",
    "Delete failed": "Silme başarısız",
    "Empty Recycle Bin": "Çöp Kutusunu Boşalt",
    "Permanently delete all recycled entries?": (
        "Geri dönüştürülmüş tüm kayıtlar kalıcı olarak silinsin mi?"
    ),
    "Empty bin failed": "Çöp kutusu boşaltma başarısız",
    "Update failed": "Güncelleme başarısız",
    "Attachment failed": "Ek işlemi başarısız",
    "Remove failed": "Kaldırma başarısız",
    "Unsaved changes": "Kaydedilmemiş değişiklikler",
    "Save this database before closing?": (
        "Kapatmadan önce bu veritabanı kaydedilsin mi?"
    ),
    "Export includes secrets": "Dışa aktarım gizli bilgiler içerir",
    "The CSV file will contain passwords and OTP secrets in plain text. Continue?": (
        "CSV dosyası şifreleri ve OTP gizli anahtarlarını "
        "düz metin olarak içerecektir. Devam edilsin mi?"
    ),
    # ── Auto-Type / Move / Favicon ────────────────────────────────────
    "Select an entry first.": "Önce bir kayıt seçin.",
    "No Auto-Type backend found. Install xdotool, ydotool, or wtype.": (
        "Otomatik yazma arka ucu bulunamadı. xdotool, ydotool veya wtype kurun."
    ),
    "Focus the target window, then confirm.\nDelay before typing (ms):": (
        "Hedef pencereye odaklanın, ardından onaylayın.\nYazmadan önceki gecikme (ms):"
    ),
    "Auto-Type failed": "Otomatik yazma başarısız",
    "Auto-Type failed unexpectedly. Secrets were not shown in this dialog.": (
        "Otomatik yazma beklenmedik şekilde başarısız oldu. "
        "Gizli bilgiler bu iletişim kutusunda gösterilmedi."
    ),
    "Move Entry": "Kaydı Taşı",
    "Target group:": "Hedef grup:",
    "Move failed": "Taşıma başarısız",
    "Move Entry to Group…": "Kaydı Gruba Taşı…",
    "Favicon": "Favicon",
    "Selected entry has no URL.": "Seçili kaydın URL’si yok.",
    "Could not fetch favicon: {exc}": "Favicon alınamadı: {exc}",
    "No favicon found for this URL.": "Bu URL için favicon bulunamadı.",
    # ── Merge / Emergency / Updates / SSH ─────────────────────────────
    "Merge": "Birleştir",
    "Merge failed": "Birleştirme başarısız",
    "Open a destination database first.": "Önce bir hedef veritabanı açın.",
    "Emergency Sheet": "Acil Durum Sayfası",
    "Emergency sheet failed": "Acil durum sayfası başarısız",
    "Save Emergency Sheet": "Acil Durum Sayfasını Kaydet",
    "HTML Files (*.html)": "HTML Dosyaları (*.html)",
    "Update check": "Güncelleme denetimi",
    "Update available": "Güncelleme mevcut",
    "Up to date": "Güncel",
    "Update available: {latest} (you have {current})": (
        "Güncelleme mevcut: {latest} (sizin sürümünüz: {current})"
    ),
    "Installed version: {current}\nGitHub version: {latest}\nSource: {source}": (
        "Yüklü sürüm: {current}\nGitHub sürümü: {latest}\nKaynak: {source}"
    ),
    "A newer version is available on GitHub.\n\n{detail}\n\nOpen the release page?": (
        "GitHub’da daha yeni bir sürüm var.\n\n{detail}\n\nSürüm sayfası açılsın mı?"
    ),
    "KDBXStudio is up to date.\n\n{detail}": ("KDBXStudio güncel.\n\n{detail}"),
    "Your installed version is newer than the version on GitHub.\n\n{detail}": (
        "Yüklü sürümünüz GitHub’daki sürümden daha yeni.\n\n{detail}"
    ),
    "KDBXStudio {version} is up to date": "KDBXStudio {version} güncel",
    "GitHub Release": "GitHub Release",
    "GitHub Tag": "GitHub Etiketi",
    "GitHub repository": "GitHub deposu",
    "Version": "Sürüm",
    "Use Tools → Check for Updates… to compare with GitHub.": (
        "GitHub ile karşılaştırmak için Araçlar → Güncellemeleri Denetle… kullanın."
    ),
    "SSH Agent": "SSH Agent",
    "Could not extract private key PEM.": ("Özel anahtar PEM’si çıkarılamadı."),
    "About KDBXStudio": "KDBXStudio Hakkında",
    # ── Command palette labels ────────────────────────────────────────
    "Command Palette": "Komut Paleti",
    "Lock All": "Tümünü Kilitle",
    "Auto-Type Selected Entry": "Seçili Kaydı Otomatik Yaz",
    "Plugin Marketplace…": "Eklenti Mağazası…",
    "Security & Appearance…": "Güvenlik ve Görünüm…",
    "Focus Search": "Aramaya Odaklan",
    # ── Misc short phrases ────────────────────────────────────────────
    "Root": "Kök",
    "Cancel": "İptal",
    "Ok": "Tamam",
    "OK": "Tamam",
    "Yes": "Evet",
    "No": "Hayır",
    "Discard": "Vazgeç",
    "critical": "kritik",
    "warning": "uyarı",
    "info": "bilgi",
    "Healthy": "Sağlıklı",
    "Warning": "Uyarı",
    "Info": "Bilgi",
    "Low entropy": "Düşük entropi",
    "entries": "kayıt",
    "entry": "kayıt",
    "Deleted": "Silindi",
    "Moved to Recycle Bin": "Çöp Kutusuna taşındı",
    "Database no longer exists:\n{path}": ("Veritabanı artık mevcut değil:\n{path}"),
    "Save {count} database(s) with unsaved changes before quitting?": (
        "Çıkmadan önce kaydedilmemiş değişikliği olan "
        "{count} veritabanı kaydedilsin mi?"
    ),
    "Permanently delete {count} selected entry?": (
        "{count} seçili kayıt kalıcı olarak silinsin mi?"
    ),
    "Permanently delete {count} selected entries?": (
        "{count} seçili kayıt kalıcı olarak silinsin mi?"
    ),
    "Move {count} selected entry to the Recycle Bin?": (
        "{count} seçili kayıt Çöp Kutusuna taşınsın mı?"
    ),
    "Move {count} selected entries to the Recycle Bin?": (
        "{count} seçili kayıt Çöp Kutusuna taşınsın mı?"
    ),
    "Generated password applied to entry (save to keep)": (
        "Üretilen şifre kayda uygulandı (kalıcı olması için kaydedin)"
    ),
    "Generated password copied to clipboard": ("Üretilen şifre panoya kopyalandı"),
    "Revision restored (save database to persist)": (
        "Sürüm geri yüklendi (kalıcı olması için veritabanını kaydedin)"
    ),
    "Health Fix Wizard": "Sağlık Düzeltme Sihirbazı",
    "Walk through security findings one by one": (
        "Güvenlik bulgularını tek tek gözden geçirin"
    ),
    "Finding {n} of {total}": "Bulgu {n} / {total}",
    "All findings reviewed": "Tüm bulgular gözden geçirildi",
    "No more actionable findings.": "Düzeltilecek başka bulgu yok.",
    "Skip": "Atla",
    "Fix": "Düzelt",
    "Generate password": "Şifre üret",
    "Done": "Bitti",
    "Import custom theme…": "Özel tema içe aktar…",
    "Import theme JSON": "Tema JSON içe aktar",
    "Theme JSON (*.json)": "Tema JSON (*.json)",
    "Import theme": "Tema içe aktar",
    "Custom theme loaded. Save settings to apply.": (
        "Özel tema yüklendi. Uygulamak için ayarları kaydedin."
    ),
    "High Contrast": "Yüksek Kontrast",
    "High Contrast Light": "Yüksek Kontrast Açık",
    "Custom": "Özel",
    "Expires today": "Bugün sona eriyor",
    "Expires in {label}": "{label} içinde sona eriyor",
    "Expired {label}": "{label} önce sona erdi",
    "Panels": "Paneller",
    "No attachments": "Ek yok",
    "Drop files here or use Add…": "Dosyaları buraya bırakın veya Ekle… kullanın",
    "KDBXStudio — locked": "KDBXStudio — kilitli",
    "Password Generator": "Şifre Üreteci",
    "Generate a strong unique password": "Güçlü ve benzersiz bir şifre üretin",
    "Use password": "Şifreyi kullan",
    "Charset": "Karakter seti",
    "~{bits:.0f} bits ({n} symbol alphabet)": "~{bits:.0f} bit ({n} sembollü alfabe)",
}
