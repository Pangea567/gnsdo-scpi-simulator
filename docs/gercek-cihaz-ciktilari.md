# Gercek Cihaz Ciktilari (ham kayit)

Bu dosya, **gercek Low Noise Rubidium GNSDO cihazina** seri port uzerinden
gonderilen komutlarin ve alinan cevaplarin ham kaydidir.

- **Kaynak**: `kaynaklar/gercek-cihaz-ciktilari.docx` (bu dosyanin orijinali)
- **Cihaz**: LN Rb GPSDO (PRE), Serial 122301668, Firmware Rev 1.17
- **Kayit tarihi**: 2 Eylul 2026 (ciktilardaki UTC damgalarindan)

## Nicin repoda duruyor?

Simulatorun davranis kararlarinin buyuk kismi DOGRUDAN bu kayitlara
dayaniyor. Kilavuz cihazin ne YAPMASI gerektigini anlatir; bu kayitlar
GERCEKTE ne yaptigini gosterir -- ve ikisi her zaman ortusmuyor.

Bu belgeden cikan ve modeli degistiren bulgular `tasarim-kararlari.md`
icindeki **5.7 Gercek Cihaz Kayitlariyla Hizalama Turu** bolumunde, her
biri gerekcesiyle listelenmistir. Ozetle:

| Bulgu | Etkisi |
|---|---|
| TINT arti/eksi salaniyor (`-7.873E-09` ... `1.133E-08`) | Kilitli TINT modeli bastan yazildi (D-4) |
| `MEAS:CURR?` -> `51.3210` | Komut akim degil SICAKLIK donduruyor (D-5) |
| PCB ve CSAC sicakliklari hep +1.32 C farkla | Ikisi bagimsiz degil, turetilmis (D-6) |
| `-82 -> -0.410000%` | EFC Absolute/Relative baginti = x200 (D-7) |
| `Command Error` | Bilinmeyen komut cevabi (D-8) |
| `CSAC Temperature: 54.10` | Sabit ondalik bicimlendirme (D-9) |

## Kayitlardaki notlar

Metin icindeki Turkce sorular ve yorumlar, kaydi alan kisiye aittir ve
BILEREK korunmustur -- cunku cihazin sasirtici davranislarina isaret
ediyorlar. Ornegin `GPS:SAT:TRAC:COUN?` (20) degerinin
`GPS:SAT:VIS:COUN?` (19) degerinden buyuk cikmasi K-10'da ele alindi.

## Gizlilik notu

Kayitlar cihazin **gercek konum bilgisini** icerir (enlem/boylam, ECEF
koordinatlari). Depo sahibi bunlarin repoda yer almasini onaylamistir.

---

