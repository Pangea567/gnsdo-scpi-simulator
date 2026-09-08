"""
models/

Cihazin FIZIKSEL davranisini tanimlayan modeller.

Neden ayri bir paket?
  Buradaki fonksiyonlar "cihaz fizigi"ni anlatir; SCPI komutlarindan,
  seri porttan, config dosyasindan tamamen BAGIMSIZDIR. Bu ayrim
  sayesinde:
    - Modeli test etmek icin seri port acmaya, komut gondermeye ya da
      gercek zamanda beklemeye gerek kalmaz.
    - Formulu degistirdigimizde komut katmanina hic dokunmayiz.
    - Bildiriyi yazarken modeli tek basina, kendi basina anlatabiliriz.
"""
