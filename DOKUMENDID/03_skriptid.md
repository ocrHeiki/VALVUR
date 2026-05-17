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
#   |   FAILI NIMI:  03_skriptid.md                                       |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   VALVUR-i analüüsimoodulite detailne kirjeldus.       |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################

# VALVUR Skriptide Ülevaade

VALVUR koosneb etapiviisilistest skriptidest, mida juhib `valvurMASTER.py`. Allpool on toodud skriptide loogiline tööjärjekord.

### 00_terviklus_kontroll.py
Arvutab algallika logide (EVTX, syslog) SHA-256 räsid enne analüüsi alustamist. Tagab andmete tervikluse tõendamise.

### 01_konverteering_evtx_csv.py
Teisendab Windowsi .evtx logid CSV formaati. Toetab lukus failide automaatset kopeerimist ja reaalajas süsteemi skaneerimist.

### 02_linux_logid_csv.py
Teisendab Linuxi syslogid ühtsesse normaliseeritud CSV formaati, lisades sündmuste ID-d (nt 4624/4625).

### 03_turvafiltreering.py
Eraldab logidest kriitilised turvasündmused (GPO muudatused, privileegide eskaleerimine, ebaharilikud sisselogimised).

### 04_otsing_marksonade_jargi.py
Otsib logidest ründetööriistade jälgi, seostades leitud märksõnad **MITRE ATT&CK** taktikate ja **CVE** koodidega. Kasutab sarnasuse kontrolli (Fuzzy Matching).

### 05_powershell_dekodeerimine.py
Teostab süvaanalüüsi, dekodeerides obfuskeeritud PowerShell koodi (Base64 ja XOR) ning tuvastades peidetud ründeindikaatoreid.

### 06_kahtlased_failid.py
Teostab süsteemi reaalajas kontrolli (Live Scan) ajutistes kaustades, otsides peidetud faile, Cron-töid ja brauseri tegevuse jälgi.

### 07_vorgu_skaneerimine.py
Kaardistab võrgu varad ja avatud teenused (nmap), aidates tuvastada ebaharilikke kuulatavaid porte või sisevõrgu seadmeid.

### 08_kasutajate_nimekiri.py
Koostab ülevaate süsteemi kasutajakontodest, tuvastades peidetud root-õigustega kontod (UID 0) ja unikaalsed logidest leitud tunnused.

### 09_turvaaudit.py
Kontrollib süsteemi vastavust E-ITS standardile ja **NIST CSF 2.0** raamistikule. Genereerib samm-sammulise paranduskava (Roadmap).

### 10_threat_intel.py
Võrdleb leitud IP-aadresside ja failide mainet väliste IoC andmebaasidega (valmidus API integratsiooniks).

### 11_malu_analuus.py
Liides Volatility 3 tööriistale, mis võimaldab analüüsida mälutõmmiseid (.raw, .mem), tuvastamaks mälus peituvat pahavara (malfind, psscan).

### 12_linux_syvaanaluus.py
Linuxi-spetsiifiline süvakontroll: tuvastab logide manipuleerimist (Log Tampering) ja teostab SSH sisselogimiste normaliseeritud analüüsi.

### 13_koond_ajajoon.py
Genereerib ühtse kronoloogilise ajajoone (Unified Timeline) kõikidest logiallikatest, visualiseerides ründaja tegevust sekundilise täpsusega.

### 14_genereeriRAPORT.py
Koostab lõpliku koondraporti, mis sisaldab **Executive Summary**-t, NIST CSF maatriksit ja peamisi turvaleide.

### 15_tehniline_raport_pdf.py
Genereerib visuaalselt korrektse tehnilise ülevaate ja raporti PDF-formaadis.

---

### valvurMASTER.py
Süsteemi peamootor, mis juhib kogu analüüsiahelat. Sisaldab admin-õiguste kontrolli, metoodilist "klooni" märget ja robustset veatöötlust.
