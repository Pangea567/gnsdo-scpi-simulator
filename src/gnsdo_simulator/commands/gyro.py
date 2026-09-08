"""
commands/gyro.py

GYRO alt sistemi (kilavuz §3.4).

BU NE ISE YARIYOR:
  Cihazda opsiyonel bir ivmeolcer/jiroskop bulunuyor. Amaci suslu
  degil, tamamen pratik: bir osilatorun frekansi UZERINE ETKI EDEN
  G-KUVVETINE duyarlidir ("g-sensitivity"). Ucakta, aracta ya da
  titresimli bir ortamda bu etki olculebilir bir frekans hatasi
  yaratir. Cihaz ivmeyi olcup bu hatayi yazilimla telafi edebiliyor.

  Kilavuz §1.1 bunu soyle anlatiyor: "Software compensation measures
  residual aging, thermal, and g-sensitivity errors of the oscillators,
  and applies electronic compensation to reduce these residual errors."

BURADA SADECE SORGULARI UYGULUYORUZ:
  Kilavuzda kalibrasyon ayarlari da var (GYRO:CAL, GYRO:SENS gibi)
  ama onlar cihazi AYARLAYAN komutlar. Simulatorun amaci bir izleme /
  test uygulamasina cevap vermek oldugu icin oncelik SORGULARDA.

CIKTI BICIMI:
  GERCEK cihaz kaydindan alindi (docs/gercek-cihaz-ciktilari.md):

      MODE : 0
      TRACE: 0
      CALIBRATION : Offset: 0.000, 0.000, 0.000, Gain: 1.0000, 1.0000, 1.0000
      G-SENSITIVITY : X 0.000 mHz/g, Y 0.000 mHz/g, Z: 0.000 mHz/g
      GLOAD : -0.067,-0.045,-1.063
      PORT : RS232

  DIKKAT -- bicim tutarsizliklari BILEREK korunuyor: "MODE :" ayrik
  ama "TRACE:" bitisik; G-SENSITIVITY satirinda X ve Y'den sonra iki
  nokta yokken Z'den sonra var ("Z: 0.000"). Gercek cihaz boyle
  yaziyor; "duzeltmek" sabit bicimde ayristiran bir istemciyi bozar.
"""

from gnsdo_simulator.device_state import DeviceState, measured_gload
from gnsdo_simulator.scpi_parser import SCPIParser


def make_gyro_gload_handler(state: DeviceState):
    """
    GYRO:GLOAD? -- uc eksendeki g-kuvveti.

    Gercek cihaz -0.067,-0.045,-1.063 okumustu: Z ekseninde yaklasik
    -1 g, yani cihaz duz duruyor ve YERCEKIMINI olcuyor. X/Y'deki
    kucuk degerler hafif egiklik.
    """

    def handler() -> str:
        x, y, z = measured_gload(state)
        return f"{x:.3f},{y:.3f},{z:.3f}"

    return handler


def make_gyro_port_handler(state: DeviceState):
    """GYRO:PORT? -- jiroskobun bagli oldugu seri arayuz."""

    def handler() -> str:
        return state.gyro_port

    return handler


def make_gyro_handler(state: DeviceState):
    """GYRO? -- alt sistemin tum durumunun ozeti."""

    def handler() -> str:
        ox, oy, oz = state.gyro_cal_offset
        gx, gy, gz = state.gyro_cal_gain
        sx, sy, sz = state.gyro_sensitivity_mhz_per_g

        lines = [
            f"MODE : {state.gyro_mode}",
            f"TRACE: {state.gyro_trace}",
            (
                f"CALIBRATION : Offset: {ox:.3f}, {oy:.3f}, {oz:.3f}, "
                f"Gain: {gx:.4f}, {gy:.4f}, {gz:.4f}"
            ),
            (
                f"G-SENSITIVITY : X {sx:.3f} mHz/g, Y {sy:.3f} mHz/g, "
                f"Z: {sz:.3f} mHz/g"
            ),
            f"GLOAD : {make_gyro_gload_handler(state)()}",
            f"PORT : {state.gyro_port}",
        ]
        return "\r\n".join(lines)

    return handler


def register_gyro_commands(parser: SCPIParser, state: DeviceState) -> None:
    """GYRO alt sisteminin SORGU komutlarini parser'a kaydeder."""
    parser.register("GYRO?", make_gyro_handler(state))
    parser.register("GYRO:GLOAD?", make_gyro_gload_handler(state))
    parser.register("GYRO:PORT?", make_gyro_port_handler(state))
