"""
test_commands.py

Sistem komutlari (*IDN?, HELP?, SYST:STAT?) icin testler.

pytest calistirmak icin (repo kok dizininden):
    pytest tests/test_commands.py -v
"""

import sys
import os
import time

import pytest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gnsdo_simulator.device_state import DeviceState, is_locked
from gnsdo_simulator.scpi_parser import SCPIParser
from gnsdo_simulator.commands.system import register_system_commands
from gnsdo_simulator.commands.gps import register_gps_commands
from gnsdo_simulator.commands.ptime import register_ptime_commands
from gnsdo_simulator.commands.sync import register_sync_commands
from gnsdo_simulator.commands.diagnostic import register_diagnostic_commands
from gnsdo_simulator.commands.measure import register_measure_commands
from gnsdo_simulator.commands.csac import register_csac_commands
from gnsdo_simulator.commands.gyro import register_gyro_commands
from gnsdo_simulator.commands.servo import register_servo_commands


def make_test_parser() -> SCPIParser:
    """
    Her testte sifirdan, temiz bir parser + state kurmak icin
    kucuk bir yardimci fonksiyon. Boylece testler birbirini
    etkilemez (her biri kendi bagimsiz DeviceState'iyle calisir).

    Artik TUM komut gruplarini kaydediyoruz, boylece HELP? testi ve
    genel komut testleri gercek, tam bir simulator'i yansitiyor.
    """
    state = DeviceState()
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_gps_commands(parser, state)
    register_ptime_commands(parser, state)
    register_sync_commands(parser, state)
    register_diagnostic_commands(parser, state)
    register_measure_commands(parser, state)
    register_csac_commands(parser, state)
    register_servo_commands(parser, state)
    register_gyro_commands(parser, state)
    return parser


def make_test_parser_with_state():
    """
    make_test_parser() ile ayni kurulumu yapar ama parser'in YANINDA
    DeviceState'i de dondurur.

    Nicin ayri bir fonksiyon? Bazi testlerin state'e dogrudan
    dokunmasi gerekiyor (ornegin holdover baslangicini geriye
    tarihleyip "5 saat gecmis olsaydi" senaryosunu kurmak icin).
    Mevcut make_test_parser()'in donus tipini degistirmek yerine
    yeni bir yardimci ekliyoruz -- boylece onu kullanan onlarca test
    oldugu gibi calismaya devam ediyor.
    """
    state = DeviceState()
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_gps_commands(parser, state)
    register_ptime_commands(parser, state)
    register_sync_commands(parser, state)
    register_diagnostic_commands(parser, state)
    register_measure_commands(parser, state)
    register_csac_commands(parser, state)
    register_servo_commands(parser, state)
    register_gyro_commands(parser, state)
    return parser, state


def test_idn():
    parser = make_test_parser()
    response = parser.dispatch("*IDN?")

    assert response is not None
    # GERCEK cihaz formati: "Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev X.XX"
    # (seri numarasi burada YOK -- eski 4 alanli varsayimimiz yanlisti)
    assert response == "Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 1.17"


def test_idn_uses_device_state():
    """
    *IDN? cevabinin gercekten DeviceState'ten okundugunu kanitlar --
    state'i degistirince cevabin da degismesi lazim.
    """
    state = DeviceState(firmware_version="2.0")
    parser = SCPIParser()
    register_system_commands(parser, state)

    response = parser.dispatch("*IDN?")
    assert response == "Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 2.0"


def test_help():
    parser = make_test_parser()
    response = parser.dispatch("HELP?")

    assert response is not None
    assert "*IDN?" in response
    assert "SYST:STAT?" in response
    # Artik GPS komutlari da kayitli, HELP? bunlari da gostermeli
    # (elle guncellenen bir liste degil, parser'in gercek kayitlarindan
    # otomatik uretiliyor -- bunu kanitliyoruz)
    assert "GPS?" in response
    assert "GPS:SAT:TRAC:COUN?" in response


def test_gps():
    parser = make_test_parser()

    # Varsayilan DeviceState: 8 uydu takip ediliyor (>= 4), yani "3D Fix" olmali
    gps_response = parser.dispatch("GPS?")
    assert gps_response is not None
    lines = gps_response.split("\r\n")
    assert len(lines) == 22
    assert "GPS Receiver Status: 3D Fix" in lines
    assert "TRACKED SATS :8" in lines
    assert "VISIBLE SATS :12" in lines
    assert "N,4047.2368" in lines  # gercek konumdan donusturulmus enlem
    assert "HOLD POSITION:-267998828,-430158341,385929826" in lines

    assert parser.dispatch("GPS:SAT:TRAC:COUN?") == "8"
    assert parser.dispatch("GPS:SAT:VIS:COUN?") == "12"


def test_gps_no_fix_when_few_satellites():
    """
    GPS? cevabinin gercekten DeviceState'e bagli oldugunu kanitlar:
    takip edilen uydu sayisi esigin altina dusunce, konumla ilgili
    TUM alanlar (enlem/boylam/yukseklik/ECEF/sure/varyans) gercek
    cihazdaki gibi sifirlanmali/"gecersiz" degerlere donmeli.
    """
    state = DeviceState(gnss_satellites_tracking=2, gnss_satellites_visible=2)
    parser = SCPIParser()
    register_system_commands(parser, state)
    register_gps_commands(parser, state)

    gps_response = parser.dispatch("GPS?")
    assert gps_response is not None
    lines = gps_response.split("\r\n")
    assert "GPS Receiver Status: No Fix" in lines
    assert "N,   0.0000" in lines
    assert "E,   0.0000" in lines
    assert "0.00 m" in lines
    # Uydu sayilari GERCEK degerleri gostermeye devam etmeli (zorla 0 yapilmiyor)
    assert "TRACKED SATS :2" in lines
    assert "VISIBLE SATS :2" in lines
    # HOLD POSITION fix olsun olmasin AYNI kalmali (gercek cihazda oyleydi)
    assert "HOLD POSITION:-267998828,-430158341,385929826" in lines


