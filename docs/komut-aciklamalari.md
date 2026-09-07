# Komut Açıklamaları

Bu belge, simülatörün desteklediği SCPI komutlarının **ne işe yaradığını**
sade bir dille anlatır. Amaç: bir izleme/otomasyon yazılımı yazan biri
(ya da projeyi ilk kez inceleyen biri), her komutun gerçek bir GNSDO
cihazında ne anlama geldiğini hızlıca kavrayabilsin.

> Komutların tam listesi, kısa/uzun formları ve örnek çıktıları için
> ana [README](../README.md) dosyasındaki komut tablosuna bakın.

---

## Genel kavramlar

- **GNSDO** (GPS/GNSS Disciplined Oscillator): İçindeki hassas osilatörü
  (burada bir Rubidyum/CSAC atomik saat) sürekli olarak GPS zaman
  referansına göre "terbiye eden" (disipline eden) cihaz. Böylece hem
  GPS'in uzun vadeli doğruluğunu hem de atomik saatin kısa vadeli
  kararlılığını birlikte verir.
- **Lock (kilit):** Osilatörün GPS referansına başarıyla ayarlanmış,
  sağlıklı çalıştığı durum.
- **Holdover:** GPS sinyali kesildiğinde cihazın durmayıp, son bilinen
  doğru frekansı kullanarak idare etmeye devam etmesi. Zaman geçtikçe
  biriken hata büyür.
- **Query / Setter:** Sonu `?` ile biten komutlar **sorgudur** (bir değer
  okur). Sonu `?` ile bitmeyenler **setter'dır** (cihazın durumunu
  değiştirir), örn. `SYNC:HOLD:INIT`.

---

## SYNC — Senkronizasyon komutları

**`SYNC?`** → "Genel olarak durumun ne?" Cihazın senkronizasyonuyla ilgili
tüm önemli alanları (kaynak modu, kilit durumu, holdover durumu, frekans
hata tahmini, zaman aralığı farkı, sağlık kodu) tek seferde döndürür. Bir
izleme yazılımı bu tek komutla cihazın genel sağlığına hızlıca bakabilir.

**`SYNC:LOCKED?`** → Daha kesin/ikili bir soru: "Şu an GPS'e kilitli misin,
evet mi hayır mı?" Cevap sadece `1` ya da `0`. Otomasyon yazılımları
genelde böyle net evet/hayır cevaplarını tercih eder (metin ayrıştırmak
yerine).

**`SYNC:TINT?`** ("Time INTerval error") → "GPS referansıyla aranda şu an
kaç saniyelik fark var?" Gerçek cihazda bu, gerçek bir ölçüm devresinden
gelen çok küçük bir sayıdır (nanosaniye mertebesinde, bilimsel gösterimle).
Cihazın ne kadar hassas çalıştığının doğrudan göstergesidir — sayı ne kadar
küçükse cihaz o kadar iyi ayarlanmış demektir.

**`SYNC:HEALTH?`** → Sağlık durumu. Gerçek cihazda tek kelimelik bir metin
değil, bir **onaltılık (hex) bit-maskesidir**: her bit ayrı bir sorunu
işaret eder (faz farkı çok büyük, cihaz henüz yeni açılmış, holdover çok
uzun sürmüş, donanım arızası...). `0x0` = tamamen sağlıklı. Birden fazla
sorun varsa bitler birleştirilir.

**`SYNC:HOLD:INIT`** → Bir komut (setter), soru değil. Cihaza "şimdi
holdover'a geç" der. Neden gerekli? Test/geliştirme yaparken, GPS anteninin
kablosunu fiziksel olarak çıkarıp sinyali gerçekten kesmek yerine, cihaza
(ya da bu simülatöre) "GPS kaybolmuş gibi davran" demek çok daha pratiktir.
Yani test amaçlı bir tetikleyicidir.

**`SYNC:HOLD:REC:INIT`** ("Holdover RECovery INIT") → Tam tersi: "tamam, GPS
geri geldi, normale dön" komutu.

**`SYNC:HOLD:DUR?`** ("Holdover DURation") → "Ne zamandır holdover'dasın?"
GPS ne kadar uzun süre kayıpsa, cihazın biriktirdiği hata da o kadar büyür;
bu yüzden izleme yazılımları bu süreyi takip eder, çok uzun sürerse alarm
verir.

