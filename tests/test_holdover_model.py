"""
test_holdover_model.py

Holdover hata birikimi modeli (models/holdover.py) icin testler.

Bu testler MODELI DOGRUDAN cagirir -- seri port, parser ya da DeviceState
devrede degildir. Model saf fonksiyonlardan olustugu icin "3.24 saat
gecmis olsaydi" senaryosunu gercek zamanda beklemeden, sureyi parametre
vererek test edebiliyoruz.

Calistirmak icin (depo kokunden):
    pytest tests/test_holdover_model.py -v
"""
import pytest

from gnsdo_simulator.models.holdover import holdover_tint_seconds


@pytest.mark.parametrize("seconds", [0, -1, 3600, 86400, 30 * 86400])
@pytest.mark.parametrize("offset", [-1.8e-11, 0.0, 1.8e-11])
def test_linear_signed_accumulation_without_ageing(seconds, offset):
    """
    Birikim TAM DOGRUSAL olmali: hicbir surede ikinci dereceden bir
    katki cikmamali.

    Bu testin asil isi bir REGRESYON duvari olmak. Modelde eskiden
    (D/2)*t^2 yaslanma terimi vardi ve kilavuz §2.9'daki 8E-14 degeri
    yaslanma katsayisi sanilmisti -- ama o bir Allan sapmasi rakamidir.
    30 GUNLUK sureyi de sinamamizin sebebi bu: kuadratik bir
    terim kisa surede gorunmez, uzun surede belirginlesir. Biri geri
    gelirse buradan yakalanir.

    Isaret ve sifir da ayni testte: y_h negatifse TINT negatif yonde
    buyumeli, sifirsa faz hic kaymamali. Negatif sure anlamsiz oldugu
    icin giris degeri aynen donmeli.
    """
    entry = 12e-9
    expected = entry + offset * max(0, seconds)
    assert holdover_tint_seconds(seconds, entry, offset) == pytest.approx(
        expected, rel=1e-12, abs=1e-18)


def test_paper_threshold_and_example_values():
    """
    Bildiride YAZILI olan sayilari sabitler. Bildiri ile kod arasinda
    sessiz bir ayrisma olusmasin diye bu degerler testte duruyor:

        y_h = 1.8e-11, x0 = 0 ile
        1 saat -> 64.8 ns
        1 gun  -> 1.5552 us
        210 ns saglik esigi (§3.6.18, HEALTH 0x4) -> 3.24 saat

    Esik gecisi iki yandan sinaniyor: bir saniye once asilmamis, bir
    saniye sonra asilmis olmali.
    """
    assert holdover_tint_seconds(3600, 0, 1.8e-11) == pytest.approx(64.8e-9)
    assert holdover_tint_seconds(86400, 0, 1.8e-11) == pytest.approx(1.5552e-6)
    crossing = 210e-9 / 1.8e-11
    assert holdover_tint_seconds(crossing - 1, 0, 1.8e-11) < 210e-9
    assert holdover_tint_seconds(crossing + 1, 0, 1.8e-11) > 210e-9


def test_entering_holdover_preserves_phase_with_noise_enabled():
    """
    FAZ SUREKLIDIR: holdover'a girildigi anda TINT ziplamamali.

    Bu test gercek bir hatayi yakaladi. x0 ANLIK okuma oldugu
    icin giristeki jitter'i zaten iceriyordu; birikim hesabi bunun
    uzerine jitter'i BIR KEZ DAHA ekliyordu. Sonuc: holdover'a girer
    girmez faz, olcum degisimi kadar ziplıyordu.

    Olcum degisimi ACIK olarak sinaniyor (noise_scale varsayilan) --
    kapali olsaydi hata hic gorunmezdi.
    """
    from datetime import datetime, timedelta
    from gnsdo_simulator.device_state import (
        DeviceState, current_tint_seconds, enter_holdover)

    now = datetime(2026, 1, 1, 12)
    state = DeviceState(process_started_at=now - timedelta(seconds=400))
    before = current_tint_seconds(state, now)
    enter_holdover(state, now)
    assert current_tint_seconds(state, now) == pytest.approx(before, abs=1e-18)