def test_syst_stat():
    parser = make_test_parser()
    response = parser.dispatch("SYST:STAT?")

    assert response is not None
    lines = response.split("\r\n")
    assert lines[0].startswith("LN Rb GPSDO (PRE)")
    assert "Serial Number : 122301668" in lines[0]
    assert "Tracking:8        Not Tracking: 4" in lines
    assert "GPS Receiver Status: 3D Fix             GPSDO Status : Locked" in lines


def test_syst_stat_reflects_state():
    """
    SYST:STAT?'in "GPSDO Status" alaninin, state'e gore
    DEGISTIGINI kanitlar -- her farkli durumda dogru metni
    icermesi lazim (artik tek kelimelik cevap degil, tam bir
    rapor icinde bir alan).
    """
    from gnsdo_simulator.commands.system import register_system_commands

    # 1) Donanim arizasi -- en yuksek oncelikli, digerlerini gecersiz kilar
    state = DeviceState(hardware_fault=True)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Fault" in parser.dispatch("SYST:STAT?")

    # 2) Holdover
    state = DeviceState(holdover=True, sync_locked=False)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Holdover" in parser.dispatch("SYST:STAT?")

    # 3) warming-up senaryosu aktif (warmup_started_at dolu), henuz
    #    2 dakika gecmemis -> Warming Up
    state = DeviceState(sync_locked=False, warmup_started_at=datetime.now())
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Warming Up" in parser.dispatch("SYST:STAT?")

    # 4) Uzun suredir calisiyor ama kilitlenememis (warmup_started_at
    #    YOK -- yani bu bir isinma degil, kalici bir sorun) -> Not Locked
    state = DeviceState(sync_locked=False)
    parser = SCPIParser()
    register_system_commands(parser, state)
    assert "GPSDO Status : Not Locked" in parser.dispatch("SYST:STAT?")


def test_locked_requires_fix():
    """
    YENI KURAL: GPS fix'i yoksa (yeterli uydu takip edilmiyorsa),
    is_locked() sync_locked ne olursa olsun False donmeli -- gercek
    dunyada osilator, GPS referansi olmadan kilitlenemez. Bu, daha
    once EKSIK olan bir tutarlilik kontrolu.
    """
    # sync_locked=True olsa BILE, fix yoksa (tracking < 4) kilitli SAYILMAMALI
    state = DeviceState(sync_locked=True, gnss_satellites_tracking=2)
    assert is_locked(state) is False

    # Yeterli uydu VARSA ve sync_locked=True ise, gercekten kilitli olmali
    state = DeviceState(sync_locked=True, gnss_satellites_tracking=8)
    assert is_locked(state) is True


def test_case_insensitive_command():
    parser = make_test_parser()

    assert parser.dispatch("*idn?") == parser.dispatch("*IDN?")
    assert parser.dispatch("help?") == parser.dispatch("HELP?")


def test_unknown_command():
    parser = make_test_parser()
    assert parser.dispatch("NOT:A:REAL:COMMAND?") is None


def test_ptime():
    """
    PTIME komutlari sistem saatinden geldigi icin sabit bir deger
    bekleyemeyiz -- onun yerine FORMATIN dogru oldugunu kontrol
    ediyoruz (ornegin PTIME:TIME? "SS,DD,SS" seklinde 3 sayidan
    olusmali).
    """
    parser = make_test_parser()

    time_response = parser.dispatch("PTIME:TIME?")
    assert time_response is not None
    parts = time_response.split(",")
    assert len(parts) == 3  # saat, dakika, saniye

    time_string_response = parser.dispatch("PTIME:TIME:STRING?")
    assert time_string_response is not None
    assert time_string_response.count(":") == 2  # "HH:MM:SS"

    date_response = parser.dispatch("PTIME:DATE?")
    assert date_response is not None
    assert len(date_response.split(",")) == 3  # yil, ay, gun

    # PTIME? artik gercek cihaz ciktisina gore ETIKETLI 5 satir:
    # "DATE :...", "TIME :...", "TINTerval :...", "OUTput :...",
    # "LEAPSECOND :..."
    ptime_response = parser.dispatch("PTIME?")
    assert ptime_response is not None
    lines = ptime_response.split("\r\n")
    assert len(lines) == 5
    assert lines[0].startswith("DATE :")
    assert lines[1].startswith("TIME :")
    assert lines[2].startswith("TINTerval :")
    assert lines[3] in ("OUTput :0", "OUTput :1")
    assert lines[4] == "LEAPSECOND :18"


def test_sync():
    parser = make_test_parser()

    # SYNC? artik gercek cihaz ciktisina gore ETIKETLI 12 satir
    sync_response = parser.dispatch("SYNC?")
    assert sync_response is not None
    lines = sync_response.split("\r\n")
    assert len(lines) == 12
    assert "1PPS LOCK STATUS  : 1" in lines  # varsayilan DeviceState: kilitli
    assert "HOLDOVER STATE: NONE" in lines
    assert any(line.startswith("HEALTH STATUS : 0x") for line in lines)

    assert parser.dispatch("SYNC:LOCKED?") == "1"

    # HEALTH? artik hex bit-mask -- "0x" ile baslamali, gecerli hex olmali
    health = parser.dispatch("SYNC:HEALTH?")
    assert health is not None
    assert health.startswith("0x")
    int(health, 16)  # gecerli bir hex sayi mi (hata firlatirsa test patlar)

    # TINT icin tam degeri degil, bir sayi oldugunu kontrol edelim
    tint = parser.dispatch("SYNC:TINT?")
    assert tint is not None
    float(tint)  # sayiya cevrilebiliyor mu (hata firlatirsa test patlar)


