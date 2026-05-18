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
#   |   FAILI NIMI:  VALVUR_master_kaughaldus.md                          |   #
#   |   LOODUD:      2026-05-18                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   VALVUR Master Launcher ja kaughalduse                |   #
#   |                eksfiltreerimise juhend (SCP Kali masinasse).        |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
```
# VALVUR – Keskne Master Launcher ja Kaughalduse Eksfiltreerimine

See dokument kirjeldab, kuidas kasutada `VALVUR_master.py` ja `launch_VALVUR.py`
skripte, et käivitada analüüs kaugmasinal ja saata tulemused automaatselt
Kali masina töölauale SCP protokolli kaudu.

---

## Arhitektuur

```
┌─────────────────────────────────────────────────────────────────────┐
│  KALI MASIN (analüütiku tööjaam)                                    │
│  IP: 192.168.10.50                                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 1. SSH ühendus uuritavasse masinasse                         │   │
│  │ 2. Käivitab VALVUR githubi ühe rea käsuga                    │   │
│  │ 3. Ootab tulemusi                                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    SSH (port 22)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  UURITAV MASIN (DC / server / ruuter / klient)                      │
│  OS: Windows või Linux                                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ 1. VALVUR kloonitakse GitHubist                              │   │
│  │ 2. Luuakse Python venv                                       │   │
│  │ 3. Käivitatakse VALVUR_master.py (interaktiivne menüü)       │   │
│  │ 4. Analüüsitakse süsteemi                                    │   │
│  │ 5. Tulemused pakitakse ZIP-ks                                │   │
│  │ 6. Saadetakse SCP-ga tagasi Kali masinasse                   │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    SCP (port 22)
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  KALI MASIN (tulemused kohal)                                       │
│  /home/kali/Desktop/VALVUR_TULEMUSED/                               │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ VALVUR_dc01_20260518_143022.zip                              │   │
│  │ VALVUR_fileserver_20260518_151045.zip                        │   │
│  │ VALVUR_ruuter_20260518_160230.zip                            │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Ühe rea käivitus (githubist)

### 1.1 Lihtkäivitus (ilma eksfiltreerimiseta)

```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py)"
```

Skript kloonib repo, loob venv ja käivitab interaktiivse menüü.
Eksfiltreerimist saab hiljem seadistada menüüst **5**.

### 1.2 Käivitus koos Kali IP-ga (soovitatud)

**Variant A – keskkonnamuutuja:**
```bash
KALI_IP=192.168.10.50 python3 -c "$(curl -fsSL https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py)"
```

**Variant B – käsurea argument:**
```bash
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py)" 192.168.10.50
```

**Variant C – automaatne (Kali enda IP):**
```bash
KALI_IP=$(hostname -I | awk '{print $1}') python3 -c "$(curl -fsSL https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py)"
```

> ⚡ **Eksami nipp:**  selle käsuga ei pea sa ühtegi IP-d meelde jätma –
> Kali IP võetakse automaatselt ja tulemused jõuavad otse töölauale.

---

## 2. Interaktiivne menüü

Pärast käivitust kuvatakse:

```
  HOST: itsh-eksam-dc01
  OS:   Linux
  VÄLJUND: /tmp/VALVUR_LIVE/TULEMUSED/itsh-eksam-dc01
  EKSFILTREERIMINE: AKTIIVNE -> kali@192.168.10.50:/home/kali/Desktop/VALVUR_TULEMUSED
======================================================================
  1. FAAS 1+2 – Terviklus + Logifiltreering (KIIRANALÜÜS)
  2. FAAS 4   – E-ITS 2024 baasturvalisuse audit
  3. KÕIK MOODULID – Täielik analüüs (FAAS 1–5)
  4. Ekspordi tulemused käsitsi (ilma uue analüüsita)
  5. Seadista kaughalduse eksfiltreerimine
  6. Välju
======================================================================
```

### Valikute selgitused

| Valik | Kirjeldus | Kasutusala |
|-------|-----------|------------|
| **1** | Tervikluskontroll (SHA-256) + turvafiltreering + märksõnade otsing | Kiire ohutuvastus, kui aega on vähe |
| **2** | E-ITS 2024 audit (kasutajad, võrk, tulemüür, paroolid) + võrguskaneerimine | Baasturvalisuse hindamine |
| **3** | Kõik 5 faasi – terviklusest raportini (14 moodulit) | Täielik intsidendianalüüs |
| **4** | Pakib olemasolevad tulemused ja saadab Kalisse | Kui analüüs juba tehtud, aga ununes ära saata |
| **5** | Kali IP / kasutaja / sihtkausta muutmine | Esmane seadistus või võrgu muutus |

---

## 3. Töövoog samm-sammult

### Eksami stsenaarium 1 – DC analüüs koos eksfiltreerimisega

```
1. Kali masinas:
   ssh heiki@itsh-eksam-dc01

2. Uuritavas masinas (DC):
   KALI_IP=$(hostname -I | awk '{print $1}') python3 -c "$(curl -fsSL ...)"

3. VALVUR menüüs:
   Vali "3. KÕIK MOODULID"
   (oota 5–10 minutit)

4. Tulemused Kali töölaual:
   ls -la /home/kali/Desktop/VALVUR_TULEMUSED/
   > VALVUR_itsh-eksam-dc01_20260518_143022.zip
```

