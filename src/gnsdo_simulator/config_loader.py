"""
config_loader.py

Bir YAML config dosyasini okuyup, icindeki degerleri bir DeviceState
nesnesine uygular.

Neden ayri bir dosya?
  DeviceState'in kendisi "hangi alanlar var" bilgisini tasir, ama
  "bu alanlari bir YAML dosyasindan nasil dolduracagimi" bilmesi
  onun isi degil -- o sadece bir veri kutusu. Config okuma/uygulama
  mantigini ayri tutmak, ikisini de daha basit ve anlasilir kilar.

YAML dosyasi soyle bir yapida (bkz. configs/normal.yaml):
    device:
      serial_number: SIM000001
    gps:
      visible: 12
      tracking: 8
    sync:
      locked: true
      holdover: false
    measure:
      temperature: 42.5
      voltage: 12.1
      current: 0.42

Onemli tasarim karari: config dosyasinda bir alan YAZILMAMISSA,
DeviceState'in kendi Python varsayilanini (dataclass'taki "= 42.5"
gibi degerleri) OLDUGU GIBI birakiyoruz -- yani config dosyasi
"kismi" olabilir, her seyi tekrar yazmak zorunda degilsin.
"""

from datetime import datetime
from pathlib import Path

import yaml

from gnsdo_simulator.device_state import DeviceState


def load_scenario_config(path: str | Path) -> dict:
    """
    Bir YAML dosyasini okuyup Python dict'ine cevirir.

    yaml.safe_load(): dosyanin icerigini guvenli bir sekilde
    (kod calistirmadan, sadece veri olarak) Python veri yapilarina
    (dict, list, str, int, bool...) cevirir.
    """
    file_path = Path(path)
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


def apply_config_to_state(state: DeviceState, config: dict) -> None:
    """
    config dict'indeki degerleri, verilen DeviceState nesnesinin
    UZERINE yazar (in-place degistirir, yeni bir state DONMEZ).

    .get("anahtar", {}) kullanmamizin sebebi: eger config
    dosyasinda o bolum (ornegin "sync:") hic yoksa, hata vermek
    yerine bos bir dict ({}) varsayip o bolumdeki hicbir seyi
    degistirmemek.
    """
    device = config.get("device", {})
    if "serial_number" in device:
        state.serial_number = device["serial_number"]
    if "firmware_version" in device:
        state.firmware_version = device["firmware_version"]

    gps = config.get("gps", {})
    if "visible" in gps:
        state.gnss_satellites_visible = gps["visible"]
    if "tracking" in gps:
        state.gnss_satellites_tracking = gps["tracking"]

    sync = config.get("sync", {})
    if "locked" in sync:
        state.sync_locked = sync["locked"]
    if "holdover" in sync:
        state.holdover = sync["holdover"]
        # Config'ten "holdover: true" ile basliyorsak, holdover'in
        # NE ZAMAN basladigini bilmemiz lazim (SYNC:HOLD:DUR? icin).
        # Config dosyasinda bir zaman belirtilmedigi icin, en
        # mantikli varsayim: "simdi baslamis gibi say" (program
        # baslama ani).
        if sync["holdover"]:
            state.holdover_started_at = datetime.now()
        else:
            state.holdover_started_at = None

    measure = config.get("measure", {})
    if "temperature" in measure:
        state.temperature_celsius = measure["temperature"]
    if "voltage" in measure:
        state.voltage = measure["voltage"]
    if "current" in measure:
        state.current = measure["current"]

    # "diag" bolumu -- DIAG?/SYST:STAT? icin kullanilan alanlar.
    # lifetime_hours artik BASLANGIC (baseline) degeri -- gercekte
    # goruntulenen Lifetime, buna simulator'in calisma suresi
    # EKLENEREK hesaplanir (bkz. commands/diagnostic.py).
    # "hardware-error" senaryosu icin fault=true kullanacagiz.
    diag = config.get("diag", {})
    if "lifetime_hours" in diag:
        state.diag_lifetime_base_hours = diag["lifetime_hours"]
    if "fault" in diag:
        state.hardware_fault = diag["fault"]
    if "fault_message" in diag:
        state.fault_message = diag["fault_message"]

    # "warmup" bolumu -- "warming-up" senaryosu icin. true ise,
    # cihaz gercek cihazin kilavuzundaki gibi (2 dakika) bir sure
    # sonra KENDILIGINDEN kilitlenecek (bkz. device_state.is_locked()).
    warmup = config.get("warmup", {})
    if warmup.get("active"):
        state.warmup_started_at = datetime.now()


def load_scenario(scenario_name: str, configs_dir: str | Path = "configs") -> DeviceState:
    """
    Ust duzey, kolay kullanilir fonksiyon: senaryo ismini
    ("normal", "gnss-lost", "holdover" gibi) alir, ilgili
    "configs/<isim>.yaml" dosyasini bulur, okur, ve o degerlerle
    doldurulmus TAZE bir DeviceState nesnesi doner.

    main.py sadece bunu cagiracak:
        device_state = load_scenario(args.scenario)
    """
    config_path = Path(configs_dir) / f"{scenario_name}.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Senaryo config dosyasi bulunamadi: {config_path}. "
            f"Desteklenen senaryolar icin configs/ klasorune bak."
        )

    state = DeviceState()  # once Python varsayilanlariyla bos bir state
    config = load_scenario_config(config_path)
    apply_config_to_state(state, config)  # sonra config'teki degerleri uzerine yaz
    return state