def test_holdover_transition():
    """
    Dokumanin ozellikle istedigi test: SYNC:HOLD:INIT komutundan
    SONRA, SYNC:LOCKED?'in 0'a dusmesi ve SYNC:HOLD:DUR?'un artan
    bir sure dondurmesi gerekiyor.

    NOT: SYNC:HOLD:DUR? gercek cihazda "sure,durum" seklinde IKI
    sayi doner (bkz. commands/sync.py), o yuzden burada virgulden
    once ve sonraki kismi ayri ayri kontrol ediyoruz.
    """
    parser = make_test_parser()

    # Once normal durumda kilitli olmali
    assert parser.dispatch("SYNC:LOCKED?") == "1"
    assert parser.dispatch("SYNC:HOLD:DUR?") == "0,0"

    # Holdover'i baslat
    response = parser.dispatch("SYNC:HOLD:INIT")
    assert response == ""  # setter, soylenecek bir sey yok ama cevap bos string (None degil)

    # Artik kilitli OLMAMALI
    assert parser.dispatch("SYNC:LOCKED?") == "0"
    sync_response = parser.dispatch("SYNC?")
    assert sync_response is not None
    assert "1PPS LOCK STATUS  : 0" in sync_response
    assert "HOLDOVER STATE: ACTIVE" in sync_response

    # Bir sure gecmesini simule edip DUR?'un artip artmadigina bakalim
    time.sleep(0.2)
    dur_response = parser.dispatch("SYNC:HOLD:DUR?")
    assert dur_response is not None
    duration_str, holdover_flag = dur_response.split(",")
    assert float(duration_str) > 0
    assert holdover_flag == "1"

    # Recovery baslatinca tekrar kilitli olmali
    parser.dispatch("SYNC:HOLD:REC:INIT")
    assert parser.dispatch("SYNC:LOCKED?") == "1"

    # DEGISTI: eskiden burada "0,0" bekliyorduk, ama bu kilavuza
    # AYKIRIYDI. §3.6.1: "If the Receiver is not in holdover, the
    # response quantifies the PREVIOUS holdover." Yani holdover
    # bittikten sonra sorgu, BITEN holdover'in suresini ve durum
    # bayragi olarak 0 dondurmelidir.
    dur_after = parser.dispatch("SYNC:HOLD:DUR?")
    assert dur_after is not None
    previous_duration, holdover_flag = dur_after.split(",")
    assert float(previous_duration) > 0  # yukarida ~0.2 sn holdover yasandi
    assert holdover_flag == "0"  # artik holdover'da DEGILIZ


def test_sync_source_mode_setter():
    parser = make_test_parser()
    response = parser.dispatch("SYNC:SOUR:MODE EXTERNAL")
    assert response == ""  # cevap yok ama komut taninmis (None degil)


def test_diag():
    """DIAG? taban degerleri (gurultu kapali)."""
    parser, state = make_test_parser_with_state()
    state.noise_scale = 0.0

    response = parser.dispatch("DIAG?")
    assert response is not None
    # ONEMLI: gercek cihaz ciktisinda "Fault:" satiri YOK -- artik
    # bu satiri beklemiyoruz.
    assert "Fault:" not in response
    assert "EFControl Relative: -0.410000%" in response
    assert "EFControl Absolute: -82.000000" in response
    assert "Lifetime : +871" in response


def test_diag_efc_absolute_derived_from_relative():
    """
    GERCEK CIHAZDA KESFEDILEN BAGINTI: EFControl Absolute her zaman
    Relative'in 200 katidir. Dort ardisik kayitta da tutuyor:

        -0.410000%  ->  -82        -0.440000%  ->  -88
        -0.640000%  ->  -128       -0.105000%  ->  -21

    Ikisi ayni fiziksel buyuklugun farkli birimlerdeki ifadesi
    (Relative yuzde, Absolute parts-per-trillion). Bagimsiz alanlar
    olarak tutulsalardi birbiriyle CELISEN degerler uretebilirlerdi.

    Bu testi zamanla degisen degerlerle yapiyoruz -- bagintinin
    sadece taban degerde degil, HER AN gecerli oldugunu dogrulamak icin.
    """
    import re
    from datetime import timedelta

    parser, state = make_test_parser_with_state()

    for saniye in range(0, 120, 13):
        state.process_started_at = datetime.now() - timedelta(seconds=saniye)
        response = parser.dispatch("DIAG?")
        assert response is not None

        relative = float(re.search(r"Relative: (-?[\d.]+)%", response).group(1))
        absolute = float(re.search(r"Absolute: (-?[\d.]+)", response).group(1))

        assert absolute == pytest.approx(relative * 200.0, rel=1e-6)