### Eksami stsenaarium 2 – ainult E-ITS audit

```
1. KALI_IP=192.168.10.50 python3 -c "$(curl -fsSL ...)"

2. Menüüs:
   Vali "2. FAAS 4 – E-ITS 2024 audit"

3. ZIP saabub Kali töölauale sisuga:
   34_tulemus_eits_vastavus.txt
   31_tulemus_vorgu_skaneerimine.txt
   32_tulemus_kasutajate_audit.csv
```

---

## 4. Käsitsi seadistus (ilma githubita)

Kui oled juba repoo kloonitud ja tahad otse käivitada:

```bash
cd VALVUR
python3 SKRIPTID/VALVUR_master.py
```

Kali IP seadistamiseks:
```bash
KALI_IP=192.168.10.50 python3 SKRIPTID/VALVUR_master.py
```

Või menüüst valik **5** – seadistus salvestub faili
`SKRIPTID/.kali_config` ja jääb püsima.

Konfiguratsioonifaili sisu:
```
KALI_IP=192.168.10.50
KALI_USER=kali
KALI_PATH=/home/kali/Desktop/VALVUR_TULEMUSED
```

---

## 5. Nõuded

### Uuritav masin
- Python 3
- `git` (kui kasutad githubi käivituskäsku)
- `openssh-client` (SCP jaoks, Linuxis tavaliselt olemas)
- Internetiühendus (githubi kloonimiseks)

### Kali masin
- `openssh-server` peab jooksma (`sudo systemctl status ssh`)
- Kaust `KALI_PATH` peab eksisteerima või SCP loob selle automaatselt
- Võrgühendus uuritava masinaga (port 22)

Kali SSH kontroll:
```bash
sudo systemctl enable ssh --now
ss -tlnp | grep 22  # port 22 peab kuulama
```

---

## 6. Turvakaalutlused

| Aspekt | Selgitus |
|--------|----------|
| **StrictHostKeyChecking=no** | Eksami keskkonnas mugav, tootmises eemalda |
| **SCP parool** | Küsitakse konsoolist, kui võtmeid pole seatud |
| **Ajutine kaust** | Repo kloonitakse `/tmp/VALVUR_LIVE/`, mis kustub taaskäivitusel |
| **ZIP kustutamine** | Pärast edukat SCP-d kustutatakse kohalik pakifail |
| **Andmed** | Tulemused sisaldavad tundlikku infot – kaitse juurdepääsu |

### SSH võtmega autentimine (soovitatud)

```bash
# Kali masinas:
ssh-keygen -t ed25519
ssh-copy-id kali@192.168.10.50  # (kui Kali on ka sihtmärk – siin vastupidi)

# Või uuritavas masinas võtme genereerimine:
ssh-keygen -t ed25519
ssh-copy-id kali@192.168.10.50
```

---

## 7. Tõrkeotsing

| Probleem | Põhjus | Lahendus |
|----------|--------|----------|
| `ssh: connect to host ... port 22: Connection refused` | Kali SSH server ei jookse | `sudo systemctl start ssh` |
| `scp: ... No such file or directory` | Sihtkaust puudub | `mkdir -p /home/kali/Desktop/VALVUR_TULEMUSED` |
| `Permission denied (publickey,password)` | SSH autentimine ebaõnnestus | Kontrolli parooli või sea võtmed |
| `git: command not found` | Git pole paigaldatud | `sudo apt install git` |
| Tulemused jäid kohalikku | SCP ebaõnnestus | Otsi pakifail menüüst: `VALVUR_*.zip` asub `SKRIPTID/` kõrval |

---

## 8. Failide struktuur (pärast analüüsi)

```
/tmp/VALVUR_LIVE/                       # Ajutine töökaust
├── SKRIPTID/
│   ├── VALVUR_master.py                # Master launcher
│   ├── .kali_config                    # Kali seadistus
│   ├── 01_terviklus.py
│   ├── 34_eits_vastavus.py
│   └── ...
├── TULEMUSED/
│   └── itsh-eksam-dc01/
│       ├── 01_tulemus_terviklus_raport.txt
│       ├── 11_tulemus_turvafiltreering.csv
│       ├── 34_tulemus_eits_vastavus.txt
│       └── ...
└── venv/                               # Python virtuaalkeskkond

Kali töölaual:
/home/kali/Desktop/VALVUR_TULEMUSED/
└── VALVUR_itsh-eksam-dc01_20260518_143022.zip
```

---

## 9. Kokkuvõte

VALVUR Master Launcher võimaldab:

1. **SSH** kaudu analüüsida kaugmasinat ilma füüsilise ligipääsuta
2. **Automaatne tulemuste tagastus** Kali masinasse SCP protokolli kaudu
3. **Menüüpõhine valik** – kiiranalüüs, E-ITS audit või täielik intsidendianalüüs
4. **IP edastamine** githubi ühe rea käsuga – IP tuleb kaasa juba käivitushetkel
5. **Püsiv konfiguratsioon** – Kali IP salvestub `.kali_config` faili

> *"VALVUR: analüüs teostatud süsteemi kloonil, tulemused kättesaadavad Kali töölaual."*
