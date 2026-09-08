# GNSDO SCPI Cihaz Simülatörü

**Low Noise Rubidium GNSDO** (GPS/GNSS ile disipline edilen Rubidyum
osilatörlü zaman-frekans referans cihazı) donanımının **seri port
üzerinden SCPI davranışını** taklit eden, Linux tabanlı bir simülatördür.

Amaç: cihazla konuşacak izleme/otomasyon yazılımlarını **gerçek donanıma
ihtiyaç duymadan** geliştirmek ve test etmek. Simülatör, sanal bir seri
port dinler; ona bağlanan bir istemci, gerçek cihaza yazar gibi SCPI
komutları gönderir ve gerçekçi cevaplar alır.

> Bu proje bir TÜBİTAK yazılım geliştirme stajı kapsamında geliştirilmiştir.
> Komutların çıktı formatları, gerçek bir cihazdan alınmış örnek çıktılara
> ve cihazın kullanım kılavuzuna dayanır.

---

## İçindekiler

- [Ne işe yarar?](#ne-işe-yarar)
- [Öne çıkan özellikler](#öne-çıkan-özellikler)
- [Nasıl çalışır (mimari)](#nasıl-çalışır-mimari)
- [Fiziksel modeller](#fiziksel-modeller)
- [Kurulum](#kurulum)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Senaryolar](#senaryolar)
- [Desteklenen komutlar](#desteklenen-komutlar)
- [Örnek çıktılar](#örnek-çıktılar)
- [Testler](#testler)
- [Proje yapısı](#proje-yapısı)
- [Bilinçli basitleştirmeler](#bilinçli-basitleştirmeler)
- [Belgeler](#belgeler)
- [Yol haritası](#yol-haritası)
- [Lisans](#lisans)

---

## Ne işe yarar?

Gerçek bir GNSDO cihazı pahalıdır, tek bir tanedir ve her geliştiricinin
masasında bulunmaz. Cihazla konuşan bir yazılım geliştirirken şunlara
ihtiyaç duyarsınız:

- Cihaz "GPS'i kaybetti" (holdover) durumunda yazılım doğru davranıyor mu?
- Cihaz "yeni açıldı, ısınıyor" durumunda ne oluyor?
- Donanım arızası olduğunda alarm mekanizması çalışıyor mu?

Bunların hepsini gerçek cihazda tetiklemek zor ve risklidir (anten
kablosunu çıkarmak, cihazı kapatıp açmak vb.). Bu simülatör, bu durumların
her birini bir **senaryo** olarak, tek bir komutla ayağa kaldırmanızı
sağlar.

## Öne çıkan özellikler

- **Gerçek seri port protokolü:** `pyserial` ile 8N1, 115200 baud —
  kod, `/tmp/...` sanal portuyla da gerçek bir `/dev/ttyUSB0` cihazıyla da
  aynı şekilde çalışır.
- **Genişletilebilir komut kaydı:** Komutlar bir kayıt defterine (registry)
  fonksiyon olarak bağlanır; yeni komut eklemek için tek bir dosya yazıp
  `register_*` çağrısı eklemek yeterlidir, çekirdek koda dokunulmaz.
- **Kısa/uzun SCPI formları:** `SYNC:HEA?` ile `SYNCHRONIZATION:HEALTH?`
  aynı komuta çözülür (alias mekanizması).
- **Senaryo tabanlı yapılandırma:** Cihazın durumu YAML dosyalarından
  yüklenir (`normal`, `gnss-lost`, `holdover`, `warming-up`, `not-locked`,
  `hardware-error`).
- **Fiziksel olarak modellenmiş dinamik davranış:** Holdover'da zaman hatası
  gerçekten birikir, ölçümler deterministik gürültüyle gezinir, cihaz soğuk
  başlangıçtan kilide üstel bir ısınma rampasıyla ilerler. Ayrıntı için
  [Fiziksel modeller](#fiziksel-modeller).
- **Gerçek cihaz verisiyle doğrulanmış:** Değerler ve çıktı biçimleri, gerçek
  bir LN Rb GNSDO cihazından alınmış komut kayıtlarıyla karşılaştırılarak
  hizalandı ([docs/gercek-cihaz-ciktilari.md](docs/gercek-cihaz-ciktilari.md)).
- **Kalıcı loglama:** Alınan/gönderilen tüm veri hem ekrana hem
  `logs/simulator.log` dosyasına yazılır.
- **Çökme dayanıklılığı:** Bilinmeyen komutlar programı çökertmez; gerçek
  cihazın yaptığı gibi `Command Error` döner ve sunucu çalışmaya devam eder.
- **Otomatik testler:** Parser, config, komutlar ve gerçek PTY üzerinden
  uçtan uca seri iletişim için `pytest` testleri.

## Nasıl çalışır (mimari)

```
   İstemci (izleme yazılımı)                Simülatör
   ┌─────────────────────┐                 ┌──────────────────────────────┐
   │  "*IDN?\r\n" yazar   │  sanal seri     │  SerialServer                │
   │                     │──── kablo ─────▶│   • porttan satır okur        │
   │                     │  (socat / PTY)   │   • SCPIParser'a verir        │
   │  cevabı okur ◀──────│◀────────────────│  SCPIParser                   │
   └─────────────────────┘                 │   • komutu handler'a yönlendir│
                                           │  DeviceState                  │
                                           │   • cihazın "hafızası"        │
                                           └──────────────────────────────┘
```

Katmanlar birbirinden bağımsızdır:

| Katman | Dosya | Sorumluluğu |
|---|---|---|
| Seri sunucu | `serial_server.py` | Portu açar, byte akışını satırlara böler, cevabı geri yazar. Komutların ne olduğunu **bilmez.** |
| Parser | `scpi_parser.py` | Ham satırı normalize eder, doğru handler'a yönlendirir. Alias çözümlemesi burada. |
| Cihaz durumu | `device_state.py` | Cihazın tüm alanları (seri no, uydu sayısı, kilit durumu, sıcaklık...) tek bir yerde. Kilit mantığı (`is_locked`) burada. |
| Config yükleyici | `config_loader.py` | YAML senaryosunu okuyup `DeviceState`'e uygular. |
| Komutlar | `commands/*.py` | Her komut grubu (system, gps, ptime, sync, diag, measure, csac) ayrı dosyada, handler fonksiyonları olarak. |
| Giriş noktası | `main.py` | Parçaları birleştirir, argümanları okur, sunucuyu başlatır. |

## Fiziksel modeller

Simülatör "hazır cevap veren" bir yapı değildir: üç ayrı fiziksel model,
cihazın zamanla nasıl davrandığını belirler. Modeller
`src/gnsdo_simulator/models/` altında **saf fonksiyonlar** olarak durur —
seri porttan, komutlardan ve config'ten bağımsızdırlar, geçen süreyi
parametre olarak alırlar. Bu sayede "5 saat geçmiş olsaydı" sorusu testte
gerçek zamanda beklemeden sorulabilir.

Kullanılan sayıların tamamı ya cihaz kılavuzundan ya da gerçek cihaz
kayıtlarından gelir. Her kararın gerekçesi
[docs/tasarim-kararlari.md](docs/tasarim-kararlari.md) içindedir.

### 1. Holdover hata birikimi

GPS kaybolunca kontrol döngüsü açılır, düzeltme gelmez ve osilatörün küçük
frekans hatası zamanla **zaman** hatasına dönüşür:

```
x(t) = x₀ + y₀·t + (D/2)·t²
```

| Terim | Anlamı | Kaynak |
|---|---|---|
| `x₀` | kayıp anında donan faz hatası | anlık TINT okuması |
| `y₀` | kayıp anındaki frekans hatası | FEE, kılavuz §3.6.10 |
| `D` | Rubidyum yaşlanma hızı (8E-14/gün) | kılavuz §2.9 |

Sonuç: 1 saatte ~65 ns, ~3 saatte 210 ns'lik sağlık eşiği (`HEALTH 0x4`),
1 günde ~1.5 µs. Kuadratik terim saatler mertebesinde görünmez, günler
mertebesinde devreye girer.

### 2. Deterministik ölçüm gürültüsü

Sıcaklık, voltaj, akım ve TINT okumaları sabit değildir — ama gürültü
**rastgele sayı akışı değil, zamanın fonksiyonudur**:

```
değer(t) = taban + genlik · pürüzsüz_gürültü(t)
```

Bu iki şeyi birden sağlar: aynı anda iki kez sorulunca **aynı** cevap gelir
(fiziksel gereklilik — cihazın sıcaklığı sen sorduğun için değişmez) ve aynı
çalıştırma **aynı** değerleri üretir (hata ayıklanabilirlik).

Genlikler gerçek cihazda gözlenen aralıklardan alındı; zaman ölçekleri
fiziksel olarak ayrıldı (sıcaklık ısıl kütle nedeniyle yavaş gezinir,
voltaj hızlı titreşir).

Gürültü varsayılan olarak açıktır; `noise.enabled: false` ya da
`noise.scale: 0.0` ile kapatılabilir.

### 3. Isınma rampası ve servo durum makinesi

Cihaz fişe takıldığı anda hazır değildir. Sıcaklık **üstel** olarak yaklaşır
(ısı kaybı sıcaklık farkıyla orantılıdır — doğrusal bir rampa hedefi aşardı):

```
T(t) = T_son − (T_son − T_baş)·e^(−t/τ)
```

Bu sırada cihaz gerçek aşamalardan geçer (`SERV:STATE?`, kılavuz §3.10.3):

| Durum | Anlamı | Ne zaman |
|---|---|---|
| `0` | ısınma | ilk 2 dakika (§1.1) |
| `2` | kilitleniyor | atomik kilit var, GNSS eğitimi sürüyor |
| `6` | kilitli, GNSS aktif | ~20 dakika sonra (§2.5) |
| `5` | holdover ama hâlâ faz kilitli | GNSS kaybından sonraki ~100 sn |
| `1` | holdover | sonrası |

`SYNC:LOCKED?` yalnızca durum `6`'da `1` döner. Durum `0` ile `2`'yi ayırt
etmenin tek yolu `SERV:STATE?`'tir: cihaz henüz mü ısınıyor, yoksa ısındı da
GNSS'e mi kilitlenemiyor?

---

## Kurulum

Gereksinimler: **Python 3.10+**, Linux (sanal seri port için `socat`).

```bash
# socat (Debian/Ubuntu)
sudo apt install socat

# Bağımlılıklar
pip install -r requirements.txt
# veya projeyi paket olarak (gnsdo-sim komutuyla) kurmak için:
pip install -e .
```

## Hızlı başlangıç

Üç terminal (ya da üç sekme) kullanacağız.

**1) Sanal seri port çiftini oluştur** (bir uçta simülatör, diğer uçta
istemci olacak):

```bash
./scripts/create-virtual-serial.sh
```

Bu, `/tmp/gnsdo-simulator` ve `/tmp/gnsdo-client` adında iki bağlı port
yaratır ve açık kalır.

**2) Simülatörü başlat** (başka bir terminalde):

```bash
./scripts/run-simulator.sh --scenario normal
# veya paket olarak kurduysan:
gnsdo-sim --port /tmp/gnsdo-simulator --scenario normal
```

**3) Cihaza komut gönder** (üçüncü terminalde). Örneğin basit bir Python
tek satırıyla:

```bash
python3 - <<'PY'
import serial
c = serial.Serial("/tmp/gnsdo-client", 115200, timeout=1)
c.write(b"*IDN?\r\n")
print(c.readline().decode().strip())
PY
```

Çıktı:

```
Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 1.17
```

Elle denemek isterseniz `screen /tmp/gnsdo-client 115200` ile de
bağlanabilirsiniz.

## Senaryolar

Senaryo, cihazın hangi durumda başlayacağını belirler (`--scenario <isim>`):

| Senaryo | Ne simüle eder |
|---|---|
| `normal` | Her şey sağlıklı: GPS kilitli, uydular iyi, ölçümler normal. |
| `gnss-lost` | GPS sinyali yok (uydu sayısı 0), cihaz kilitlenemiyor. |
| `holdover` | Cihaz açılışta zaten holdover'da (GPS'i az önce kaybetmiş gibi). |
| `warming-up` | Cihaz yeni açıldı; 2 dakika sonra **kendiliğinden** kilitlenir. |
| `not-locked` | Donanım sağlam, GPS iyi, ama osilatör kilitlenememiş (kalıcı sorun). |
| `hardware-error` | Gerçek bir donanım arızası; `SYST:STAT?` "Fault" döner. |

Kendi senaryonuzu eklemek için `configs/` altına bir YAML dosyası koymanız
yeterli; yazmadığınız alanlar için makul varsayılanlar kullanılır.

## Desteklenen komutlar

Her komutun **ne anlama geldiğinin** sade açıklaması için
[docs/komut-aciklamalari.md](docs/komut-aciklamalari.md) belgesine bakın.
Çalışan bir simülatörde `HELP?` komutu güncel tam listeyi döndürür.

| Grup | Komutlar |
|---|---|
| Sistem/kimlik | `*IDN?`, `HELP?`, `SYST:STAT?` |
| Senkronizasyon | `SYNC?`, `SYNC:LOCKED?`, `SYNC:TINT?`, `SYNC:HEALTH?`, `SYNC:HOLD:DUR?`, `SYNC:HOLD:INIT`, `SYNC:HOLD:REC:INIT`, `SYNC:SOUR:MODE <değer>` |
| GPS | `GPS?`, `GPS:SAT:TRAC:COUN?`, `GPS:SAT:VIS:COUN?` |
| Zaman | `PTIME?`, `PTIME:DATE?`, `PTIME:TIME?`, `PTIME:TIME:STRING?`, `PTIME:OUTPUT?`/`<ON\|OFF>`, `PTIME:LEAP:ACC?` |
| Tanı | `DIAG?`, `DIAG:LIFE:COUN?` |
| Ölçüm | `MEAS?`, `MEAS:TEMP?`, `MEAS:VOLT?`, `MEAS:CURR?`, `MEAS:POW?` |
| CSAC | `CSAC?` (`MAC?`), `CSAC:STATUS?`, `CSAC:TEMP?`, `CSAC:SN?`, `CSAC:LIFE?` |
| Servo | `SERV?`, `SERV:STATE?` |

Komutlar büyük/küçük harf duyarsızdır ve çoğu için uzun form takma adı
(`MEASURE:TEMPERATURE?` gibi) tanımlıdır.

## Örnek çıktılar

`normal` senaryosunda (çalışan simülatörden alınmış gerçek çıktı):

```
*IDN?
  → Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 1.17

SYNC?
  → 1PPS SOURCE MODE  : GPS
    1PPS SOURCE STATE : GPS
    1PPS on RESET : OFF
    1PPS DOMAIN : CSAC
    1PPS LOCK STATUS  : 1
    HOLDOVER STATE: NONE
    LAST HOLDOVER DURATION : 0,0
    FREQ ERROR ESTIMATE : 1.64E-11
    TIME INTERVAL DIFFERENCE : -1.913E-09
    TIME INTERVAL THRESHOLD : 220
    PHASE NOISE FILTER : ON
    HEALTH STATUS : 0x8

MEAS?
  → PCB Temperature: 53.0799
    CSAC Temperature: 54.38
    TCXO Voltage: 1.662
    Power Supply Voltage: 11.70

DIAG?
  → EFControl Relative: -0.530000%
    EFControl Absolute: -106.000000
    Lifetime : +871

SERV:STATE?
  → 6
```

> **Değerler her sorguda birebir aynı çıkmaz** — sıcaklık, voltaj, TINT ve
> FEE zamanla gezinir ([Fiziksel modeller](#fiziksel-modeller)). Aynı anda
> iki kez sorulunca ise aynı cevap gelir; gürültü rastgele değil, zamanın
> fonksiyonudur.

> `HEALTH STATUS`, simülatör açıldıktan sonraki ilk 200 saniye boyunca `0x8`
> ("cihaz yeni açıldı") bitini taşır (kılavuz §3.6.18); bu süre sonunda `0x0`
> (tamamen sağlıklı) olur.

Bilinmeyen bir komut gönderilirse gerçek cihazın yaptığı gibi:

```
FOO:BAR?
  → Command Error
```

Holdover'da zaman hatasının birikmesi (`SYNC:HOLD:INIT` sonrası):

```
holdover süresi    SYNC:TINT?     SYNC:HEALTH?
        0 sn        1.200E-08         0x0
        1 dk        1.279E-08         0x10     ← holdover > 60 sn
        1 saat      5.917E-08         0x10
        5 saat      2.480E-07         0x14     ← faz > 210 ns de eklendi
        1 gün       1.147E-06         0x14
```

Soğuk başlangıç (`warming-up` senaryosu):

```
dakika    PCB      CSAC    SERV:STATE?   SYNC:LOCKED?
   0     25.00    26.32         0             0        ← ısınma
   2     30.04    31.36         2             0        ← atomik kilit
  10     42.57    43.89         2             0
  20     49.04    50.36         6             1        ← GNSS kilidi
  60     52.73    54.05         6             1
```

## Testler

```bash
pytest
# veya paket olarak kurmadıysanız:
PYTHONPATH=src pytest
```

Test kapsamı:

- **`test_parser.py`** — komut normalize etme, alias çözümleme, bilinmeyen
  komutta çökmeme.
- **`test_config.py`** — her senaryonun doğru `DeviceState` üretmesi,
  `warming-up`'ın süre sonunda kilitlenmesi.
- **`test_commands.py`** — her komut grubunun doğru çıktı üretmesi, kilit
  durumunun state'e göre değişmesi.
- **`test_serial.py`** — gerçek bir PTY (pseudo-terminal) üzerinden uçtan
  uca seri iletişim; bilinmeyen komut sonrası sunucunun ayakta kalması.

## Proje yapısı

```
gnsdo-scpi-simulator/
├── README.md
├── LICENSE
├── pyproject.toml            # paketleme + pytest yapılandırması
├── requirements.txt
├── configs/                  # senaryo YAML dosyaları
│   ├── normal.yaml
│   ├── gnss-lost.yaml
│   ├── holdover.yaml
│   ├── warming-up.yaml
│   ├── not-locked.yaml
│   └── hardware-error.yaml
├── docs/
│   ├── komut-aciklamalari.md    # her komutun sade açıklaması
│   ├── tasarim-kararlari.md     # modelleme kararları ve gerekçeleri
│   ├── gercek-cihaz-ciktilari.md# gerçek cihaz komut kayıtları
│   └── kaynaklar/               # kayıtların orijinal dosyası
├── scripts/
│   ├── create-virtual-serial.sh
│   └── run-simulator.sh
├── src/gnsdo_simulator/
│   ├── main.py
│   ├── serial_server.py
│   ├── scpi_parser.py
│   ├── device_state.py
│   ├── config_loader.py
│   ├── models/               # cihaz FİZİĞİ (saf fonksiyonlar, I/O yok)
│   │   ├── holdover.py       #   holdover hata birikimi
│   │   ├── noise.py          #   deterministik ölçüm gürültüsü
│   │   └── warmup.py         #   ısınma rampası + servo durum makinesi
│   └── commands/
│       ├── system.py  gps.py  ptime.py  servo.py
│       ├── sync.py  diagnostic.py  measure.py  csac.py
└── tests/
    ├── test_parser.py  test_config.py
    ├── test_commands.py  test_serial.py
    ├── test_holdover_model.py  test_noise_model.py
    └── test_warmup_model.py
```

## Bilinçli basitleştirmeler

Simülatörün modellediği şeyler [Fiziksel modeller](#fiziksel-modeller)
bölümünde. Burada **kasıtlı olarak modellenmeyenler** ve nedenleri var:

- **Uydu tablosundaki El/Az/SS değerleri** gerçek yörünge hesabıyla değil,
  tekrarlanabilir basit bir formülle üretilir. Gerçek yörünge mekaniği bu
  projenin kapsamı dışında.
- **`SYNC:HEALTH?`'in iki biti üretilmez:** `0x20` ("Frequency Estimate out
  of bounds") için kılavuz bir eşik değeri vermiyor — uydurmak yerine
  bırakıldı. `0x200` (faz-reset sonrası ilk 3 dakika) ise jam-sync
  davranışını gerektiriyor, o da henüz modellenmedi.
- **Gerçek cihazın bir tutarsızlığı taklit edilmez:** Kayıtlarda
  `GPS:SAT:TRAC:COUN?` (20), `GPS:SAT:VIS:COUN?`ten (19) büyük çıkıyor.
  Simülatörde takip edilen uydu sayısı görünürü aşamaz — tutarlı olmak,
  bir ölçüm artefaktını yeniden üretmekten daha değerli. (Gerekçe:
  `docs/tasarim-kararlari.md`, K-10.)
- **Zaman hızlandırma yoktur.** Simülatör gerçek zamanda çalışır; holdover
  eşiğine ulaşmak gerçekten saatler alır. Hızlandırma ihtiyacı bir *test*
  ihtiyacıdır ve test katmanında çözülür (K-2).

## Yol haritası

Simülatörü "hazır cevap veren" bir yapıdan **zamanla değişen, fiziksel
olarak anlamlı** bir modele taşıma çalışması:

- [x] **Holdover hata birikimi** — GPS kaybından sonra zaman hatasının
      süreyle birlikte artması.
- [x] **Deterministik ölçüm gürültüsü** — zamanın fonksiyonu olarak, aynı
      çalıştırmada tekrarlanabilir.
- [x] **Isınma rampası ve servo durum makinesi** — soğuk başlangıçtan kilide
      kademeli geçiş, `SERV:STATE?` ile gözlemlenebilir.
- [x] **Gerçek cihaz verisiyle hizalama** — çıktı biçimleri ve değerler,
      gerçek cihaz kayıtlarıyla karşılaştırılarak düzeltildi.
- [x] Sürekli entegrasyon (GitHub Actions ile otomatik test).
- [ ] SCPI hata kuyruğu (`SYST:ERR?`) ve standart hata davranışı.
- [ ] Jam-sync / faz-reset davranışı (`SYNC:IMME`, `HEALTH 0x200`).

## Belgeler

| Belge | İçerik |
|---|---|
| [docs/komut-aciklamalari.md](docs/komut-aciklamalari.md) | Her SCPI komutunun sade açıklaması |
| [docs/tasarim-kararlari.md](docs/tasarim-kararlari.md) | Modelleme kararları, gerekçeleri ve düzeltilen hatalar |
| [docs/gercek-cihaz-ciktilari.md](docs/gercek-cihaz-ciktilari.md) | Gerçek cihazdan alınmış komut girdi/çıktı kayıtları |

`tasarim-kararlari.md` özellikle önemli: her modelin **neden öyle
kurulduğunu**, hangi kılavuz maddesine ya da hangi gerçek ölçüme
dayandığını ve yol boyunca düzeltilen hataları kaydeder.

## Lisans

[MIT](LICENSE) — © 2026 Ömer Faruk Karagöz