def test_measure():
    """
    Olcum komutlarinin TABAN degerleri.

    Gurultuyu kapatiyoruz (noise_scale = 0): burada test edilen sey
    "hangi alan hangi komuta bagli" ve bicimlendirme -- gurultunun
    kendisi degil. Gurultu davranisi ayri testlerde dogrulaniyor.
    """
    parser, state = make_test_parser_with_state()
    state.noise_scale = 0.0

    assert parser.dispatch("MEAS:TEMP?") == "52.8000"
    assert parser.dispatch("MEAS:VOLT?") == "1.660"
    # MEAS:CURR? AKIM DEGIL SICAKLIK doner (kilavuz §3.8.3, "legacy
    # SCPI command"). Gercek cihaz: MEAS:CURR? -> 51.3210 iken
    # hemen yanindaki MEAS:TEMP? -> 51.1479 idi.
    assert parser.dispatch("MEAS:CURR?") == "54.1200"
    assert parser.dispatch("MEAS:POW?") == "11.70"

    # MEAS? artik gercek cihaz ciktisina gore ETIKETLI 4 satir,
    # CSAC Temperature dahil. CSAC sicakligi PCB'den TURETILIYOR
    # (+1.32 C, gercek cihaz kayitlarindan).
    meas_response = parser.dispatch("MEAS?")
    assert meas_response is not None
    assert meas_response.split("\r\n") == [
        "PCB Temperature: 52.8000",
        "CSAC Temperature: 54.12",
        "TCXO Voltage: 1.660",
        "Power Supply Voltage: 11.70",
    ]


def test_csac():
    parser = make_test_parser()
    # Varsayilan DeviceState: sync_locked=True -> saglikli -> "0"
    # (GERCEK cihaz ciktisi ciplak sayi doner, hex degil)
    assert parser.dispatch("CSAC:STATUS?") == "0"
    assert parser.dispatch("CSAC:SN?") == "2209MX04906"

    # CSAC? artik gercek cihaz ciktisina gore ETIKETLI 13 satir
    csac_response = parser.dispatch("CSAC?")
    assert csac_response is not None
    lines = csac_response.split("\r\n")
    assert len(lines) == 13
    assert lines[0] == "RS232: OK"
    assert lines[2] == "STATUS: 0"
    assert lines[10] == "SN: 2209MX04906"
    assert lines[12].startswith("LIFETIME: ")

    # MAC? gercek cihazda CSAC? ile BIREBIR AYNI sonucu dondurmeli (alias)
    assert parser.dispatch("MAC?") == csac_response


def test_csac_status_reflects_lock_state():
    """CSAC:STATUS?'in gercekten kilit durumuna bagli oldugunu kanitlar."""
    from gnsdo_simulator.commands.csac import register_csac_commands

    state = DeviceState(sync_locked=False)
    parser = SCPIParser()
    register_csac_commands(parser, state)
    assert parser.dispatch("CSAC:STATUS?") == "1"

def test_holdover_tint_grows_over_time_via_scpi():
    """
    Holdover'da SYNC:TINT? SCPI cevabi zamanla BUYUMELI.

    Bu, modelin dogrudan degil KOMUT KATMANI uzerinden testi -- yani
    gercek bir istemcinin gordugu sey. Model dogru calissa bile
    komutlara baglanmasi unutulmus olabilirdi; bu test onu yakalar.

    Gercek zamanda saatlerce beklemek yerine holdover baslangicini
    geriye tarihliyoruz.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()
    parser.dispatch("SYNC:HOLD:INIT")

    okumalar = []
    for saat in [0, 1, 5]:
        # "su kadar sure gecmis olsaydi" -- gercek zamanda beklemek
        # yerine holdover baslangicini geriye tarihliyoruz
        state.holdover_started_at = datetime.now() - timedelta(hours=saat)
        cevap = parser.dispatch("SYNC:TINT?")
        assert cevap is not None
        okumalar.append(float(cevap))

    # Kesin artan olmali -- holdover uzadikca hata birikir
    assert okumalar == sorted(okumalar)
    assert okumalar[0] < okumalar[1] < okumalar[2]

    # 5 saat sonra 210 ns'lik saglik esigi (§3.6.18) asilmis olmali
    assert abs(okumalar[2]) > 210e-9


def test_holdover_health_matches_manual_worked_example():
    """
    Kilavuz §3.6.18 su ornegi veriyor:

        "if the unit is in GNSS holdover and the UTC phase offset is
         > 250ns then ... 0x10 | 0x4 = 0x14"

    Yani uzun sureli holdover + 210 ns ustu faz kaymasi = 0x14.
    Modelimiz bu birlesimi KENDILIGINDEN uretmeli; hedefleyerek
    kodlamadik, fizik oraya goturuyor.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()
    parser.dispatch("SYNC:HOLD:INIT")

    # 0x8 (calisma suresi < 200 sn) karismasin diye programi
    # "coktan acilmis" say
    state.process_started_at = datetime.now() - timedelta(seconds=1000)

    # 5 saatlik holdover: hem holdover>60sn (0x10) hem faz>210ns (0x4)
    state.holdover_started_at = datetime.now() - timedelta(hours=5)

    assert parser.dispatch("SYNC:HEALTH?") == "0x14"


