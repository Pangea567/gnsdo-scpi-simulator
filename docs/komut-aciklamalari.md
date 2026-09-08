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

## DIAG — Tanı (diagnostic) komutları

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


## SERVO — Disiplin döngüsü komutları

Cihazın içinde iki tane **kontrol döngüsü** (servo loop) var. Bunların işi,
osilatörün frekansını sürekli ince ayar yaparak referansa kilitli tutmak:

- **Rubidyum döngüsü:** Rubidyum osilatörü GNSS 1PPS'ine kilitler
- **Filtre döngüsü:** Filtre OCXO'sunu Rubidyum'a kilitler

| Komut | Ne yapar |
|---|---|
| `SERV:STATE?` | Cihazın hangi aşamada olduğunu söyler (aşağıya bakın) |
| `SERV?` | Döngü ayarlarının tamamının özeti (kazanç, sönümleme, filtre uzunluğu vb.) |

### `SERV:STATE?` — neden önemli

Cihaz açılıştan kilide **tek adımda geçmez**:

| Değer | Anlamı |
|---|---|
| `0` | Osilatör ısınıyor |
| `2` | Kilitleniyor — atomik kilit sağlandı, GNSS'e kilitlenme eğitimi sürüyor |
| `6` | Kilitli, GNSS aktif |
| `5` | Holdover ama hâlâ faz kilitli (GNSS kaybından sonraki ~100 saniye) |
| `1` | Holdover |

`SYNC:LOCKED?` yalnızca `1`/`0` döner, yani **`0` ile `2`'yi ayırt edemez**.
İzleme yazılımı "neden hâlâ kilitlenmedi?" sorusuna ancak `SERV:STATE?` ile
cevap verebilir: cihaz henüz mü ısınıyor, yoksa ısındı da GNSS'e mi
kilitlenemiyor?

## GYRO — İvmeölçer komutları

Cihazda opsiyonel bir ivmeölçer var. Amacı süslü değil, tamamen pratik:
**bir osilatörün frekansı üzerine etki eden g-kuvvetine duyarlıdır**
("g-sensitivity"). Uçakta, araçta veya titreşimli bir ortamda bu etki
ölçülebilir bir frekans hatası yaratır. Cihaz ivmeyi ölçüp bu hatayı
yazılımla telafi edebiliyor.

| Komut | Ne yapar |
|---|---|
| `GYRO?` | Mod, kalibrasyon, g-duyarlılık, g-yükü ve port bilgisinin özeti |
| `GYRO:GLOAD?` | Üç eksendeki anlık g-kuvveti (`x,y,z`) |
| `GYRO:PORT?` | İvmeölçerin bağlı olduğu seri arayüz |

`GYRO:GLOAD?` çıktısında **Z ekseni yaklaşık `-1`** çıkar — cihaz düz
duruyorsa ölçtüğü şey yerçekimidir.

## Sistem / kimlik komutları

**`*IDN?`** → "Kimsin?" Üretici, model ve firmware bilgisini döndüren
standart SCPI kimlik komutu.

**`HELP?`** → Simülatörün tanıdığı tüm komutların listesi. Bu liste elle
tutulmaz; parser'ın gerçekten kayıtlı komutlarından otomatik üretilir.

**`SYST:STAT?`** → Cihazın çok satırlı "gösterge paneli" raporu: başlık,
uydu tablosu, konum/UTC ve sağlık özeti (GPSDO Status: Locked / Holdover /
Warming Up / Not Locked / Fault).


---

## Sonradan eklenen sorgular

Aşağıdaki komutlar, cihazın zaten modellediği ama başlangıçta tek başına
sorulamayan değerlerini dışarı açar. Hepsi özet çıktılarla **aynı kaynaktan**
okur, dolayısıyla özet ile tekil sorgu birbiriyle çelişemez.

### SYNC

| Komut | Ne yapar |
|---|---|
| `SYNC:FEE?` | Frekans hata tahmini. Holdover'da hatanın **ne hızla** birikeceğini belirleyen değer |
| `SYNC:HOLD:STATE?` | Holdover'da mıyız (`1`/`0`) |
| `SYNC:SOUR:STATE?` | Aktif 1PPS kaynağı |
| `SYNC:TINT:CSAC?` | Rubidyum 1PPS ↔ GNSS 1PPS farkı — **holdover'da biriken** değer |
| `SYNC:TINT:FILTER?` | Filtre OCXO 1PPS ↔ Rubidyum 1PPS farkı — **holdover'da birikmez** |
| `SYNC:TINT:THRESHOLD?` | Jam-sync eşiği (ns) |
| `SYNC:OUT:FILTER?` | Faz gürültü filtresi açık mı |
| `SYNC:OUT:1PPS:RESET?` | Reset'te 1PPS üretilsin mi |
| `SYNC:OUT:1PPS:DOMAIN?` | 1PPS çıkışı hangi osilatörden alınıyor |

