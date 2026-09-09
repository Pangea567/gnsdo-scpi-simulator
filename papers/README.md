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
├── eleco/            # (sonra) ELECO şablonuna uyarlanmış sürüm
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
Yerelde LaTeX yok; **Overleaf** önerilir (IEEEtran hazır gelir).
Yerel derleme istenirse: `tectonic main.tex` (tek binary) veya texlive.

## Dil
Ana taslak İngilizce (ilerleyiş kolaylığı). ELECO sürümünde dil/şablon
konferans şartına göre uyarlanır. Grafik etiketlerinin dili
`experiments/` içinden yeniden üretilerek değiştirilebilir.
