```
###############################################################################
#                                                                             #
#   █████   █████           ████                                              #
#  ▒▒███   ▒▒███           ▒▒███                                              #
#   ▒███    ▒███   ██████   ▒███  █████ █████ █████ ████ ████████             #
#   ▒███    ▒███  ▒▒▒▒▒███  ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███            #
#   ▒▒███   ███    ███████  ▒███  ▒███  ▒███  ▒███ ▒███  ▒███ ▒▒▒             #
#    ▒▒▒█████▒    ███▒▒███  ▒███  ▒▒███ ███   ▒███ ▒███  ▒███                 #
#      ▒▒███     ▒▒████████ █████  ▒▒█████    ▒▒████████ █████                #
#       ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒    ▒▒▒▒▒      ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                 #
#                                                                             #
#   =======================================================================   #
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  README.md                                            |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Projekti koondülevaade ja kiirkäivitusjuhend.        |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
```
# VALVUR - Intsidendi süvaanalüüsi ja turvaauditi platvorm

**VALVUR** on professionaalne ja automatiseeritud tööriistakomplekt Windowsi ja
Linuxi operatsioonisüsteemide turvaauditiks ja küberintsidentide lahendamiseks.
Projekt järgib tööstusstandardeid nagu **NIST CSF 2.0** ja **MITRE ATT&CK**.

## Kiirkäivitus (Remote Launch)

```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py)"
```

## Strateegiline raamistik: NIST CSF 2.0

- **IDENTIFY**: Varade ja kasutajate kaardistus (FAAS 4: 31, 32)
- **PROTECT**: E-ITS audit ja turvapoliitika kontroll (FAAS 4: 32)
- **DETECT**: MITRE ATT&CK põhine logi- ja failianalüüs (FAAS 2/3: 11, 12, 21, 22)
- **RESPOND**: Automatiseeritud raporteerimine (FAAS 5: 52, 53)
- **RECOVER**: Kronoloogiline ajajoon süsteemi taastamiseks (FAAS 5: 51)

## Faaside ülevaade (Phase Architecture)

### FAAS 1: Algkäivitus ja Andmehõive (00-09)
- `01_terviklus.py` — Algfailide SHA-256 räside arvutamine (forensiliselt korrektne)
- `02_windows_evtx.py` — Windows .evtx logide parsimine CSV-ks (`raw_eksport_win_*`)
- `03_linux_logid.py` — Linuxi syslogide struktureerimine (`raw_eksport_linux_*`)

### FAAS 2: Filtreerimine ja Tuvastus (10-19)
- `11_turvafiltreering.py` — Müra eemaldamine, kriitilised Event ID-d → `11_tulemus_turvafiltreering.csv`
- `12_marksonade_otsing.py` — MITRE ATT&CK märksõnade otsing + Fuzzy Matching → `12_tulemus_kahtlased_marksonad.csv`

### FAAS 3: Süvaanalüüs ja Deobfuskatsioon (20-29)
- `21_powershell_decode.py` — Base64/XOR/Char obfuskatsiooni lahtiharutamine
- `22_kahtlased_failid.py` — Temp-/tmp-kaustade audit ja anomaalsete failide jaht
- `23_linux_syvaanaluus.py` — SUID failid, SSH logid, logide terviklus
- `24_malu_analuus.py` — Volatility 3 liides mälutõmmiste analüüsiks

### FAAS 4: Välisluure ja Kontekst (30-39)
- `31_vorgu_skaneerimine.py` — Aktiivsete võrguühenduste ja avatud portide kaardistamine (Nmap)
- `32_kasutajate_audit.py` — Kasutajakontode tuvastus + E-ITS turvaaudit (konsolideeritud)
- `33_threat_intel_osint.py` — OSINT & Profiler: AbuseIPDB, VirusTotal, MalwareBazaar, LeakCheck

### FAAS 5: Süntees ja Raporteerimine (50-59)
- `51_koond_ajajoon.py` — Unified Timeline kõikidest `raw_eksport_*` logiallikatest
- `52_genereeri_raport.py` — Koondraport (kokkuvõte kõigist faasidest)
- `53_tehniline_raport_pdf.py` — Lõppraporti trükk PDF-formaadis juhtkonnale

## Struktuur

```
VALVUR/
├── launch_VALVUR.py         # Süsteemi alglaadija (kloorib repo, seab venv, käivitab)
├── SKRIPTID/                # Analüüsimootor (5 faasi)
│   ├── valvurMASTER.py      # Peakontroll ja töövoo orkestraator
│   ├── utils.py             # Ühised funktsioonid (logimine, veatöötlus, kaustad)
│   ├── 01_terviklus.py ...  # FAAS 1-5 skriptid
│   └── tests/               # Unit testid
├── DOKUMENDID/              # Metoodilised juhendid ja strateegiad
└── TULEMUSED/               # Analüüsitulemused (hostname-põhised alamkaustad)
```

## Metoodiline märkus

Analüüs teostatakse süsteemi kloonil vastavalt **ISO 27037** standardile.