def test_locked_tint_has_no_trend():
    """
    Kilitliyken TINT'in TRENDI olmamali -- yani birikmemeli.

    ONEMLI AYRIM (FAZ 2'de netlesti): "trend yok" demek "hic
    degismiyor" demek DEGIL. Gercek cihazda kilitliyken bile okuma
    jitter yapar (GNSS 1PPS jitter'i, §1.1'e gore 0.2 ns mertebesinde).
    Yasak olan sey TEK YONLU BIRIKIMDIR -- cunku kapali kontrol
    dongusu TINT'i surekli sifira ceker; oraya bir trend eklemek
    dongunun calismadigi anlamina gelirdi.

    Bu yuzden test, degerin SABIT oldugunu degil, dar bir bant
    icinde KALDIGINI dogrular.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()

    # Gurultuyu kapatinca deger tamamen sabit olmali (trend yok)
    state.noise_scale = 0.0
    assert parser.dispatch("SYNC:TINT?") == parser.dispatch("SYNC:TINT?")

    # Gurultu acikken: uzun sure boyunca dar bir bant icinde kalmali,
    # yani jitter yapar ama BIRIKMEZ. Saatleri ileri sararak kontrol
    # ediyoruz -- holdover olsaydi bu araligi coktan asardi.
    state.noise_scale = 1.0
    okumalar = []
    # DIKKAT -- ornekleme araligi jitter PERIYODUNUN TAM KATI OLMAMALI.
    # Ilk yazimda saat basi ornekleme yapmistik; jitter periyodu 5 sn
    # oldugu icin 3600 sn tam 720 cevrime denk geliyordu ve her ornek
    # AYNI faza dusuyordu (ortusme/aliasing). Sonuc: sinyal sabitmis
    # gibi gorunuyordu. Periyotla ortak boleni olmayan bir adim
    # seciyoruz.
    for adim in range(24):
        gecen = adim * 3.7  # 5 sn'lik periyotla ortak katı yok
        state.process_started_at = datetime.now() - timedelta(seconds=gecen)
        cevap = parser.dispatch("SYNC:TINT?")
        assert cevap is not None
        okumalar.append(float(cevap))

    # Jitter genligi 12 ns (gercek cihaz kayitlarindan) -- okumalar
    # SIFIRIN ETRAFINDA bu bant icinde kalmali. Holdover olsaydi
    # 5 saatte 200 ns'yi asardi; buradaki sinir onun cok altinda.
    for deger in okumalar:
        assert abs(deger) < 15e-9

    # Ayrica gercek cihaz gibi HEM ARTI HEM EKSI deger gorulmeli --
    # sifirin tek tarafinda kalsaydi bu bir trend (offset) olurdu
    assert min(okumalar) < 0 < max(okumalar)


def test_measurements_vary_over_time():
    """
    Gurultunun GERCEKTEN calistigini dogrular: ayni olcum, farkli
    zamanlarda farkli degerler vermeli.

    Bu test olmasa gurultu sessizce devre disi kalabilir (ornegin
    bir alan yanlislikla taban degeri dondurmeye devam ederse) ve
    kimse fark etmezdi.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()

    okumalar = set()
    for saniye in range(0, 300, 30):
        state.process_started_at = datetime.now() - timedelta(seconds=saniye)
        okumalar.add(parser.dispatch("MEAS:TEMP?"))

    # 10 farkli anda en az birkac farkli deger gorulmeli
    assert len(okumalar) > 3


def test_same_instant_gives_same_reading():
    """
    FIZIKSEL GEREKLILIK: cihazin sicakligi belli bir ANDA belli bir
    degerdir; art arda iki kez sormak sonucu degistirmemeli.

    Bu test, "her sorguda rastgele sayi uret" yaklasimini elerdi.
    Zamani sabitleyerek ayni ani iki kez sorguluyoruz.
    """
    parser, state = make_test_parser_with_state()

    sabit_an = state.process_started_at
    state.process_started_at = sabit_an

    ilk = parser.dispatch("MEAS?")
    ikinci = parser.dispatch("MEAS?")

    # Ayni an (mikrosaniye farkiyla) -- degerler pratikte ayni olmali
    assert ilk == ikinci


def test_servo_state_query():
    """
    SERVo:STATe? cihazin isinma/kilitlenme asamasini bildirir
    (kilavuz §3.10.3). Coktan isinmis bir cihazda 6 (kilitli) olmali.
    """
    parser, state = make_test_parser_with_state()
    assert parser.dispatch("SERV:STATE?") == "6"
    # Kilavuzun uzun yazimlari da calismali
    assert parser.dispatch("SERVO:STATE?") == "6"


def test_servo_state_distinguishes_warmup_from_locking():
    """
    SERVo:STATe?'IN ASIL DEGERI: SYNC:LOCKED?'in ayirt EDEMEDIGI iki
    durumu ayirir.

    Cihaz aciliskan kilide tek adimda gecmez:
        0 isinma  ->  2 kilitleniyor  ->  6 kilitli
    SYNC:LOCKED? ilk ikisinde de "0" doner -- yani bir izleme
    yazilimi "neden hala kilitlenmedi?" sorusuna cevap veremez.
    SERVo:STATe? ise cihazin henuz mi isindigini, yoksa isinip da
    GNSS'e mi kilitlenemedigini soyler.
    """
    from datetime import timedelta

    from gnsdo_simulator.models.warmup import ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS

    parser, state = make_test_parser_with_state()
    state.warmup_started_at = datetime.now()

    # Isinma: STATe 0, LOCKED? 0
    assert parser.dispatch("SERV:STATE?") == "0"
    assert parser.dispatch("SYNC:LOCKED?") == "0"

    # Kilitleniyor: STATe 2, ama LOCKED? HALA 0 -- iste fark burada
    state.warmup_started_at = datetime.now() - timedelta(
        seconds=ATOMIC_LOCK_SECONDS + 10
    )
    assert parser.dispatch("SERV:STATE?") == "2"
    assert parser.dispatch("SYNC:LOCKED?") == "0"

    # Kilitli: ikisi de uyumlu
    state.warmup_started_at = datetime.now() - timedelta(
        seconds=GNSS_LOCK_SECONDS + 10
    )
    assert parser.dispatch("SERV:STATE?") == "6"
    assert parser.dispatch("SYNC:LOCKED?") == "1"


