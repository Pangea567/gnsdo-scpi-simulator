# papers/

Bildiri sürümleri. Çekirdek fikir: **çerçeveden bağımsız bir taslağı**
(`draft-en/`) tek bir yerde tutmak, her konferans için ondan türetilmiş
ayrı bir sürüm oluşturmak.

```
papers/
├── draft-en/         # çerçeveden bağımsız, İngilizce ANA taslak
│   ├── main.tex
│   ├── references.bib
│   └── figures/      # experiments/figures'tan kopyalanan PDF'ler
├── eleco/            # ELECO 2026 sürümü (Türkçe); giriş dosyası main.tex
│   ├── main.tex
│   ├── references.bib
│   ├── data/         # şekillerin okuduğu CSV'ler + manifest + kapsam
│   ├── generate_evidence.py   # data/ dosyalarını modelden üretir
│   ├── monitor_client.py      # bağımsız pySerial izleme istemcisi
│   ├── run_client_test.py     # uçtan uca istemci testi (socat gerekir)
│   ├── REVISION_NOTES.md      # hakem maddesi -> yapılan değişiklik
│   ├── REPRODUCIBILITY.md     # sürüm kimliği, komutlar, kanıt sınırları
│   └── FORMAT.md              # şablon uyumu, font ve derleme notları
└── sync_figures.sh   # experiments/figures/*.pdf -> her bildirinin figures/
```

Her klasörde tek bir giriş dosyası vardır: `main.tex`. Aşılmış taslaklar
klasörde tutulmaz; git geçmişinden erişilebilir.

## Grafikler
`draft-en/` için grafikler `experiments/` altında üretilir; `sync_figures.sh`
üretilen PDF'leri bildiri klasörlerine kopyalar.

**ELECO sürümü farklı çalışır:** şekiller `main.tex` içinde PGFPlots ile
çizilir ve verilerini `eleco/data/*.csv` dosyalarından okur. O CSV'leri
`eleco/generate_evidence.py` doğrudan model fonksiyonlarından üretir, yani
şekilde görünen eğri ile koddaki model aynı kaynaktan gelir.

```bash
./papers/sync_figures.sh
```

## Derleme
Yerel derleme için `tectonic` komutunun PATH üzerinde bulunması gerekir.
Bu ortamda Tectonic 0.15.0 kuruludur; ayrıca TeX Live kurulumu gerekmez.
Gerekli LaTeX paketleri ve TeX yazı tipleri Tectonic tarafından gerektiğinde
indirilip önbelleğe alınır; ilk derlemede internet bağlantısı gerekebilir.
ELECO sürümü ayrıca gerçek Times New Roman dosyalarını gerektirir;
kurulum ve şablon ayrıntıları [biçim notlarında](eleco/FORMAT.md) açıklanmıştır.

Bu klasörden:

```bash
./build.sh eleco       # eleco/main.pdf
./build.sh draft-en    # draft-en/main.pdf (varsayılan)
```

Depo kökünden aynı komutlar `./papers/build.sh eleco` ve
`./papers/build.sh draft-en` şeklinde çalıştırılır. Betik, grafik klasörlerini
oluşturup `experiments/figures/*.pdf` dosyalarını kopyalar ve ardından
`main.tex` dosyasını kaynakçasıyla birlikte derler. ELECO'nun `main.tex`
dosyasındaki grafikler doğrudan TikZ/PGFPlots ile çizilir.

Overleaf için ilgili bildiri klasörünü (`main.tex`, `references.bib`,
varsa `figures/` ve ELECO için `data/` CSV dosyaları) yükleyebilirsiniz.
Derleme betiği giriş dosyası olarak `main.tex` kullanır. ELECO için Overleaf
derleyicisini **XeLaTeX** seçin; Times New Roman bulunmuyorsa biçim notlarında
belirtilen `fonts/` klasörünü de yükleyin.

ELECO hakem revizyonunun kod sürümü, testleri ve grafik verileri için
[yeniden üretim kılavuzuna](eleco/REPRODUCIBILITY.md) bakın. `draft-en/`
altındaki İngilizce taslak bu revizyonun bilimsel güncellemelerini içermez.

## Dil
Ana taslak İngilizce (ilerleyiş kolaylığı). ELECO sürümünde dil/şablon
konferans şartına göre uyarlanır. Grafik etiketlerinin dili
`experiments/` içinden yeniden üretilerek değiştirilebilir.