```text
REAL COMMAND OUTPUTS 


*IDN? - HELP? - SYST:STAT?


*IDN?

Jackson Labs, LN Rb GPSDO (PRE), Firmware Rev 1.17


HELP?

*IDN?
SERVo?
SERVo:DACGain    <float>[0.001, 10000]
     :MODE       <SLOW|MEDium|FAST|AUTO>
     :STATE?
     :EFCScale   <float>[0.0, 500.0]
     :EFCDamping <int>  [2, 4000]
     :FILTerlength <int>  [2, 20]
     :TEMPCOmpensation  <float> [-4000.0, 4000.0]
     :AGINGcompensation <float> [-10.0, 10.0]
     :PHASECOrrection   <float> [-500.0, 500.0]
     :1PPSoffset        <int> ns
     :QUIet   <ON|OFF>
     :TRACe   <int>  [0,255]
     :TRACe:PORT <RS232|USB>
     :LOOP    <ON|OFF>
     :COARSedac [0,255]
     :SELect <CSAC:FILTer>
SYNChronization?
SYNChronization:SOURce:MODE <GPS|EXTernal|AUTO>
SYNChronization:SOURce:STATE?
SYNChronization:HOLDover:DURation?
               :HOLDover:STATe?
               :HOLDover:INITiate
               :HOLDover:RECovery:INITiate
               :TINTerval?
               :TINTerval:CSAC?
               :TINTerval:FILTer?
               :TINTerval:THReshold <int> [50,2000]
               :IMMEdiate
               :FEEstimate?
               :LOCKed?
               :OUTput:FILTer  <ON|OFF>
               :OUTput:1PPS:RESET  <ON|OFF>
               :OUTput:1PPS:DOMAIN <CSAC|FILTer>
               :HEAlth?
MAC?
MAC:RS232?
   :STeer?
   :STATus?
   :MODE?
   :DDScenter?
   :TECcontrol?
   :TCXO?
   :SIGnal?
   :HEATpackage?
   :TEMPerature?
   :SN?
   :FWrev?
   :LIFEtime?
   :STeer:LATch  ONCE
   :PASSthrough <csac_cmd>
DIAGnostic?
DIAGnostic:ROSCillator:EFControl:RELative?
                                 RELative:CSAC?
                                 RELative:FILTer?
                                 ABSolute?
                                 ABSolute:CSAC?
                                 ABSolute:FILTer?
          :LIFetime:COUNt?
GPS?
GPS:RESET   ONCE
GPS:REFerence:ADELay  <float> <s|ns> [-32767ns,32767ns]
GPS:REFerence:PULse:SAWtooth?
GPS:TMODe   <ON|OFF|RSTSURV>
GPS:SURVey  ONCE
GPS:SURVey:STATus?
          :DURation  <int in sec>
          :VARiance  <int>
GPS:HOLD:POSition <int,int,int>
GPS:DYNAMic:MODE  <int>  [0,8]
GPS:DYNAMic:STATe?
GPS:PORT     <RS232|USB>
GPS:GPRMC    <int>  [0,255]
GPS:GPGGA    <int>  [0,255]
GPS:GGASTat  <int>  [0,255]
GPS:XYZSPeed <int>  [0,255]
GPS:GPZDA    <int>  [0,255]
GPS:PASHR    <int>  [0,255]
GPS:GPGSV    <int>  [0,255]
GPS:SATellite:TRAcking:COUNT?
             :VISible:COUNT?
GPS:POSition?
GPS:POSition:ECEF?
GPS:JAMlevel?
GPS:FWver?
GPS:INITial:DATE <yyyy,mm,dd>
           :TIME <hour,min,sec>
YSTem:SELect  [GPS | SBAS | QZSS | GAL | BD ^ GLO]
GYRO?
GYRO:MODE        <ON|OFF>
GYRO:TRACE       <int>  [0,255]
GYRO:CALibrate   <float,float,float,float,float,float>
GYRO:CALibrate:COMPute
GYRO:CALibrate:RESET
GYRO:SENSitivity <float,float,float>
GYRO:GLOAD?
GYRO:PORT        <RS232|USB>
MEASure?
MEASure:TEMPerature?
       :VOLTage?
       :CURRent?
       :POWersupply?
PTIMe?
PTIMe:DATE?
PTIMe:TIME?
PTIMe:TIME:STRing?
PTIMe:TINTerval?
PTIMe:OUTput <ON|OFF>
PTIMe:LEAPsecond?
PTIMe:LEAPsecond:PENDing?
                :ACCumulated?
                :DATE?
                :DURation?
SYSTem:COMMunicate:SERial:ECHO   <ON|OFF>
                         :PROmpt <ON|OFF>
                         :BAUD   <9600 | 19200 | 38400 | 57600 | 115200>
                         :SERVo  <CSAC | FILTer>
SYSTem:COMMunicate:USB:BAUD      <9600 | 19200 | 38400 | 57600 | 115200>
                      :SERVo  <CSAC | FILTer>
SYSTem:STATus?
SYSTem:ID?
SYSTem:ID:SN?
SYSTem:ID:HWrev?
SYSTem:LCD:CONTrast <float> [0,1.0]
SYSTem:LCD:PAGE     <int> [0,9]
SYSTem:FACToryreset ONCE
HELP?


SYST:STAT?

LN Rb GPSDO (PRE)  Serial Number : 122301668    Hw version : 1.01.00
AQUISITION ................................................
Tracking:14        Not Tracking: 2             
PRN  El  Az   SS   PRN  El  Az                 
  1  87 250   23    19   4 329                
  2  65 159   31    308   1  40                
  4  30 220   30                              
  8  10 194   10                              
 17  25 303   16                              
 28  34  78   38                              
 31  34 115   47                              
 32  21  47   41                              
 40  38 142   32                              
 41  18 116   41                              
 307  49  53   33                              
 326  60 120   30                              
 329  68 183   24                              
 333  63 320   19                              
                                              
LAT   N 40:47:13.689             LON   E 29:27:12.366
HGT   147.60 m (MSL)             UTC    7:06:46   2 Sep 2026    
HEALTH MONITOR................................................
GPS Receiver Status: 3D Fix             GPSDO Status : Locked
1PPS SOURCE MODE  : GPS                 1PPS SOURCE STATE  : GPS

SYST:STAT?

LN Rb GPSDO (PRE)  Serial Number : 122301668    Hw version : 1.01.00
AQUISITION ................................................
Tracking:14        Not Tracking: 6             
PRN  El  Az   SS   PRN  El  Az                 
  1  83 178   30     8   5 192                
  2  58 161   33     9   4 228                
  3  58 312   19    19   8 325                
  4  36 223   25    312  15 312                
 17  27 296   15    313   5 130                
 28  33  69   40    319  26 213                
 31  38 107   46                              
 32  15  48   31                              
 40  38 142   32                              
 41  18 116   41                              
 307  45  50   41                              
 326  55 127   37                              
 329  74 181   26                              
 333  69 319   24                              
                                              
LAT   N 40:47:13.813             LON   E 29:27:13.291
HGT   192.10 m (MSL)             UTC    7:21:20   2 Sep 2026    
HEALTH MONITOR................................................
GPS Receiver Status: 3D Fix             GPSDO Status : Locked
1PPS SOURCE MODE  : GPS                 1PPS SOURCE STATE  : GPS


GPS?


GPS?

GNSS: GPS SBAS GAL 
ANTENNA DELAY:2.5e-08
PULSE SAWTOOTH:-6.0
TRACKED SATS :13
VISIBLE SATS :21
ACTUAL POSITION:
N,4047.2368
E,2927.2267
190.00 m
0.10 Knots
0.00 Degrees
GPS Receiver Status: 3D Fix
DYNAMIC MODE:AUTOMATIC(8)
DYNAMIC STATE:STATIONARY(1)
SURVEY MIN DURATION:3600
SURVEY VARIANCE LIMIT:150000
SURVEY STATUS:ACTIVE
Duration : 2580, ECEF 421116328,237806312,414469764, 3D variance 274822336
TIMING MODE:RSTSURV
HOLD POSITION:-267998828,-430158341,385929826
JAMMING LEVEL:5
FIRMWARE VERSION: 3.01


GPS?

GNSS: GPS SBAS GAL 
ANTENNA DELAY:2.5e-08
PULSE SAWTOOTH:-3.1
TRACKED SATS :13
VISIBLE SATS :20
ACTUAL POSITION:
N,4047.2281
E,2927.2189
182.90 m
0.09 Knots
0.00 Degrees
GPS Receiver Status: 3D Fix
DYNAMIC MODE:AUTOMATIC(8)
DYNAMIC STATE:STATIONARY(1)
SURVEY MIN DURATION:3600
SURVEY VARIANCE LIMIT:150000
SURVEY STATUS:ACTIVE
Duration : 1270, ECEF 421116113,237805586,414468927, 3D variance 266913968
TIMING MODE:RSTSURV
HOLD POSITION:-267998828,-430158341,385929826
JAMMING LEVEL:8
FIRMWARE VERSION: 3.01

GPS?

GNSS: GPS SBAS GAL 
ANTENNA DELAY:2.5e-08
PULSE SAWTOOTH:-5.4
TRACKED SATS :14
VISIBLE SATS :20
ACTUAL POSITION:
N,4047.2319
E,2927.2278
187.30 m
0.03 Knots
0.00 Degrees
GPS Receiver Status: 3D Fix
DYNAMIC MODE:AUTOMATIC(8)
DYNAMIC STATE:STATIONARY(1)
SURVEY MIN DURATION:3600
SURVEY VARIANCE LIMIT:150000
SURVEY STATUS:ACTIVE
Duration : 2798, ECEF 421116317,237806519,414469904, 3D variance 276520608
TIMING MODE:RSTSURV
HOLD POSITION:-267998828,-430158341,385929826
JAMMING LEVEL:11
FIRMWARE VERSION: 3.01


GPS?
(BURDA ANTENDEN SİNYAL ALAMIYO)
GNSS: GPS SBAS GAL 
ANTENNA DELAY:2.5e-08
PULSE SAWTOOTH:0.0
TRACKED SATS :0
VISIBLE SATS :0
ACTUAL POSITION:
N,   0.0000
E,   0.0000
0.00 m
0.00 Knots
0.00 Degrees
GPS Receiver Status: No Fix
DYNAMIC MODE:AUTOMATIC(8)
DYNAMIC STATE:STATIONARY(1)
SURVEY MIN DURATION:3600
SURVEY VARIANCE LIMIT:150000
SURVEY STATUS:ACTIVE
Duration : 14, ECEF 0,0,0, 3D variance 4294967295
TIMING MODE:RSTSURV
HOLD POSITION:-267998828,-430158341,385929826
JAMMING LEVEL:4
FIRMWARE VERSION: 3.01


GPS:SAT:TRAC:COUN?

20

GPS:SAT:VIS:COUN?

19
ŞUAN BİDAHA DENEDİM COMMAND ERROR VERİYO ???? SIKINTI

Nasıl böyle oluyo, niye fark var ???


PTIME?

PTIME?

DATE :2026,9,2
TIME :7:15:14
TINTerval :9.063E-09
OUTput :0
LEAPSECOND :18

PTIME?

DATE :2026,9,2
TIME :7:44:23
TINTerval :2.672E-09
OUTput :0
LEAPSECOND :18


PTIME:DATE?

2026,9,2

PTIME:TIME?

7,46,13


PTIME:TIME:STRING?


7:46:33


SYNC?


SYNC?

1PPS SOURCE MODE  : GPS     
1PPS SOURCE STATE : GPS
1PPS on RESET : OFF
1PPS DOMAIN : CSAC
1PPS LOCK STATUS  : 1
HOLDOVER STATE: NONE
LAST HOLDOVER DURATION : 191,0
FREQ ERROR ESTIMATE : 1.31E-11
TIME INTERVAL DIFFERENCE : 1.133E-08
TIME INTERVAL THRESHOLD : 220
PHASE NOISE FILTER : ON  
HEALTH STATUS : 0x0

SYNC? 

1PPS SOURCE MODE  : GPS     
1PPS SOURCE STATE : GPS
1PPS on RESET : OFF
1PPS DOMAIN : CSAC
1PPS LOCK STATUS  : 1
HOLDOVER STATE: NONE
LAST HOLDOVER DURATION : 191,0
FREQ ERROR ESTIMATE : 2.49E-11
TIME INTERVAL DIFFERENCE : -7.873E-09
TIME INTERVAL THRESHOLD : 220
PHASE NOISE FILTER : ON  
HEALTH STATUS : 0x0

SYNC?

1PPS SOURCE MODE  : GPS     
1PPS SOURCE STATE : GPS
1PPS on RESET : OFF
1PPS DOMAIN : CSAC
1PPS LOCK STATUS  : 1
HOLDOVER STATE: NONE
LAST HOLDOVER DURATION : 191,0
FREQ ERROR ESTIMATE : 1.59E-11
TIME INTERVAL DIFFERENCE : -1.179E-08
TIME INTERVAL THRESHOLD : 220
PHASE NOISE FILTER : ON  
HEALTH STATUS : 0x0

SYNC:LOCKED?

1

SYNC:TINT?

6.763E-08

SYNC:HEALTH?

0x1000


SYNC:HOLD:DUR?

150,0


SYNC:HOLD:INIT
SYNC:HOLD:REC:INIT
SYNC:SOUR:MODE <m>

bunlar çok lazım değilmiş 


DIAG? - MEAS? - CSAC?


DIAG?

EFControl Relative: -0.410000%
EFControl Absolute: -82.000000
Lifetime : +0

DIAG?

EFControl Relative: -0.440000%
EFControl Absolute: -88.000000
Lifetime : +0

diag?

EFControl Relative: -0.640000%
EFControl Absolute: -128.000000
Lifetime : +0

DIAG?

EFControl Relative: -0.105000%
EFControl Absolute: -21.000000
Lifetime : +0


MEAS? 

PCB Temperature: 46.5688
CSAC Temperature: 47.83
TCXO Voltage: 1.672
Power Supply Voltage: 11.71	


MEAS? 

PCB Temperature: 52.7762
CSAC Temperature: 54.10
TCXO Voltage: 1.659
Power Supply Voltage: 11.74

MEAS?

PCB Temperature: 52.8652
CSAC Temperature: 54.17
TCXO Voltage: 1.659
Power Supply Voltage: 11.73

MEAS:TEMP?

51.1479

MEAS:CURR?

51.3210

MEAS:VOLT?

1.662


CSAC?

RS232: OK
STEER: -71.000
STATUS: 0
MODE: 0x0000
TEC CONTROL: 56.22
DDS CENTER: 0.00
TCXO VOLTAGE: 1.658
DC SIGNAL LEVEL: 1.00
HEAT PACKAGE: 2730.00
TEMPERATURE: 54.36
SN: 2209MX04906
FIRMWARE REV: V1.0.23
LIFETIME: 11247

CSAC?

PCB Temperature: 49.7419
CSAC Temperature: 51.13
TCXO Voltage: 1.665
Power Supply Voltage: 11.72
Command Error
RS232: OK
STEER: -15.000
STATUS: 0
MODE: 0x0000
TEC CONTROL: 56.24
DDS CENTER: 0.00
TCXO VOLTAGE: 1.665
DC SIGNAL LEVEL: 1.00
HEAT PACKAGE: 3000.00
TEMPERATURE: 51.39
SN: 2209MX04906
FIRMWARE REV: V1.0.23
LIFETIME: 11248


CSAC:STATUS?

0

CSAC:TEMP?

54.65

CSAC:SN?

2209MX04906


EXTRA COMMANDS (NOT İMPLEMENTED YET, MAYBE WE CAN I WİLL ASK THIS)

MAC?

RS232: OK
STEER: -97.000
STATUS: 0
MODE: 0x0000
TEC CONTROL: 56.29
DDS CENTER: 0.00
TCXO VOLTAGE: 1.682
DC SIGNAL LEVEL: 1.00
HEAT PACKAGE: 3655.00
TEMPERATURE: 43.74
SN: 2209MX04906
FIRMWARE REV: V1.0.23
LIFETIME: 11248


GYRO? 

MODE : 0
TRACE: 0
CALIBRATION : Offset: 0.000, 0.000, 0.000, Gain: 1.0000, 1.0000, 1.0000
G-SENSITIVITY : X 0.000 mHz/g, Y 0.000 mHz/g, Z: 0.000 mHz/g
GLOAD : -0.067,-0.045,-1.063
PORT : RS232


GPS:POSITION?

N,4047.2327
E,2927.2257
194.70 m
0.07 Knots
0.00 Degrees

SERV?

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
```
