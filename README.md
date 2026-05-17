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
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
```

# 🛡️ VALVUR - Intsidendi Süvaanalüüsi ja Taktikalise Küberluure Platvorm

**VALVUR** on Heiki Rebase loodud professionaalne ja automatiseeritud tööriistakomplekt küberintsidentide lahendamiseks, süsteemide forensiliseks uurimiseks ning turvaauditiks. Süsteem pakub ühtset, ristplatvormilist analüüsiraamistikku, mis on optimeeritud töötama nii **Windowsi** kui ka **Linuxi** (tulevikus ka **macOS**) keskkondades.

Süsteemi unikaalsus seisneb selle **"andmetasemel ühilduvuses" (Feed-Ready Architecture)** ning sisseehitatud hübriidses **OSINT-vastuluure mootoris**, mis seob masinasisesed leidud globaalsete ohuindikaatoritega.

---

## 🎯 Eesmärk ja Missioon
**VALVUR-i peamine eesmärk on võimaldada turvaanalüütikul või administraatoril vaid ühe ainsa käsurea abil tuvastada operatsioonisüsteemist olenemata, millise ründega on tegu, mis meetoditega see läbi viidi ning kes (või mis asukohast/rahvusest) on ründaja.**

Projekt koondab keerulise ja aeganõudva forensilise uurimistöö ühtseks, faasipõhiseks töölooks. VALVUR järgib **NIST CSF 2.0** raamistikku, **MITRE ATT&CK** taksnoomiat ja **ISO 27037** digitaalkriminalistika standardeid, tagades tõendite tervikluse ja analüüsi kvaliteedi nii domeenikontrollerite kui ka veebiserverite puhul.

**Autor:** Heiki Rebane  
**Versioon:** 2.0 (Eksamiprojekt 2026 – *Faasipõhine Arhitektuur*)

---

## 🚀 Kiirkäivitus (Cross-Platform Remote Launch)
VALVUR on disainitud olema täielikult autonoomne ja platvormist sõltumatu. Süsteem tuvastab automaatselt operatsioonisüsteemi, loob isoleeritud virtuaalkeskkonna (`venv`) ja paigaldab vajalikud moodulid, et tagada analüüsi puhtus ja vältida uuritava süsteemi saastamist.

Käivitamiseks sisesta terminali (toimib nii PowerShellis kui Bashis):
```bash
python3 -c "$(curl -fsSL [https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py](https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py))"

📂 Projekti Struktuur (Süsteemne Loogika)

Mootor on jagatud viieks funktsionaalseks intsidendihalduse faasiks. See tagab koodi skaleeritavuse, võimaldades uusi mooduleid lisada olemasolevat numeratsiooni lõhkumata.
Plaintext

VALVUR/
├── launch_VALVUR.py          # Süsteemi alglaadija (Windows/Linux autodetection)
├── utils.py                  # Ühised funktsioonid (logimine, veatöötlus, kaustad)
├── requirements.txt          # Vajalikud Pythoni teegid (pandas, requests, rich jne)
├── .gitignore                # Reeglid prügi ja analüüsitulemuste välistamiseks
│
├── SKRIPTID/                 # Analüüsimootor (Faasipõhine jada)
│   ├── valvurMASTER.py       # Peakontroll ja töövoo orkestraator
│   │
│   │  🔥 FAAS 1: Algkäivitus ja Andmehõive (00-09)
│   ├── 01_terviklus.py       # Algfailide SHA-256 kontroll ja tõendite lukustamine
│   ├── 02_windows_evtx.py    # Windows binaarsete EVTX logide parsimine CSV-ks
│   ├── 03_linux_logid.py     # Linuxi süsteemilogide (syslog, auth.log) struktureerimine
│   │
│   │  🔍 FAAS 2: Filtreerimine ja Tuvastus (10-19)
│   ├── 11_turvafiltreering.py# Müra eemaldamine, kriitilised Event ID-d (nt 4624, 4724)
│   ├── 12_marksonade_otsing.py# MITRE ATT&CK maatriksil põhinev ründejälgede tuvastus
│   │
│   │  🔬 FAAS 3: Süvaanalüüs ja Deobfuskatsioon (20-29)
│   ├── 21_powershell_decode.py# Base64/XOR/Char obfuskatsiooni lahtiharutamine
│   ├── 22_kahtlased_failid.py# Temp / /tmp kaustade audit ja anomaalsete failide jaht
│   ├── 23_linux_syvaanaluus.py# SUID failid, SSH autoriseeritud võtmed, varjatud protsessid
│   │
│   │  🌐 FAAS 4: Välisluure ja Kontekst (30-39)
│   ├── 31_vorgu_skaneerimine.py# Aktiivsete võrguühenduste ja avatud portide kaardistamine
│   ├── 32_kasutajate_audit.py# Privileegid, paroolimuudatused ründeakna ajal (LOLBIN audit)
│   ├── 33_threat_intel_osint.py# OSINT & Profiler: AbuseIPDB, VirusTotal ja LeakCheck API
│   │
│   │  📊 FAAS 5: Süntees ja Raporteerimine (50-59)
│   ├── 51_koond_ajajoon.py   # UNIFIED TIMELINE (Kõikide platvormide logid ühel teljel)
│   ├── 52_genereeri_raport.py# Koondandmete ja ohuindikaatorite (IoC) struktureerimine
│   └── 53_tehniline_raport_pdf.py# Lõppraporti trükk ja vormistamine juhtkonnale
│
└── DOKUMENDID/               # Metoodilised juhendid ja strateegiad
    ├── ANALYYSI_JUHEND.md    # Juhised leiudude tõlgendamiseks
    ├── DEMO_SPIKK.md         # Operatiivne lühijuhend esitluseks
    └── TULEVIKU_MOTTED.md    # VALVUR-i laiendatud arengukava ja visioon