def test_servo_state_shows_phase_locked_holdover():
    """
    Kilavuz §3.10.3, durum 5: GNSS kaybindan sonra cihaz ANINDA
    holdover demez, ~100 saniye faz kilitli kalir.

    Bu ara durum simulatorde olmasaydi, GNSS kaybini izleyen bir test
    uygulamasi gercek cihazda gorecegi gecisi hic gormezdi.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()
    parser.dispatch("SYNC:HOLD:INIT")

    # Holdover'in ilk saniyeleri: faz halen kilitli (durum 5)
    assert parser.dispatch("SERV:STATE?") == "5"

    # 100 saniye sonra: tam holdover (durum 1)
    state.holdover_started_at = datetime.now() - timedelta(seconds=150)
    assert parser.dispatch("SERV:STATE?") == "1"


def test_serv_summary_matches_real_device_format():
    """
    SERV? ciktisi gercek cihaz kaydiyla BIREBIR ayni olmali
    (docs/gercek-cihaz-ciktilari.md).

    Etiketlerdeki bosluk tutarsizliklari ("LOOP:" bitisik ama
    "EFC SCALE :" ayrik, "FASTLOCK PERIOD  :" iki bosluklu) BILEREK
    korunuyor: sabit bicimde ayristiran bir istemci, bizim
    "duzelttigimiz" bir bosluk yuzunden gercek cihazda calisip
    simulatorde calismayabilir.
    """
    parser = make_test_parser()
    response = parser.dispatch("SERV?")
    assert response is not None

    assert response.split("\r\n") == [
        "SERVO: CSAC",
        "LOOP: 1",
        "DAC GAIN: 2.000",
        "EFC SCALE : 0.50",
        "PHASE CORRECTION : 1.500000",
        "EFC DAMPING: 10",
        "FILTER LENGTH: 20",
        "TEMPERATURE COMPENSATION : 0",
        "AGING COMPENSATION : -0.000547502",
        "1PPS OFFSET : 0.000 ns",
        "TRACE PORT : RS232",
        "TRACE : 0",
        "FASTLOCK : 1",
        "FASTLOCK PERIOD  : 1800",
    ]


def test_health_jamming_requires_both_conditions():
    """
    Kilavuz §3.3.28: "Any level exceeding 50 in combination to loss of
    GNSS lock will cause a SYNC:HEALTH 0x800 event".

    IKI KOSUL BIRLIKTE saglanmali. Sadece jamming yuksekse ama fix
    devam ediyorsa bayrak YANMAMALI -- gercek cihaz da oyle davraniyor.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()
    # 0x8 (calisma suresi < 200 sn) karismasin
    state.process_started_at = datetime.now() - timedelta(seconds=1000)

    # Sadece jamming yuksek, fix var -> bayrak YOK
    state.gps_jamming_level = 90
    state.gnss_satellites_tracking = 8
    assert "0x800" not in _health_bits(parser)

    # Sadece fix yok, jamming dusuk -> bayrak YOK
    state.gps_jamming_level = 5
    state.gnss_satellites_tracking = 0
    assert 0x800 & _health_value(parser) == 0

    # Ikisi birden -> bayrak VAR
    state.gps_jamming_level = 90
    state.gnss_satellites_tracking = 0
    assert 0x800 & _health_value(parser) == 0x800


def test_health_filter_loop_bit_during_warmup_only():
    """
    Kilavuz §3.6.18, 0x1000: filtre osilator dongusu kilitli degil.

    Isinma ve kilitlenme asamalarinda yanar, kilitlendikten sonra soner.

    HOLDOVER'DA YANMAMALI -- kilavuz §2.5: GNSS beslemesi olmadan cihaz
    "Rubidyum holdover modunda" calisir ve LED'i "OCXO'yu Rubidyum
    referansina icsel olarak kilitledigini, cihazin SAGLIKLI oldugunu
    ve BEKLEYEN OLAY OLMADIGINI" bildirir. Yani GNSS kaybi filtre
    dongusunu bozmaz: o dongu OCXO'yu Rubidyum'a kilitler, GNSS'e degil.
    """
    from datetime import timedelta

    from gnsdo_simulator.models.warmup import ATOMIC_LOCK_SECONDS, GNSS_LOCK_SECONDS

    parser, state = make_test_parser_with_state()
    state.process_started_at = datetime.now() - timedelta(seconds=1000)

    # Isinma -> 0x1000 yanar
    state.warmup_started_at = datetime.now()
    assert 0x1000 & _health_value(parser) == 0x1000

    # Kilitleniyor -> hala yanar
    state.warmup_started_at = datetime.now() - timedelta(
        seconds=ATOMIC_LOCK_SECONDS + 10
    )
    assert 0x1000 & _health_value(parser) == 0x1000

    # Kilitli -> soner
    state.warmup_started_at = datetime.now() - timedelta(
        seconds=GNSS_LOCK_SECONDS + 10
    )
    assert 0x1000 & _health_value(parser) == 0

    # Holdover -> YANMAMALI (filtre dongusu Rubidyum'a kilitli kalir)
    parser.dispatch("SYNC:HOLD:INIT")
    state.holdover_started_at = datetime.now() - timedelta(seconds=300)
    assert 0x1000 & _health_value(parser) == 0


def test_freq_error_estimate_varies():
    """
    FEE sabit degil. Kilavuz §3.6.10'a gore 1000 saniyelik olcum
    araligiyla hesaplanan, Allan varyansina benzer bir buyukluktur --
    dolayisiyla oynar. Gercek cihaz kayitlarindaki uc ardisik sorgu:
    1.31E-11, 2.49E-11, 1.59E-11.
    """
    import re
    from datetime import timedelta

    parser, state = make_test_parser_with_state()

    degerler = set()
    for saniye in range(0, 300, 25):
        state.process_started_at = datetime.now() - timedelta(seconds=saniye)
        response = parser.dispatch("SYNC?")
        assert response is not None
        degerler.add(re.search(r"FREQ ERROR ESTIMATE : (\S+)", response).group(1))

    assert len(degerler) > 3


