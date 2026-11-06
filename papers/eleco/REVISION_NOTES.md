# Hakem maddelerine karşılık yapılan düzenlemeler

1. **Kod–model eşleşmesi:** İkinci dereceden terim ve `RB_DRIFT_PER_DAY`
   kaldırıldı. İşaretli `holdover_frequency_error` parametresi eklendi.
   Grafikler elle yazılmış LaTeX fonksiyonları yerine modelden üretilen CSV'leri
   kullanıyor. Kaynak commit, dosya özetleri ve sürüm etiketi belgelendi.
   İstemci izinde fark edilen, holdover girişinde ölçüm değişiminin iki kez
   eklenmesi de düzeltildi; faz sürekliliği regresyon testi eklendi.
2. **Doğrulama sınırı:** Özetler, giriş, doğrulama, şekil açıklamaları ve
   sınırlamalar değiştirildi. Zamansal donanım doğrulaması yapıldığı izlenimi
   kaldırıldı; yüksek doğruluk, sınırlı kanıtı olan bir tasarım hedefi olarak
   tanımlandı. Nitel operatör gözlemi nicel ölçümden ayrıldı.
3. **Pratik katkı ve kapsam:** Ayrı süreçte çalışan yeni bir pySerial izleme
   istemcisiyle 62 saniyelik holdover/alarm/recovery testi yapıldı. Bunun
   mevcut saha uygulaması testi olmadığı açıklandı. 66/50/16 sayım yöntemi,
   eksik sorgular ve etkiledikleri işlevler tablo ve CSV ile sunuldu.
4. **Semboller ve birimler:** Denklem (2)'deki tüm semboller, altın oran,
   kanal fazı, ağırlıklar ve periyot açıklandı. Holdover süresi `t`, simülatör
   çalışma süresi `t_u`, soğuk açılış süresi `t_w` olarak ayrıldı; hesaplar
   saniye, grafikler saat/dakika kullanıyor. EFC katsayısı ppt/% olarak verildi.
5. **Terimler ve TINT:** Belirsiz “önceki sürüm” ifadesi kaldırıldı. GPSDO ve
   CSAC ilk kullanımda açıldı. Kimlik yanıtındaki GPSDO yazımı düzeltildi.
   TINT değişim aralığı ölçüm doğruluğundan ayrıldı. Yeni kapsam tablosu
   nedeniyle eski Çizelge 2 karşılaştırması revizyonda Çizelge 3 oldu.

Ek donanım zaman serisi veya mevcut saha istemcisi sağlanmadığı için bu
alanlarda sonuç uydurulmadı; yeni örnek ve kanıt sınırı açıkça yazıldı.