**İki TINT'i karıştırmayın.** Biri Rubidyum'u GNSS'e kıyaslar, diğeri filtre
osilatörünü Rubidyum'a. GNSS kaybolunca **birincisi** birikir; ikincisi
birikmez, çünkü o döngü GNSS'e değil Rubidyum'a kilitlidir ve o çalışmaya
devam eder.

### DIAG

| Komut | Ne yapar |
|---|---|
| `DIAG:ROSC:EFC:REL?` | Elektronik frekans kontrolü, yüzde (−100…+100) |
| `DIAG:ROSC:EFC:ABS?` | Aynı büyüklük, parts-per-trillion cinsinden |

Bu ikisi **bağımsız değil**: `Absolute = Relative × 200`. Asıl değer tam sayı
olan `Absolute`, yüzde ondan hesaplanıyor.

### GPS

| Komut | Ne yapar |
|---|---|
| `GPS:POSITION?` | Konum, yükseklik, hız, yön |
| `GPS:POSITION:ECEF?` | Konum, yer merkezli kartezyen koordinatlarda |
| `GPS:JAMLEVEL?` | Girişim (jamming) seviyesi, 0–255 |
| `GPS:FWVER?` | GNSS alıcısının yazılım sürümü |
| `GPS:SURVEY:STATUS?` | Konum belirleme (survey) durumu |
| `GPS:DYNAMIC:MODE?` / `:STATE?` | Hareket profili modu ve algılanan durum |
| `GPS:REF:PULSE:SAWTOOTH?` | Testere dişi hatası (ns) |
| `GPS:REF:ADELAY?` | Anten kablosu gecikmesi (s) |

**Survey nedir:** Sabit kurulumlarda cihaz önce uzun bir ölçümle kendi
konumunu belirler, sonra o konumu sabitleyip *tüm* uydu sinyalini zaman
doğruluğu için kullanır. Timing uygulamalarında doğruluğu ciddi ölçüde artırır.

**Testere dişi (sawtooth) hatası:** Alıcının 1PPS darbesi iç saatinin
adımlarına yuvarlanır; bu yuvarlama her darbede bilinen bir hata bırakır.
Alıcı bu hatayı bildirir, isteyen düzeltir.

### CSAC

`CSAC?` özetindeki her alan tek başına da sorulabilir: `CSAC:RS232?`,
`CSAC:STEER?`, `CSAC:MODE?`, `CSAC:TEC?`, `CSAC:TCXO?`, `CSAC:SIG?`,
`CSAC:HEAT?`, `CSAC:FW?`

Bir izleme yazılımı genelde tek bir değeri periyodik okur; her seferinde
13 satırlık özeti alıp ayrıştırmak hem gereksiz trafik hem de kırılgandır.

### PTIME — artı saniye

| Komut | Ne yapar |
|---|---|
| `PTIME:LEAP?` | Artı saniye bilgilerinin özeti |
| `PTIME:LEAP:PEND?` | Bekleyen bir artı saniye var mı |
| `PTIME:LEAP:DATE?` | Bekleyen olayın tarihi |
| `PTIME:LEAP:DUR?` | O günkü son dakikanın uzunluğu |

**Artı saniye nedir:** Dünyanın dönüşü düzensiz olduğu için, atomik zaman ile
astronomik zaman arasındaki fark büyüdüğünde UTC'ye bir saniye eklenir. Alıcı
bunu almanaktan öğrenip önceden haber verir — zaman kritik sistemler o anı
hazırlıklı karşılasın diye.

`PTIME:LEAP:DUR?` için **`60` = bekleyen olay yok** (normal dakika),
`61` = bir saniye eklenecek, `59` = çıkarılacak.

### Sistem

| Komut | Ne yapar |
|---|---|
| `SYST:ID?` / `:SN?` / `:HWREV?` | Seri numarası ve donanım revizyonu |
| `SYST:COMM:SER:ECHO <ON\|OFF>` | Cihaz aldığı karakterleri geri yansıtsın mı |
| `SYST:COMM:SER:PROMPT <ON\|OFF>` | Cevaplardan sonra komut istemi yazılsın mı |
| `SYST:COMM:SER:BAUD?` | Seri hız |

**Echo ve prompt neden var:** İkisi de terminalden elle komut yazan bir
*insan* için faydalıdır (yazdığını görürsün, istem seni bekler). Ama
*yazılım* için gürültüdür — gönderdiği her şeyi geri okur ve istem satırını
da cevap sanabilir. Bu yüzden varsayılan olarak kapalıdırlar.