def test_holdover_accumulation_uses_frozen_fee():
    """
    Holdover birikimi, KAYIP ANINDAKI frekans hatasina dayanmali --
    anlik FEE'ye degil.

    Nicin: FEE artik zamanla oynuyor. Birikim anlik degeri kullansaydi,
    gecmiste birikmis hata sonradan DEGISIRDI -- fiziksel olarak sacma.
    Bir kere olan sey, sonradan baska turlu olmus sayilamaz.
    """
    parser, state = make_test_parser_with_state()

    parser.dispatch("SYNC:HOLD:INIT")
    dondurulmus = state.holdover_entry_fee

    # Taban FEE'yi degistirsek bile birikim dondurulmus degeri kullanmali
    state.freq_error_estimate = 9.9e-10
    assert state.holdover_entry_fee == dondurulmus


def _health_value(parser) -> int:
    """SYNC:HEALTH? cevabini sayiya cevirir."""
    cevap = parser.dispatch("SYNC:HEALTH?")
    assert cevap is not None
    return int(cevap, 16)


def _health_bits(parser) -> str:
    cevap = parser.dispatch("SYNC:HEALTH?")
    assert cevap is not None
    return cevap


def test_gyro_summary_matches_real_device_format():
    """
    GYRO? ciktisi gercek cihaz kaydiyla ayni bicimde olmali
    (docs/gercek-cihaz-ciktilari.md). GLOAD satiri haric -- o bir
    sensor okumasi oldugu icin gurultulu.

    Bicim tutarsizliklari BILEREK korunuyor: "MODE :" ayrik ama
    "TRACE:" bitisik; G-SENSITIVITY satirinda X ve Y'den sonra iki
    nokta yokken Z'den sonra var.
    """
    parser = make_test_parser()
    response = parser.dispatch("GYRO?")
    assert response is not None

    satirlar = response.split("\r\n")
    assert satirlar[0] == "MODE : 0"
    assert satirlar[1] == "TRACE: 0"
    assert satirlar[2] == (
        "CALIBRATION : Offset: 0.000, 0.000, 0.000, "
        "Gain: 1.0000, 1.0000, 1.0000"
    )
    assert satirlar[3] == (
        "G-SENSITIVITY : X 0.000 mHz/g, Y 0.000 mHz/g, Z: 0.000 mHz/g"
    )
    assert satirlar[4].startswith("GLOAD : ")
    assert satirlar[5] == "PORT : RS232"


