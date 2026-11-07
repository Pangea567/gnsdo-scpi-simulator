# Cihaz Referansı

Modelde kullanılan ve kılavuzdan alınan değerler. Kaynak: Jackson Labs
Technologies, *Low Noise Rubidium GNSDO User Manual*, Doküman 80200526,
Sürüm 1.3, Ağustos 2015. Bölüm numaraları o belgeye aittir.

Bu dosya **referans**; bir değerin modelde nasıl ve neden kullanıldığı
ilgili modülün başındaki açıklamada yazılıdır
(`src/gnsdo_simulator/models/`).

> **Uyarı.** Bir değerin kılavuzda bulunması, modelin o davranışı donanımla
> doğrulanmış biçimde ürettiği anlamına gelmez. Hangi davranışın ölçümle
> desteklendiği `papers/eleco/REPRODUCIBILITY.md` içinde ayrıca yazılıdır.

---

## Zaman ve faz

| Değer | Kaynak |
|---|---|
| TINT çözünürlüğü 1E-10 s (0,1 ns) | §3.6.6 |
| Zaman-aralık sayacı çözünürlüğü 20 ps | §1.1 |
| Kilitliyken Rb → 1PPS faz doğruluğu < 0,2 ns **ortalama** | §1.1 |
| Kilitliyken Filtre OCXO → Rb < 0,3 ns | §1.1 |
| Kilitliyken ADEV 8E-14/gün'e yaklaşıyor | §2.9 |
| FEE ≈ 1000 s Allan varyansı; 1E-12 gürültü tabanının altı | §3.6.10 |
| TINT eşiği [50, 2000] ns, varsayılan 220 ns → jam-sync | §3.6.19 |

İlk iki faz değerindeki niteleyicilere dikkat: "**ortalama**" doğruluk ile
anlık okuma aynı şey değil. `8E-14` de bir **Allan sapması**
rakamıdır, yaşlanma katsayısı değildir ve modelde kullanılmaz.

## ADEV tablosu

Premium seçenek, GPS kilitli, Şekil 2.19:

| τ | σ(τ) |
|---|---|
| 1 s | 1,76E-12 |
| 10 s | 4,15E-12 |
| 100 s | 6,11E-12 |
| 1000 s | 4,74E-12 |
| 4000 s | 1,47E-12 |

Simülatör Allan sapmasını modellemez; bu tablo yalnızca mertebe referansıdır.

## `SYNC:HEALTH?` bit haritası (§3.6.18)

| Bit | Koşul |
|---|---|
| `0x4` | referansa faz farkı > 210 ns |
| `0x8` | çalışma süresi < 200 s |
| `0x10` | holdover > 60 s |
| `0x20` | FEE sınır dışı |
| `0x100` | kısa dönem drift (ADEV@100s) > 100 ns |
| `0x200` | faz-reset sonrası ilk 3 dakika |
| `0x400` | Rubidyum osilatör alarmı |
| `0x800` | güçlü jamming (≥50, aralık 0–255) ve GNSS fix yok |
| `0x1000` | filtre osilatör döngüsü kilitli değil |

`0x0` = tamamen sağlıklı, ısınmış, kilitli cihaz. Bayraklar bit düzeyinde
VEYA ile birleşir; örneğin uzun holdover sırasında faz eşiğinin aşılması
`0x14` üretir.

Modelde uygulanan: `0x4`, `0x8`, `0x10`, `0x1000`.
Uygulanmayan: `0x20`, `0x100`, `0x200`, `0x400`, `0x800`.

## `SERVo:STATe?` durum makinesi (§3.10.3)

| Değer | Anlam |
|---|---|
| 0 | Rubidyum / filtre osilatör ısınması |
| 1 | Holdover |
| 2 | Kilitleniyor (Rubidyum / filtre eğitimi) |
| 4 | tanımsız |
| 5 | Holdover ama hâlâ faz kilitli — GNSS kaybından sonra ~100 s |
| 6 | Kilitli, GNSS aktif |

Durum 5 bir geçiş durumu: GNSS kesildiği anda cihaz hemen "holdover"
demiyor, faz bir süre daha kilitli kalıyor.

## Isınma

| Değer | Kaynak |
|---|---|
| Atomik kilide < 2 dakika | §1.1 |
| LOCK_OK tipik olarak < 20 dakika | §2.5 |
| Fazların ns seviyesinde tam oturması 24 saate kadar | §2.9, Şekil 2.20 |
| Güç: ısınmada ~18 W, birkaç dakika sonra < 5,6 W | §2.2 |
| CSAC seçeneği: < 1,4 W kalıcı | §2.2 |

§1.1'deki "< 2 dakika" ifadesi **CSAC** varyantına aittir; incelenen rubidyum
cihazı için ölçülmüş bir geçiş süresi değildir.

## Diğer

| Değer | Kaynak |
|---|---|
| Seri: 115200 baud, 8N1, akış kontrolü yok | §2.2 |
| Sıcaklık aralığı −40 … +70 °C | §1.1 |
| EFC Relative: −100 % … +100 % | §3.7.1 |
| EFC Absolute: ppt (1E-12) cinsinden | §3.7.2 |
| `DIAG:LIFetime:COUNt?` saat cinsinden | §3.7.5 |
| Jamming seviyesi aralığı 0–255 | §3.6.18 |

---

## Modelin ürettiği ısınma profili

τ = 90 s ile. Sıcaklık hızlı oturur, GNSS kilidi ayrı ve yavaş bir süreçtir:

| Dakika | PCB (°C) | `SERVo:STATe?` | `SYNC:LOCKED?` |
|---|---|---|---|
| 0 | 25,0 | 0 | 0 |
| 1 | 38,5 | 0 | 0 |
| 2 | 45,5 | 2 | 0 |
| 3 | 49,0 | 2 | 0 |
| 5 | 51,8 | 2 | 0 |
| 20 | 52,8 | 6 | 1 |

Bu tablo **model çıktısıdır**, zaman hizalı donanım ölçümü değildir.