🌐 Nutikas OSINT- & Profiler-Mootor (Faas 4)

VALVUR-i kood sisaldab intelligentset Hübriid-OSINT võimekust (33_threat_intel_osint.py), mis rikastab masinast leitud küberründe märke reaalajas välisluure andmetega.

    Hübriidne režiim (No-Key Fallback): Kui kasutajal puuduvad tasulised või privaatsed API võtmed, lülitub mootor automaatselt ümber Võtmeta režiimile, tehes avalikke veebipäringuid andmebaasidesse (ip-api, MalwareBazaar, LeakCheck public), tagades analüüsi jätkumise igas olukorras.

    Identiteedi Profileerimine (Attribution): Kui süsteemist leitakse ründaja jäetud e-maile või kasutajanimesid, suudab VALVUR analüüsida ajaloolisi andmelekkeid ja foorumite profiile, et tuletada ründaja pärisnimi, vanus, digitaalne jalajälg ja rahvus/päritolumaa (nt tuvastades seoseid Vene või Hiina sotsiaalmeediavõrgustikega).

    Maskeeringu Tuvastus: Süsteem tunneb automaatselt ära, kui ründaja kasutab Tor Exit Node'i, VPN-i või hosting-teenust, andes uurijale teada, et ründaja varjab oma tegelikku asukohta.

📊 Tulemus ja SIEM/XDR Integratsioon

VALVUR-i töö tulemusena genereeritakse isoleeritud kataloog TULEMUSED/[HOSTNAME], mis pakub standardiseeritud CSV/JSON koondajajoont (Unified Timeline). Tänu puhtale andmeformaadile on VALVUR valmis koheseks liidestamiseks tööstuslike platvormidega:

    Wazuh / Elastic Stack: Läbi Filebeati või Wazuh Agendi, mis edastab VALVUR-i poolt mürast puhastatud logid kesksesse SIEM serverisse.

    Splunk: Kasutades Splunki Scripted Input režiimi, kus Splunk käivitab VALVUR-i ja indekseerib selle väljundi reaalajas.

    SOAR (Microsoft Sentinel / Cortex): Võimekus edastada kriitilised ohuindikaatorid otse pilve-API kaudu automaatsete küberkaitse reeglite (Playbooks) käivitamiseks.

🔭 Tulevikuvaated ja Skaleeritavus

Tänu uuele faasipõhisele ülesehitusele on platvormile lihtne lisada täiendavaid mooduleid:

    VALVUR Web UI (SIEM/XDR Dashboard): FastAPI ja Streamlit/React baasil ehitatud kergkaalulise veebiliidese arendus, interaktiivseks logide filtreerimiseks otse brauserist.

    macOS Forensic Support (24_macos_logid.py): Unified Log süsteemi (.tracev3 failide) parsimine ja Apple'i .plist seadistusfailide audit püsivusmehhanismide tuvastamiseks.

    Mobiilne Forensika (Android & iOS): Mobiilsete seadmete logide (ADB) ja iTunesi varukoopiate analüüsimoodulid, tuvastamaks pahatahtlikke rakendusi või kompromiteeritud andmesidet.

    AI-Analüütik: Masinõppe mudelite (LLM/NLP) integreerimine suurte andmemahtude mustrituvastuseks (Pattern Recognition) ja anomaaliate avastamiseks logides.

Autor: Heiki Rebane

Kontakt: GitHub/ocrHeiki

Moto: "Vägi ilma tarkuseta on pime, tarkus ilma väeta on võimetu."