**`SYNC:SOUR:MODE <değer>`** ("SOURce MODE") → Cihaza "referans kaynağını
değiştir" der. Gerçek cihazlarda genelde birden fazla referans seçeneği
olur: `GPS` (normal), `EXTERNAL` (dışarıdan başka bir referans saat), ya da
`INTERNAL` (sadece kendi osilatörüne güven). Bu bir ayar komutudur, cihazın
çalışma modunu değiştirir.

---

## DIAG — Tanı (diagnostic) komutu

**`DIAG?`** ("Diagnostic") → Cihazın kendi kendini test etmesi / genel arıza
sorgusu. Neredeyse her profesyonel test/ölçüm cihazında böyle bir komut
bulunur: "Sende bilinen bir sorun var mı?" Bu cihazda cevap, osilatörün
elektronik frekans kontrolü (EFControl) değerlerini ve cihazın toplam
çalışma saatini (Lifetime) içerir. Bir izleme sistemi, her şeyi tek tek
kontrol etmek yerine tek bir `DIAG?` ile genel durumu görebilir.

**`DIAG:LIFE:COUN?`** → `DIAG?` içindeki "Lifetime" (cihazın ilk
açıldığından beri geçen toplam saat) değerini tek başına sorar. Bu değer
simülatörde gerçekten zamanla artar.

---

## MEAS — Ölçüm (measurement) komutları

**`MEAS?`** → Tüm ölçümleri birden döndürür: PCB sıcaklığı, CSAC sıcaklığı,
TCXO ayar voltajı ve güç kaynağı voltajı.

**`MEAS:TEMP?` / `MEAS:VOLT?` / `MEAS:CURR?` / `MEAS:POW?`** → Tek tek
ölçümler (sıcaklık, TCXO voltajı, akım/legacy ölçüm, güç kaynağı voltajı).
Bunlar çıplak sayı döndürür (etiketsiz), otomasyon için ayrıştırması kolay.

---

## GPS — Uydu/konum komutları

**`GPS?`** → GPS alıcısının ayrıntılı durumu: takip edilen/görünen uydu
sayıları, konum (enlem/boylam/yükseklik), fix durumu (3D Fix / No Fix),
survey bilgileri ve daha fazlası. GPS fix yokken konumla ilgili alanlar
sıfırlanır — tıpkı gerçek cihazdaki gibi.

**`GPS:SAT:TRAC:COUN?`** → Şu an kaç uydu **takip ediliyor** (tracking).

**`GPS:SAT:VIS:COUN?`** → Ufukta kaç uydu **görünüyor** (visible).

---

## PTIME — Zaman/tarih komutları

**`PTIME?`** → Tarih, saat, zaman aralığı farkı, çıkış durumu ve birikmiş
artık saniye (leap second) bilgisini bir arada verir.

**`PTIME:DATE?` / `PTIME:TIME?` / `PTIME:TIME:STRING?`** → Sadece tarih /
saat / okunabilir saat metni. Simülatör bunları sistem saatinden üretir.

**`PTIME:LEAP:ACC?`** → GPS zamanı ile UTC arasında birikmiş artık saniye
sayısı.

---

## CSAC — Atomik saat modülü komutları

**`CSAC?`** → Cihazın içindeki CSAC (Chip Scale Atomic Clock — çip
ölçekli atomik saat) modülünün ayrıntılı durumu: RS232 durumu, steer,
sıcaklık, seri numara, firmware ve toplam çalışma saati gibi 13 alan.
Gerçek cihazda `MAC?` komutu da birebir aynı çıktıyı verir (alias).

**`CSAC:STATUS?`** → Modülün kilitli/sağlıklı olup olmadığı (`0` = sağlıklı,
`1` = değil).

**`CSAC:TEMP?` / `CSAC:SN?` / `CSAC:LIFE?`** → CSAC sıcaklığı / seri numarası
/ toplam çalışma saati (tek tek).

---

## Sistem / kimlik komutları

**`*IDN?`** → "Kimsin?" Üretici, model ve firmware bilgisini döndüren
standart SCPI kimlik komutu.

**`HELP?`** → Simülatörün tanıdığı tüm komutların listesi. Bu liste elle
tutulmaz; parser'ın gerçekten kayıtlı komutlarından otomatik üretilir.

**`SYST:STAT?`** → Cihazın çok satırlı "gösterge paneli" raporu: başlık,
uydu tablosu, konum/UTC ve sağlık özeti (GPSDO Status: Locked / Holdover /
Warming Up / Not Locked / Fault).
