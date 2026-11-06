# ELECO 2026 biçim notları

Biçim denetiminin kaynağı, kullanıcının `papers/ELECO2026-bildiri_taslagi/`
klasörüne kopyaladığı LaTeX ve PDF şablonudur. Kaynak kod ile açıklamalar
çeliştiğinde yazılı kurallar esas alınmıştır: paragraf girintisi 0,4 mm,
başlıkların üst ve alt boşluğu 9 punto, açıklamalar iki yana yaslıdır.
Şekil etiketlerinde şablon örneğindeki iki nokta, çizelgelerde nokta kullanılır.

Uygulanan düzen:

- A4, beş sayfa; 82,5 mm genişliğinde iki sütun ve 5 mm sütun aralığı.
- Sağ/sol 20 mm, alt 37 mm, üst 25 mm; ilk sayfanın başlığı için ek 5 mm.
- Times New Roman; gövde 9, ana başlıklar 14, yazarlar 11, kurumlar ve
  bölüm başlıkları 10 punto. Matematik sembolleri NewTX/UpGreek ile dizilir.
- Türkçe özet 150, İngilizce özet 149 kelime; her ikisi 9 punto ve italik.
  Sayım, özet metnindeki boşlukla ayrılan sözcüklere göre yapılmıştır.
- Paragraf aralığı sıfır; denklem üst/alt boşluğu 9 punto, indisler 7 punto,
  Yunan harfleri dik. Şekil/çizelge açıklık aralığı 6 punto.
- Son sayfa `multicols` ile dengelenir; bu sayfadaki şekil sütun yüksekliğine
  katılması için metin içinde yerleştirilmiştir. Sayfa numarası bulunmaz.

## Yazı tipi ve derleme

Bu ortamda Times New Roman kullanıcı font dizinine kurulmuştur.
Tectonic'in Snap sürümü bu dizini göremediği için aşağıdaki dosyalar ayrıca
`papers/eleco/fonts/` altında bulunur:

```
Times.TTF
Timesbd.TTF
Timesi.TTF
Timesbi.TTF
```

Font dosyaları Git'e dahil edilmez. Başka bir ortamda lisanslı Times New Roman
kurulumunuzu kullanın veya sisteminizde `ttf-mscorefonts-installer` paketini
kurun. Fontlar sistemde görünmüyorsa yukarıdaki adlarla `fonts/` klasörüne
kopyalayın. Ana dosya bu klasör varsa onu, yoksa sistem fontunu kullanır.
Tectonic bu Microsoft fontlarını kendiliğinden indirmez.

`papers/` klasöründen:

```bash
./build.sh eleco
```

Çıktı `eleco/main.pdf` dosyasıdır. Overleaf'te **XeLaTeX** seçin; `main.tex`,
`data/` ve gerekirse `fonts/` klasörünü birlikte yükleyin.

Bu biçim düzenlemesi model kodunu veya deney verilerini değiştirmez.
`eleco-2026-review-v1` etiketi ve yayımlanmış sürüm korunmuştur; güncel
biçimlendirilmiş PDF bu eski sürümün eki olarak değiştirilmemiştir.
