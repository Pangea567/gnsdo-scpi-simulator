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
├── eleco/            # Türkçe ELECO sürümü; giriş dosyası main.tex
└── sync_figures.sh   # experiments/figures/*.pdf -> her bildirinin figures/
```

## Grafikler
Grafikler `experiments/` altında üretilir (tek kaynak). `sync_figures.sh`
üretilen PDF'leri bildiri klasörlerine kopyalar; böylece Overleaf'e
yüklenebilir hale gelirler.

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
varsa `figures/` ve ELECO için `data/` CSV dosyaları) yükleyebilirsiniz. Diğer `.tex` dosyaları önceki taslaklardır;
derleme betiği giriş dosyası olarak `main.tex` kullanır. ELECO için Overleaf
derleyicisini **XeLaTeX** seçin; Times New Roman bulunmuyorsa biçim notlarında
belirtilen `fonts/` klasörünü de yükleyin.

ELECO hakem revizyonunun kod sürümü, testleri ve grafik verileri için
[yeniden üretim kılavuzuna](eleco/REPRODUCIBILITY.md) bakın. İngilizce taslak
ve diğer ELECO `.tex` dosyaları bu revizyonun bilimsel güncellemelerini içermez.

## Dil
Ana taslak İngilizce (ilerleyiş kolaylığı). ELECO sürümünde dil/şablon
konferans şartına göre uyarlanır. Grafik etiketlerinin dili
`experiments/` içinden yeniden üretilerek değiştirilebilir.
