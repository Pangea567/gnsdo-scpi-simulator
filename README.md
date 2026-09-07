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
- [Kurulum](#kurulum)
- [Hızlı başlangıç](#hızlı-başlangıç)
- [Senaryolar](#senaryolar)
- [Desteklenen komutlar](#desteklenen-komutlar)
- [Örnek çıktılar](#örnek-çıktılar)
- [Testler](#testler)
- [Proje yapısı](#proje-yapısı)
- [Bilinçli basitleştirmeler](#bilinçli-basitleştirmeler)
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
- **Zamanla değişen durum:** Lifetime sayacı gerçek çalışma süresiyle artar;
  `warming-up` senaryosu 2 dakika sonra kendiliğinden kilitlenir; holdover
  süresi gerçek zamanlı sayılır.
- **Kalıcı loglama:** Alınan/gönderilen tüm veri hem ekrana hem
  `logs/simulator.log` dosyasına yazılır.
- **Çökme dayanıklılığı:** Bilinmeyen komutlar programı çökertmez, sessizce
  loglanır ve sunucu çalışmaya devam eder.
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

Komutlar büyük/küçük harf duyarsızdır ve çoğu için uzun form takma adı
(`MEASURE:TEMPERATURE?` gibi) tanımlıdır.

## Örnek çıktılar

`normal` senaryosunda:

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
    FREQ ERROR ESTIMATE : 1.31E-11
    TIME INTERVAL DIFFERENCE : 1.200E-08
    TIME INTERVAL THRESHOLD : 220
    PHASE NOISE FILTER : ON
    HEALTH STATUS : 0x8

MEAS?
  → PCB Temperature: 42.5
    CSAC Temperature: 54.0
    TCXO Voltage: 1.66
    Power Supply Voltage: 11.7

DIAG?
  → EFControl Relative: -0.410000%
    EFControl Absolute: -82.000000
    Lifetime : +871
```

> Not: `HEALTH STATUS`, simülatör açıldıktan sonraki ilk 200 saniye
> boyunca `0x8` ("cihaz yeni açıldı") bitini taşır; bu süre sonunda `0x0`
> (tamamen sağlıklı) olur. Bu, gerçek cihazın "ısınma" davranışını yansıtan
> bilinçli bir tasarımdır.

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
│   └── komut-aciklamalari.md # her komutun sade açıklaması
├── scripts/
│   ├── create-virtual-serial.sh
│   └── run-simulator.sh
├── src/gnsdo_simulator/
│   ├── main.py
│   ├── serial_server.py
│   ├── scpi_parser.py
│   ├── device_state.py
│   ├── config_loader.py
│   └── commands/
│       ├── system.py  gps.py  ptime.py
│       ├── sync.py  diagnostic.py  measure.py  csac.py
└── tests/
    ├── test_parser.py  test_config.py
    ├── test_commands.py  test_serial.py
```

## Bilinçli basitleştirmeler

Bu bir **davranış** simülatörüdür, fiziksel bir model değil. Gerçekçi
**görünen** ama sabit tutulan değerler vardır (bilinçli tercih):

- `SYNC:TINT?`, frekans hata tahmini, sıcaklıklar ve voltajlar sabit
  değerlerdir (gürültü/sürüklenme modeli yoktur).
- Holdover sırasındaki zaman hatası, holdover süresine bağlı olarak
  **büyümez** (sabit bir değer döner).
- Uydu tablosundaki El/Az/SS değerleri gerçek yörünge hesabıyla değil,
  tekrarlanabilir basit bir formülle üretilir.
- "En son holdover süresi" ayrıca saklanmaz.

Bunların dinamik hâle getirilmesi yol haritasındadır (aşağıya bakın).

## Yol haritası

Bir sonraki geliştirme fazı, simülatörü "hazır cevap veren" bir yapıdan
**zamanla değişen, fiziksel olarak anlamlı** bir modele taşımayı hedefler:

- [ ] **Holdover hata birikimi:** GPS kaybından sonra zaman hatasının
      süreyle birlikte artması (izleme yazılımının eşik/alarm testleri için
      en kritik davranış).
- [ ] Ölçümlere gerçekçi (tohumlanabilir/deterministik) gürültü eklenmesi.
- [ ] Isınma sırasında sıcaklık ve TINT'in kademeli yakınsaması (rampa).
- [ ] SCPI hata kuyruğu (`SYST:ERR?`) ve standart hata davranışı.
- [x] Sürekli entegrasyon (GitHub Actions ile otomatik test).

## Lisans

[MIT](LICENSE) — © 2026 Ömer Faruk Karagöz
