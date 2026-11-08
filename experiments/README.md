# experiments/ — Ölçüm script'leri

> **Not.** Holdover modeli doğrusaldır: `x(t) = x₀ + y_h·t`. Bildirideki iki
> şeklin kaynağı bu klasör **değil**, `papers/eleco/generate_evidence.py` ve
> onun ürettiği `papers/eleco/data/*.csv` dosyalarıdır. Kapsam ve yeniden
> üretim: [`papers/eleco/REPRODUCIBILITY.md`](../papers/eleco/REPRODUCIBILITY.md).

Buradaki her script TEK BASINA calisir, modeli dogrudan cagirir ve
olctugu seyi yeniden uretir. Grafikleri elle cizmiyoruz; fiziksel
degismezler de ayni script icinde dogrulanir.

## Kurulum
```bash
pip install -e ".[experiments]"   # matplotlib + numpy
```

## Calistirma
```bash
cd experiments
python3 fig01_holdover_accumulation.py   # her script figures/ altina PDF+PNG yazar
```

## Dosyalar
- `style.py` — ortak matplotlib stili (IEEE'ye yakin, vektor PDF cikti)
- `_reference.py` — gercek cihaz referans degerleri (tek kaynak;
  docs/gercek-cihaz-ciktilari.md'den)
- `figXX_*.py` — her biri bir sekil
- `figures/` — uretilen PDF (bildiri) + PNG (onizleme)
- `data/` — uzun sureli kayitlar (varsa)

## Onemli durustluk notu
Gercek cihaz olcumleri RASTGELE ANLARDA alindi, zaman damgasi YOK.
Bu yuzden onlari isinma egrisinde belirli bir zamana koymuyoruz;
bunun yerine gozlenen ARALIGI ve DEGISKENLER ARASI ILISKILERI
(PCB<->CSAC, EFC abs<->rel) dogrulama icin kullaniyoruz.