def test_gyro_gload_is_a_noisy_sensor_reading():
    """
    GLOAD bir IVMEOLCER okumasidir -- sabit olmamali, titresim ve
    elektriksel gurultu yuzunden son hanede oynamali.

    Z ekseni yaklasik -1 g olmali: cihaz duz duruyor ve YERCEKIMINI
    olcuyor. Gercek cihaz -1.063 okumustu.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()

    okumalar = set()
    for saniye in range(0, 60, 5):
        state.process_started_at = datetime.now() - timedelta(seconds=saniye)
        cevap = parser.dispatch("GYRO:GLOAD?")
        assert cevap is not None
        okumalar.add(cevap)
        z = float(cevap.split(",")[2])
        assert -1.1 < z < -1.0  # yercekimi, kucuk sapmayla

    assert len(okumalar) > 3  # gercekten oynuyor


def test_serial_echo_and_prompt_setters():
    """
    Gorev tanimindaki iki "state degistiren" komut:
    SYST:COMM:SER:ECHO ve SYST:COMM:SER:PROMPT.

    Ayrica GECERSIZ bir deger geldiginde durum DEGISMEMELI -- yanlis
    girdi yuzunden cihazin sessizce baska bir duruma gecmesi, hata
    ayiklamasi en zor davranislardan biridir.
    """
    parser = make_test_parser()

    assert parser.dispatch("SYST:COMM:SER:ECHO?") == "OFF"
    parser.dispatch("SYST:COMM:SER:ECHO ON")
    assert parser.dispatch("SYST:COMM:SER:ECHO?") == "ON"

    parser.dispatch("SYST:COMM:SER:ECHO SACMALIK")
    assert parser.dispatch("SYST:COMM:SER:ECHO?") == "ON"  # degismedi

    parser.dispatch("SYST:COMM:SER:PROMPT ON")
    assert parser.dispatch("SYST:COMM:SER:PROMPT?") == "ON"


def test_system_id_queries():
    """SYST:ID:SN? ve SYST:ID:HWrev? (kilavuz §3.9.5, §3.9.6)."""
    parser = make_test_parser()
    assert parser.dispatch("SYST:ID:SN?") == "122301668"
    assert parser.dispatch("SYST:ID:HWREV?") == "1.01.00"


def test_filter_tint_does_not_accumulate_in_holdover():
    """
    IKI FARKLI TINT OLCUMU var ve karistirilmamali:

        SYNC:TINT:CSAC?    Rubidyum 1PPS  <-> GNSS 1PPS
        SYNC:TINT:FILTer?  Filtre OCXO 1PPS <-> Rubidyum 1PPS

    GNSS kaybolunca BIRINCISI birikir (referans gitti), IKINCISI
    birikmez -- cunku filtre dongusu GNSS'e degil RUBIDYUM'a
    kilitlidir ve o calismaya devam eder (kilavuz §2.5).

    Bu ayrim modelin dogru kurulup kurulmadiginin iyi bir testidir:
    ikisini ayni sanip tek bir degere baglasaydik, filtre TINT'i de
    saatlerce birikir ve gercek cihazda olmayan bir davranis
    uretirdik.
    """
    from datetime import timedelta

    parser, state = make_test_parser_with_state()
    parser.dispatch("SYNC:HOLD:INIT")
    state.holdover_started_at = datetime.now() - timedelta(hours=5)

    ana = abs(float(parser.dispatch("SYNC:TINT:CSAC?")))
    filtre = abs(float(parser.dispatch("SYNC:TINT:FILTER?")))

    assert ana > 200e-9  # 5 saatte birikti
    assert filtre < 1e-9  # birikmedi, sadece jitter


def test_sync_fee_query_matches_summary():
    """
    SYNC:FEE? ile SYNC? ozetindeki FREQ ERROR ESTIMATE ayni ani
    ayni sekilde raporlamali -- ikisi de ayni kaynaktan okuyor.
    """
    import re

    parser = make_test_parser()

    tekil = parser.dispatch("SYNC:FEE?")
    ozet = parser.dispatch("SYNC?")
    assert tekil is not None and ozet is not None

    ozetteki = re.search(r"FREQ ERROR ESTIMATE : (\S+)", ozet).group(1)
    assert tekil == ozetteki


def test_diag_efc_queries_match_summary():
    """DIAG:ROSC:EFC:* sorgulari DIAG? ozetiyle tutarli olmali."""
    parser, state = make_test_parser_with_state()
    state.noise_scale = 0.0

    ozet = parser.dispatch("DIAG?")
    assert ozet is not None
    assert f"EFControl Relative: {parser.dispatch('DIAG:ROSC:EFC:REL?')}" in ozet
    assert f"EFControl Absolute: {parser.dispatch('DIAG:ROSC:EFC:ABS?')}" in ozet


def test_new_sync_queries_answer():
    """Yeni SYNC sorgularinin hepsi cevap vermeli (None donmemeli)."""
    parser = make_test_parser()
    for komut in [
        "SYNC:HOLD:STATE?",
        "SYNC:SOUR:STATE?",
        "SYNC:TINT:CSAC?",
        "SYNC:TINT:FILTER?",
        "SYNC:TINT:THRESHOLD?",
        "SYNC:OUT:FILTER?",
        "SYNC:OUT:1PPS:RESET?",
        "SYNC:OUT:1PPS:DOMAIN?",
    ]:
        assert parser.dispatch(komut) is not None, komut


def test_all_registered_queries_answer():
    """
    KAPSAM TESTI: kayitli HER sorgu komutu bir cevap dondurmeli.

    Nicin degerli: yeni bir komut eklerken handler'i yazip parser'a
    kaydetmeyi unutmak ya da eksik bir alan adi yuzunden calisma
    aninda patlamak kolaydir. Bu test, komut sayisi buyudukce
    tek tek test yazmadan bu tur hatalari yakalar.
    """
    parser = make_test_parser()

    for komut in parser.list_commands():
        if not komut.endswith("?"):
            continue  # setter'lar deger ister, burada kapsam disi
        cevap = parser.dispatch(komut)
        assert cevap is not None, f"{komut} cevap vermedi"
        assert cevap != "", f"{komut} bos cevap dondu"


def test_gps_position_query_matches_summary_block():
    """
    GPS:POSition? ciktisi, GPS? ozetindeki "ACTUAL POSITION" blogunun
    aynisi olmali -- ikisi de ayni kaynaktan okuyor.
    """
    parser = make_test_parser()

    tekil = parser.dispatch("GPS:POSITION?")
    ozet = parser.dispatch("GPS?")
    assert tekil is not None and ozet is not None

    for satir in tekil.split("\r\n"):
        assert satir in ozet, satir


def test_gps_jamlevel_is_readable():
    """
    Bir tutarsizligi gideriyor: jamming seviyesini SYNC:HEALTH? 0x800
    icin KULLANIYORDUK ama disaridan okunamiyordu.
    """
    parser, state = make_test_parser_with_state()
    assert parser.dispatch("GPS:JAMLEVEL?") == "5"

    state.gps_jamming_level = 120
    assert parser.dispatch("GPS:JAMLEVEL?") == "120"


def test_csac_field_queries_match_summary():
    """
    CSAC? ozetindeki her alan tek basina da sorulabilmeli ve ayni
    degeri vermeli.

    Nicin gerekli: bir izleme yazilimi genelde tek bir degeri
    periyodik okur; her seferinde 13 satirlik ozeti ayristirmak hem
    gereksiz hem kirilgan.
    """
    parser, state = make_test_parser_with_state()
    state.noise_scale = 0.0

    ozet = parser.dispatch("CSAC?")
    assert ozet is not None

    eslesmeler = {
        "RS232: ": "CSAC:RS232?",
        "STEER: ": "CSAC:STEER?",
        "MODE: ": "CSAC:MODE?",
        "TEC CONTROL: ": "CSAC:TEC?",
        "DC SIGNAL LEVEL: ": "CSAC:SIG?",
        "HEAT PACKAGE: ": "CSAC:HEAT?",
        "TEMPERATURE: ": "CSAC:TEMP?",
        "FIRMWARE REV: ": "CSAC:FW?",
    }
    for etiket, komut in eslesmeler.items():
        deger = parser.dispatch(komut)
        assert f"{etiket}{deger}" in ozet, f"{komut} ozetle uyusmuyor"


def test_ptime_leap_queries():
    """
    Artı saniye sorgulari (kilavuz §3.5.7-3.5.10).

    Kilavuz §3.5.10: DURation icin 60 = "bekleyen olay yok".
    """
    parser = make_test_parser()

    assert parser.dispatch("PTIME:LEAP:PEND?") == "0"
    assert parser.dispatch("PTIME:LEAP:DUR?") == "60"
    assert parser.dispatch("PTIME:LEAP:ACC?") == "18"
