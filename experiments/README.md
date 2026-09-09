# experiments/ — Bildiri sekillerini ureten script'ler

Her sekil, TEK BASINA calisan ve sekli YENIDEN URETEN bir script'ten
gelir. Grafikleri elle cizmiyoruz; boylece bildiri tamamen yeniden
uretilebilir.

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
