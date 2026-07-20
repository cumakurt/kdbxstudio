# Kapsamlı Uygulama Denetimi ve Otomatik İyileştirme

Bu projeyi kıdemli bir yazılım mimarı, güvenlik uzmanı, UX/UI tasarımcısı ve kalite mühendisi gibi baştan sona incele.

## Temel hedef

Uygulamayı aşağıdaki açılardan değerlendir ve tespit ettiğin doğrulanabilir sorunları doğrudan kod üzerinde düzelt:

1. Kod kalitesi
2. İş mantığı ve fonksiyonel doğruluk
3. Mimari yapı
4. Güvenlik
5. Performans
6. Kullanıcı deneyimi
7. Görsel tasarım ve tutarlılık
8. Erişilebilirlik
9. Responsive tasarım
10. Test edilebilirlik
11. Bakım kolaylığı
12. Gerçek ortamda uygulanabilirlik

## Çalışma yöntemi

Önce repository yapısını, README dosyalarını, AGENTS.md talimatlarını, bağımlılıkları, yapılandırmaları ve mevcut testleri incele.

Uygulamanın ne yaptığını ve ana kullanıcı akışlarını koddan çıkar.

Ardından projeyi mümkünse çalıştır ve şu işlemleri uygula:

* Bağımlılıkları kur.
* Build işlemini çalıştır.
* Lint ve type-check çalıştır.
* Mevcut testleri çalıştır.
* Uygulamayı tarayıcıda aç.
* Temel kullanıcı akışlarını deneyerek doğrula.
* Konsol, ağ ve çalışma zamanı hatalarını kontrol et.
* Arayüzü masaüstü, tablet ve mobil boyutlarda incele.

## Denetim kriterleri

### Kod kalitesi

Şunları kontrol et:

* Gereksiz tekrarlar
* Aşırı uzun dosya ve fonksiyonlar
* Karmaşık veya anlaşılması güç kod
* Yanlış isimlendirme
* Kullanılmayan kod ve bağımlılıklar
* Hatalı null veya hata yönetimi
* Tip güvenliği sorunları
* Sabit kodlanmış değerler
* Ayrıştırılması gereken bileşenler
* SOLID, DRY ve separation of concerns ihlalleri

### İş mantığı

Şunları kontrol et:

* Eksik veya hatalı kullanıcı akışları
* Sınır durumları
* Yanlış koşullar
* Tutarsız durum yönetimi
* Yarış koşulları
* Tekrarlanan işlemler
* Hatalı veri doğrulama
* Yetkisiz işlem ihtimalleri
* Başarısız API çağrılarında uygulama davranışı
* Boş, hatalı veya beklenmeyen veriler

### Güvenlik

Şunları kontrol et:

* Kimlik doğrulama ve yetkilendirme
* Girdi doğrulama
* XSS, CSRF, SQL/NoSQL injection ve command injection
* Path traversal ve dosya yükleme sorunları
* Açık anahtar, parola veya tokenlar
* Hassas verilerin loglanması
* Güvensiz dependency kullanımı
* Hatalı CORS ve güvenlik başlıkları
* Rate limiting eksikliği
* İstemci tarafına sızdırılan gizli bilgiler

Gizli değerleri tahmin etme veya uydurma. Eksik secret değerlerini yalnızca örnek `.env.example` değişkenleri olarak tanımla.

### UI/UX ve görsel tasarım

Şunları kontrol et:

* Renk, boşluk, tipografi ve hizalama tutarlılığı
* Görsel hiyerarşi
* Buton ve form durumları
* Loading, empty, success ve error durumları
* Kullanıcıya verilen geri bildirimler
* Mobil görünüm
* Taşma ve kırılmalar
* Kontrast
* Klavye erişimi
* Focus durumları
* Form etiketleri
* ARIA kullanımı
* Gereksiz veya kafa karıştırıcı ekran öğeleri

Mevcut tasarım dilini tamamen değiştirme. Onu daha profesyonel, modern, tutarlı ve kullanılabilir hale getir.

## Otomatik düzeltme kuralları

Tespit ettiğin sorunları yalnızca raporlamakla kalma; güvenli olanları doğrudan düzelt.

Ancak:

* Çalışan özellikleri gereksiz yere yeniden yazma.
* Projenin teknoloji yığınını sebepsiz değiştirme.
* Büyük ve riskli mimari değişiklikler yapma.
* Public API sözleşmelerini zorunlu olmadıkça bozma.
* Veritabanında geri dönüşü olmayan değişiklik yapma.
* Gerçek secret, parola veya üretim verisi oluşturma.
* Sorunu doğrulamadan varsayıma dayalı değişiklik yapma.

Her değişiklikten sonra ilgili testleri çalıştır. Bir düzeltme yeni hata oluşturursa değişikliği düzelt veya geri al.

## Test gereksinimleri

Düzelttiğin kritik mantık için test ekle veya mevcut testleri güncelle.

En az şu durumları kapsa:

* Başarılı temel akış
* Geçersiz girdi
* Boş veri
* API hatası
* Yetkisiz erişim
* Sınır durumları
* Düzeltilen hatanın tekrar oluşmasını engelleyen regression testi

Testleri yalnızca geçmesi için zayıflatma. Testleri silme veya hataları gizleme.

## Öncelik sırası

Sorunları şu sıraya göre ele al:

1. Kritik güvenlik açıkları
2. Veri kaybı veya bozulması
3. Uygulamanın çalışmasını engelleyen hatalar
4. Yanlış iş mantığı
5. Build, type ve test hataları
6. Performans sorunları
7. UX ve erişilebilirlik sorunları
8. Görsel tutarsızlıklar
9. Kod temizliği

## Tamamlanma kriterleri

Görevi ancak aşağıdaki koşullar mümkün olduğu ölçüde sağlandığında tamamlanmış kabul et:

* Proje build ediliyor.
* Type-check geçiyor.
* Lint kritik hata vermiyor.
* Testler geçiyor.
* Ana kullanıcı akışları çalışıyor.
* Tarayıcı konsolunda kritik hata bulunmuyor.
* Kritik ve yüksek öncelikli güvenlik sorunları giderilmiş.
* Mobil ve masaüstü görünümleri kullanılabilir.
* Yapılan değişiklikler mevcut özellikleri bozmuyor.

## Sonuç raporu

Çalışmanın sonunda kısa ve somut bir rapor ver:

### Yapılan düzeltmeler

Değiştirilen dosyaları ve düzeltmeleri belirt.

### Tespit edilen sorunlar

Kritik, yüksek, orta ve düşük olarak sınıflandır.

### Test sonuçları

Çalıştırılan komutları ve sonuçlarını yaz.

### Kalan riskler

Otomatik olarak güvenle çözülemeyen sorunları açıkla.

### Manuel kontrol gerekenler

İnsan tarafından doğrulanması gereken noktaları belirt.

Kanıtlayamadığın bir işlemi yapılmış veya başarılı olarak gösterme. Çalıştıramadığın testleri açıkça belirt.
