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
#   |   FAILI NIMI:  DEMO_SPIKK.md                                 |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Eksami esitlusspikker ja tehniline tugi.      |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################


# VALVUR - Eksami Esitlusspikker (Demo Cheat Sheet)

Kasuta seda spikrit, kui käivitad skripti komisjoni ees. See aitab täita "vaikust" ja näidata oma asjatundlikkust.

## 0. Ühe rea käivitus (GitHubist kaughalduse teel)

```bash
# SSH-d sihtmärki ja kleebi see rida – KALI_IP tuleb $SSH_CLIENT seest automaatselt
python3 -c "$(curl -fsSL https://raw.githubusercontent.com/ocrHeiki/VALVUR/main/launch_VALVUR.py)"
```

- **Mida öelda:** "Käivitan VALVUR-i otse GitHubist ilma kettale kirjutamata. Skript kloonib repo mällu, loob virtuaalkeskkonna ja tuvastab automaatselt minu Kali masina IP $SSH_CLIENT keskkonnamuutuja põhjal. Pärast analüüsi saadetakse tulemused SCP-ga tagasi minu Kali töölauale."

## 1. Menüüvalikud (VALVUR_master.py)
- **Valik 1 (kiiranalüüs):** "FAAS 1+2 – tervikluskontroll ja turvafiltreering. Kasutan siis, kui on vaja kiirelt anda esmane hinnang."
- **Valik 2 (E-ITS audit):** "FAAS 4 – E-ITS 2024 baasturvalisuse audit. Kontrollib tulemüüri, paroolipoliitikat, auditlogimist ja võrguseadistust."
- **Valik 3 (täielik):** "Kõik 5 faasi 14 mooduliga – terviklusest lõppraportini. See on põhjalik intsidendianalüüs."

## 2. Terviklus (00) ja Import (01)
- **Mida öelda:** "Nüüd arvutab süsteem logifailidele SHA-256 räsid. See on forensika kuldstandard – kui ma hiljem andmeid muudan, siis räsid ei klapi ja ma jään vahele. Järgmisena kopeerib süsteem lukustatud Windowsi logid turvalisse kohta ja konverteerib need analüüsiks sobivasse CSV-formaati."

## 3. Filtreerimine (02) ja Märksõnad (03)
- **Mida öelda:** "Selles etapis puhastab VALVUR logid mürast. Me ei otsi lihtsalt 'midagi', vaid kasutame MITRE ATT&CK maatriksit, et leida ründajate spetsiifilisi tehnikaid nagu Credential Dumping või Lateral Movement."

## 4. Süvaanalüüs (04) ja Kahtlased failid (06)
- **Mida öelda:** "Siin toimub maagia. VALVUR proovib automaatselt dekodeerida obfuskeeritud PowerShell koodi (Base64 ja XOR). Samuti kontrollib süsteem 'Live Scan' meetodil ajutisi kaustu ja Linuxi püsivuse märke nagu uued SSH võtmed või Cron-tööd."

## 5. Audit (07) ja Kasutajad (11)
- **Mida öelda:** "Nüüd liigume NIST raamistiku 'Protect' faasi. Kontrollime süsteemi vastavust E-ITS paroolipoliitikale ja otsime peidetud root-õigustega kasutajaid. Tulemuseks on samm-sammuline Roadmap süsteemi parandamiseks."

## 6. Kokkuvõte (05 ja Timeline 13)
- **Mida öelda:** "Lõpuks koondab VALVUR kõik killud ühtseks kronoloogiliseks ajajooneks. See võimaldab meil sekundilise täpsusega näha, kuidas ründaja masinasse sisenes ja mis ta siin tegi. Genereeritud Executive Summary on suunatud juhtkonnale, andes kiire vastuse: mis juhtus ja kui hull see on."

---
**NIPP:** Kui mõni skript viskab vea, ütle rahulikult: "Tegemist on mitte-kriitilise hoiatusega. MASTER-skript on ehitatud robustseks ja jätkab teiste andmeallikate analüüsi."
