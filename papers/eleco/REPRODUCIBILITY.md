# ELECO hakem revizyonunun yeniden üretilmesi

Sürüm etiketi: `eleco-2026-review-v1`.
Dal: `paper/eleco-2026-review-revision`.
Bu sürüm [GitHub'da yayımlanmıştır](https://github.com/Pangea567/gnsdo-scpi-simulator/releases/tag/eleco-2026-review-v1).
Sonraki şablon düzenlemesi model ve deney verilerini değiştirmez. Etiketteki
PDF ilk hakem revizyonudur; güncel `main.tex` dosyasının biçim değişiklikleri
[biçim notlarında](FORMAT.md) açıklanmıştır.

Bu revizyonun giriş dosyası `main.tex` dosyasıdır. `draft-en/` altındaki
İngilizce taslak eskidir; revize sonuçların kaynağı olarak kullanılmamalıdır.
Önceki kodda bulunan ikinci dereceden yaşlanma terimi kaldırılmıştır.
`8e-14` Allan sapması değeri yaşlanma katsayısı değildir.

## Sürüm ve sonuç bağlantısı

`data/manifest.json`, grafiklerin üretildiği kaynak commit kimliğini,
model/config dosyalarının SHA-256 özetlerini ve kullanılan parametreleri
içerir. Etiket bu kaynak sürümünü ve üretilmiş kanıt dosyalarını birlikte
sabitler. Commit kimliği hareketli `develop` dalının yerine kullanılmalıdır.
İnceleme başlangıcındaki yerel `origin/develop` kaydı
`72fbb9aa7aae23daef52eff85384b2fbc58a1db6` idi; bu bilgi uzak dalın güncel
durumuna ilişkin bir iddia değildir.

Şekil 1 `data/holdover.csv`, Şekil 2 `data/warmup.csv` dosyasını okur.
Her ikisi `generate_evidence.py` ile **doğrudan model fonksiyonlarından**
üretilir; fiziksel cihaz zaman serisi değildir. Eski `experiments/data/`
ve `experiments/figures/` dosyaları bu iki şeklin kaynağı değildir.

| Çıktı | Parametreler ve kapsam |
|---|---|
| Holdover | `x0=0 s`, `y_h=1.8e-11`, 0–24 saat, 300 s adım; şekil ilk 12 saati gösterir. Ölçüm değişimi kapalı saf model. |
| Isınma | `T0=25 °C`, `T∞=52.8 °C`, `tau=90 s`, 0–1500 s, 10 s adım; saf termal model. 20 dk çizgisi ölçülmüş kilit anı değildir. |
| Eşik | `210e-9 / 1.8e-11 / 3600 = 3.24074074 saat`; denklemden türetilmiş, donanımda ölçülmemiştir. |
| Sorgu kapsamı | Kayıtlı HELP listesindeki 66 cihaz sorgusundan 50 desteklenen, 16 desteklenmeyen. HELP isteği, ayar komutları ve bütün alternatif yazımlar sayım dışıdır. |

`sync.holdover_frequency_error` işaretli etkin eğimi açıkça belirler.
Verilmezse girişteki FEE eğim olarak eşlenir; bu fiziksel olarak ölçülmüş
bir ilişki değil, model varsayımıdır. Eski `sync.drift_per_day` ayarı hata
verir; sessizce yok sayılmaz.

## Komutlar

Depo kökünden, Python 3.10+ ile:

```bash
git checkout eleco-2026-review-v1
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev,experiments]'
.venv/bin/python -m pytest -q
.venv/bin/python papers/eleco/generate_evidence.py
.venv/bin/python papers/eleco/run_client_test.py
./papers/build.sh eleco
```

İstemci koşusu `socat`, PDF derlemesi `tectonic` gerektirir.
Bu çalışma ortamında ikisi de zaten kuruluydu. Python bağımlılıkları
`/tmp/gnsdo-paper-venv` altında kuruldu. Koşunun paket sürümleri
`data/python-packages.txt` dosyasındadır. Tectonic eksik TeX paketlerini
gerektiğinde indirir. Üretilmiş CSV'ler sürüme dahil olduğundan yalnızca
PDF derlemek için Python gerekmemektedir.

Overleaf'e yüklerken `main.tex` ile birlikte `data/holdover.csv` ve
`data/warmup.csv` dosyalarını da koruyun. Güncel şablon düzenlemesi için
**XeLaTeX** kullanın ve Times New Roman yazı tipini sağlayın; yerel font
dosyalarıyla derleme ayrıntıları [biçim notlarında](FORMAT.md) verilmiştir.
Yukarıdaki `git checkout` komutu, sonraki biçim düzenlemesini değil,
yayımlanan ilk sürümü yeniden üretir.

## Yeni istemci testinin kapsamı

`monitor_client.py`, yalnızca pySerial kullanan küçük bir izleme istemcisidir;
simülatörün Python modüllerini içe aktarmaz. `run_client_test.py`, simülatörü
ve istemciyi ayrı süreçlerde çalıştırıp iki PTY'yi socat ile bağlar.
Test normal kilit, zorlanmış holdover, gerçek zamanda 62 s bekleme, `0x10`
süre alarmı ve recovery sonrası alarmın temizlenmesini denetler.
İlk 200 s için `0x8` biti de bulunabilir; test ilgili bitleri ayrı sınar.
İstemci, ayar komutlarından gelen boş satırları sorgu yanıtı saymaz.

`data/client_test.jsonl` dört anlık durum kaydını, `data/client_test_server.log`
seri istek/yanıt izini içerir. Canlı koşuda sorgu zamanları değişir; TINT
değerlerinin farklı koşular arasında bayt düzeyinde aynı olması beklenmez.
Bu yeni örnek, önceden kullanılan bir saha istemcisi veya gerçek donanımla
yapılmış kabul testi olarak sunulmamıştır. `--exercise-holdover` seçeneği
bağlı aygıta durum değiştiren komutlar gönderir; sağlanan koşucu yalnızca
kendi oluşturduğu simülatör PTY'lerine bağlanır.

## Donanım kanıtının sınırı

Kaynak: `docs/gercek-cihaz-ciktilari.md` içindeki sınırlı, ağırlıkla kilitli
durum kayıtları. Bazı tarih/saat yanıtları olsa da holdover/soğuk açılış için
her örneği zaman eksenine bağlayan seri yoktur. Bu nedenle holdover eğimi,
ısınma zaman sabiti, kilitlenme süresi ve sağlık geçiş gecikmeleri donanımla
nicel olarak doğrulanmış sayılmaz. Birim testleri matematiksel uygulamayı,
seri istemci testi ise yazılım bileşenlerinin birlikte çalışmasını sınar.

Beş TINT kaydı `[-11.79, 11.33] ns` aralığındadır; bu bir ölçüm doğruluğu
veya belirsizlik aralığı değildir. Dört sıcaklık çiftinin 1.32 °C ofsete göre
en büyük farkı 0.0681 °C'dir. EFC ilişkisi sayısal birimlerle
`a[ppt] = 200 * r[%]` biçimindedir; örneğin `-82 ppt` ve `-0.410000%`.

Eksik 16 sorgunun tekil listesi `data/query_coverage.csv` içindedir:
13 MAC alt sorgusu ve döngüye özel 3 EFC sorgusu. MAC alanlarının çoğuna
CSAC sorgularıyla erişilebilmesi, MAC komut adlarının desteklendiği anlamına
gelmez. Sorgunun kayıtlı olması da sayısal donanım doğruluğunun kanıtı değildir.
