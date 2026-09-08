"""
commands/servo.py

SERVO alt sistemi: SERVo:STATe? ve SERV?

NICIN YENI BIR DOSYA:
  Bu alt sistem simulatorde hic yoktu. Gorev tanimindaki ilk komut
  listesinde de yer almiyordu, ama hem kilavuzda (§3.10) hem de
  GERCEK cihaz kayitlarinda mevcut -- ve SERVo:STATe?, cihazin
  isinma/kilitlenme surecini gozlemlemenin TEK dogrudan yolu.

SERVo:STATe? NICIN ONEMLI:
  SYNC:LOCKED? sadece "kilitli mi, degil mi" der (1/0). Ama cihaz
  aciliskan kilide TEK ADIMDA gecmez; arada gercek asamalar vardir:

      0 isinma  ->  2 kilitleniyor  ->  6 kilitli

  SYNC:LOCKED? bu ucunden ikisini ayni gorur (ikisinde de 0 doner).
  Bir izleme yazilimi "neden hala kilitlenmedi?" sorusuna ancak
  SERVo:STATe? ile cevap verebilir: cihaz henuz mi isiniyor, yoksa
  isindi da GNSS'e mi kilitlenemiyor?
"""

from gnsdo_simulator.device_state import DeviceState, current_servo_state
from gnsdo_simulator.scpi_parser import SCPIParser


def make_servo_state_handler(state: DeviceState):
    """
    SERVo:STATe? -- cihazin su anki servo durumu (kilavuz §3.10.3).

        0  Rubidyum/filtre osilator isinmasi
        1  Holdover
        2  Kilitleniyor (Rubidyum/filtre egitimi)
        5  Holdover ama halen faz kilitli
           (GNSS kaybindan sonra ~100 saniye)
        6  Kilitli, GNSS aktif

    Deger SAKLANMAZ, HESAPLANIR -- gecen sureye, holdover durumuna ve
    GNSS fix'ine bagli. Boylece SYNC:LOCKED? ile celisme ihtimali yok:
    ikisi de ayni kaynaktan okuyor.
    """

    def handler() -> str:
        return str(current_servo_state(state))

    return handler


def make_servo_handler(state: DeviceState):
    """
    SERV? -- servo dongusunun tum ayarlarinin ozeti.

    Bicim ve degerler GERCEK cihaz ciktisindan alindi
    (docs/gercek-cihaz-ciktilari.md):

        SERVO: CSAC
        LOOP: 1
        DAC GAIN: 2.000
        EFC SCALE : 0.50
        PHASE CORRECTION : 1.500000
        EFC DAMPING: 10
        FILTER LENGTH: 20
        TEMPERATURE COMPENSATION : 0
        AGING COMPENSATION : -0.000547502
        1PPS OFFSET : 0.000 ns
        TRACE PORT : RS232
        TRACE : 0
        FASTLOCK : 1
        FASTLOCK PERIOD  : 1800

    DIKKAT -- BOSLUKLAR: gercek ciktida etiketlerin bicimi tutarsiz
    ("LOOP:" bitisik ama "EFC SCALE :" ayrik, "FASTLOCK PERIOD  :"
    iki bosluklu). Bu tutarsizligi BILEREK KORUYORUZ: cikitiyi sabit
    bicimde ayristiran bir istemci, bizim "duzelttigimiz" bir bosluk
    yuzunden gercek cihazda calisip simulatorde calismayabilir.
    """

    def handler() -> str:
        loop = "1" if state.servo_loop_enabled else "0"
        lines = [
            f"SERVO: {state.servo_selected_loop}",
            f"LOOP: {loop}",
            f"DAC GAIN: {state.servo_dac_gain:.3f}",
            f"EFC SCALE : {state.servo_efc_scale:.2f}",
            f"PHASE CORRECTION : {state.servo_phase_correction:.6f}",
            f"EFC DAMPING: {state.servo_efc_damping}",
            f"FILTER LENGTH: {state.servo_filter_length}",
            f"TEMPERATURE COMPENSATION : {state.servo_temp_compensation:g}",
            f"AGING COMPENSATION : {state.servo_aging_compensation:g}",
            f"1PPS OFFSET : {state.servo_1pps_offset_ns:.3f} ns",
            f"TRACE PORT : {state.servo_trace_port}",
            f"TRACE : {state.servo_trace}",
            f"FASTLOCK : {state.servo_fastlock}",
            f"FASTLOCK PERIOD  : {state.servo_fastlock_period}",
        ]
        return "\r\n".join(lines)

    return handler


def register_servo_commands(parser: SCPIParser, state: DeviceState) -> None:
    """SERVO alt sisteminin komutlarini parser'a kaydeder."""
    parser.register("SERV:STATE?", make_servo_state_handler(state))
    parser.register("SERV?", make_servo_handler(state))

    # Kilavuzun uzun yazimlari (§3.10)
    parser.register_alias("SERVO:STATE?", "SERV:STATE?")
    parser.register_alias("SERVO:STAT?", "SERV:STATE?")
    parser.register_alias("SERVO?", "SERV?")
