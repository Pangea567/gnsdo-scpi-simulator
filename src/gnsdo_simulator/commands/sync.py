"""
commands/sync.py

Senkronizasyon komutlari: SYNC?, SYNC:LOCKED?, SYNC:TINT?, SYNC:HEALTH?,
ve durum degistiren (setter) komutlar: SYNC:HOLD:INIT, SYNC:HOLD:REC:INIT,
SYNC:SOUR:MODE <deger>, ve bir sorgu: SYNC:HOLD:DUR?

HOLDOVER NEDIR (kisa hatirlatma):
  Cihaz normalde GPS'e "kilitli" calisir (sync_locked=True). GPS
  sinyali kesilirse, cihaz oylece durmaz -- son bilinen dogru
  frekansi kullanarak calismaya devam eder, buna "holdover" denir.
  Holdover'dayken artik gercek zamanli bir referansa kilitli
  olmadigi icin sync_locked=False olur.

Bu dosyada iki TUR fonksiyon var:
  1. Sadece okuyan (query) fonksiyonlar -- parametre almazlar.
  2. Durum DEGISTIREN (setter) fonksiyonlar -- bir "deger" (str)
     parametresi alirlar (deger yoksa bos string "" gelir), ve
     DeviceState'i GUNCELLERLER. Bunlar register_setter() ile
     kaydedilir (bkz. scpi_parser.py'deki aciklama).
"""

from datetime import datetime
from typing import Optional

from gnsdo_simulator.device_state import DeviceState
from gnsdo_simulator.scpi_parser import SCPIParser


def make_sync_handler(state: DeviceState):
    """SYNC? -- genel senkronizasyon durumu ozeti."""

    def handler() -> str:
        if state.holdover:
            return "HOLDOVER"
        if state.sync_locked:
            return "LOCKED"
        return "NOT LOCKED"

    return handler


def make_sync_locked_handler(state: DeviceState):
    """
    SYNC:LOCKED? -- "1" (kilitli) ya da "0" (kilitli degil).
    Holdover'dayken de "0" doner, cunku artik canli referansa
    kilitli degildir.
    """

    def handler() -> str:
        return "1" if (state.sync_locked and not state.holdover) else "0"

    return handler


def make_sync_tint_handler(state: DeviceState):
    """
    SYNC:TINT? -- "time interval error", yani referansla aradaki
    zaman farkinin olcumu (saniye cinsinden). Gercek cihazlarda
    bu, gercek bir olcum devresinden gelir. Biz karmasik bir
    yakinsama/olcum modeli KURMUYORUZ (proje kararimiz geregi):
    holdover'da degilken kucuk, sabit bir deger donduruyoruz;
    holdover'dayken (referans yokken) biraz daha buyuk sabit bir
    deger donduruyoruz. Ileride gercek cihazin kilavuzuna gore
    bu sabitler kolayca degistirilebilir.
    """

    def handler() -> str:
        if state.holdover:
            return "0.000000850"  # holdover'da hata payi biraz daha buyuk (sabit varsayim)
        return "0.000000012"  # normal calismada kucuk, sabit bir deger (varsayim)

    return handler


def make_sync_health_handler(state: DeviceState):
    """SYNC:HEALTH? -- basit bir saglik ozeti, state'e gore turetilir."""

    def handler() -> str:
        if state.holdover:
            return "DEGRADED"
        return "GOOD"

    return handler


def make_sync_hold_dur_handler(state: DeviceState):
    """
    SYNC:HOLD:DUR? -- holdover ne kadar suredir devam ediyor (saniye).
    Holdover'da degilse "0" doner. Holdover'daysa, holdover'in ne
    zaman basladigini (holdover_started_at) su anki zamandan
    cikararak gecen sureyi hesapliyoruz -- yani "artan sure"
    dokumanin istedigi gibi gercekten zamanla artiyor, cunku her
    cagrildiginda YENIDEN hesaplaniyor.
    """

    def handler() -> str:
        if not state.holdover or state.holdover_started_at is None:
            return "0"
        elapsed_seconds = (datetime.now() - state.holdover_started_at).total_seconds()
        return f"{elapsed_seconds:.1f}"

    return handler


def make_sync_hold_init_setter(state: DeviceState):
    """
    SYNC:HOLD:INIT -- holdover'i BASLATAN setter komutu.
    Deger almaz (deger parametresi kullanilmiyor, "_" ile isaretledik
    -- Python'da "bu parametreyi kasitli olarak kullanmiyorum" demenin
    yaygin yolu budur).

    Cevap olarak None donuyoruz: yani "islemi yaptim ama soyleyecek
    sozel bir sey yok" -- gercek cihazlarda da bircok komut boyle
    calisir, sessizce kabul eder.
    """

    def setter(_value: str) -> Optional[str]:
        state.holdover = True
        state.sync_locked = False
        state.holdover_started_at = datetime.now()
        return None

    return setter


def make_sync_hold_rec_init_setter(state: DeviceState):
    """
    SYNC:HOLD:REC:INIT -- holdover'dan CIKISI (recovery) baslatan
    setter. Basitlestirilmis varsayimimiz: bu komut geldiginde cihaz
    aninda tekrar kilitlenmis kabul ediliyor (gercekte kademeli bir
    gecis olabilir, ama karmasik bir gecis modeli kurmuyoruz).
    """

    def setter(_value: str) -> Optional[str]:
        state.holdover = False
        state.sync_locked = True
        state.holdover_started_at = None
        return None

    return setter


def make_sync_source_mode_setter(state: DeviceState):
    """
    SYNC:SOUR:MODE <deger> -- senkronizasyon kaynak modunu degistirir.
    Ornek kullanim: "SYNC:SOUR:MODE GPS"
    Bu, DEGER PARAMETRESI kullanan ilk setter'imiz -- value burada
    bos degil, gercekten "GPS" gibi bir metin geliyor.
    """

    def setter(value: str) -> Optional[str]:
        if value:
            state.sync_source_mode = value
        return None

    return setter


def register_sync_commands(parser: SCPIParser, state: DeviceState) -> None:
    """Bu dosyadaki tum SYNC komutlarini (query + setter) parser'a kaydeder."""
    parser.register("SYNC?", make_sync_handler(state))
    parser.register("SYNC:LOCKED?", make_sync_locked_handler(state))
    parser.register("SYNC:TINT?", make_sync_tint_handler(state))
    parser.register("SYNC:HEALTH?", make_sync_health_handler(state))
    parser.register("SYNC:HOLD:DUR?", make_sync_hold_dur_handler(state))

    parser.register_setter("SYNC:HOLD:INIT", make_sync_hold_init_setter(state))
    parser.register_setter("SYNC:HOLD:REC:INIT", make_sync_hold_rec_init_setter(state))
    parser.register_setter("SYNC:SOUR:MODE", make_sync_source_mode_setter(state))