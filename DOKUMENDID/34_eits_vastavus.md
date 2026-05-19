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
#   |   FAILI NIMI:  34_eits_vastavus.md                                  |   #
#   |   LOODUD:      2026-05-18                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   E-ITS 2024 baasturvalisuse kontroll - meetmete       |   #
#   |                kirjeldus ja vastavustasemete selgitused.            |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
```
# VALVUR - E-ITS 2024 Baasturvalisuse Kontroll

See dokument kirjeldab `34_eits_vastavus.py` skripti, mis teostab automaatse
**E-ITS 2024 (Eesti Infoturbestandard)** baasturvalisuse kontrolli Windowsi ja
Linuxi süsteemidel, tuvastades vastavuse kolmele turvatasemele:
**KESK (M)** / **STANDARD (A)** / **KÕRG (S)**.

Käivitamiseks:
```bash
python3 SKRIPTID/34_eits_vastavus.py
```

---

## E-ITS 2024 Turvatasemed

E-ITS 2024 jagab turvameetmed kolmeks kategooriaks vastavalt infovarade
kaitsevajadusele:

| Tase   | Tähis | Kirjeldus | Tähendus |
|--------|-------|-----------|----------|
| **KESK** | **M** (Minimum) | **Baastase** – kohustuslikud põhimeetmed, mida peab rakendama kõigi infovarade puhul. | Madalaim aktsepteeritav turvatase. |
| **STANDARD** | **A** (Advanced) | **Täiendav tase** – soovituslikud meetmed, mida rakendatakse olulisemate infovarade kaitseks. | Keskmine turvatase. |
| **KÕRG** | **S** (Special) | **Kõrge tase** – spetsiifilised meetmed eriti kriitiliste infovarade kaitseks. | Kõrgeim turvatase. |

---

## Kontrollitavad E-ITS Meetmed

### CON – Ühenduvus (Connectivity)

| Meede | Tase | Kontroll | Kirjeldus |
|-------|------|----------|-----------|
| **CON.1.M2** | **KESK** | Tulemüür | UFW / iptables / nftables / Windows Firewall oleku kontroll. Kui tulemüür pole aktiivne, on süsteem võrgus kaitsmata. |
| **CON.1.M1** | **KESK** | Avatud pordid | `ss -tlnp` / `netstat` abil tuvastatakse kõik avatud TCP pordid. Ohtlikud pordid (Telnet 23, FTP 21) märgitakse eraldi. |
| **CON.1.A1** | **STANDARD** | SSH turve | **PermitRootLogin** – kas root saab SSH kaudu sisse logida. **PasswordAuthentication** – kas parooliga autentimine on lubatud. SSH port – kas vaikeport 22 on muudetud. |
| **CON.1.A1** | **STANDARD** | Fail2ban | Kas Fail2ban on paigaldatud ja aktiivne (kaitseb brute-force rünnete vastu). |
| **CON.1.A1** | **STANDARD** | Telnet/FTP/ RDP | Ohtlike teenuste tuvastus (telnet, rsh, rlogin, vsftpd, tftp). |
| **CON.1.A1** | **STANDARD** | SMB1 | Windowsis kontrollitakse, kas SMB1 on lubatud (väga vana ja ebaturvaline). |
| **CON.1.A1** | **STANDARD** | WinRM | Windowsis kontrollitakse WinRM olemasolu (kaugjuhtimine). |
| **CON.1.A1** | **STANDARD** | RDP | Windowsis kontrollitakse RDP olekut ja NLA (Network Level Authentication) nõuet. |

> **NIST CSF** – IDENTIFY (ID.AM-01, ID.RA-01), PROTECT (PR.AC-03, PR.PT-04)

---

### SYS – Süsteem (System)

| Meede | Tase | Kontroll | Kirjeldus |
|-------|------|----------|-----------|
| **SYS.1.1.M1** | **KESK** | Süsteemi kõvendamine | Windows Defender (reaalajakaitse), UAC (User Account Control), ClamAV, chkrootkit, rkhunter. |
| **SYS.1.3.M1** | **KESK** | /tmp ja /var/tmp | Sticky Bit olemasolu – ilma selleta saavad kasutajad üksteise ajutisi faile kustutada. |
| **SYS.1.3.M1** | **KÕRG** | /dev/shm | Sticky Bit olemasolu jagatud mälus (kõrgmeede). |
| **SYS.1.3.M3** | **KESK** | Turvauuendused | APT/YUM/DNF/Zypper kaudu kontrollitakse, kas turvauuendused on ajakohased. |
| **SYS.1.1.A6** | **STANDARD** | Teenuste audit | Kõikide töös olevate teenuste loendamine, ohtlike teenuste (telnet, rsh, vsftpd, tftp, nfs, RemoteRegistry, TlntSvr) tuvastus. |
| **SYS.1.3.A1** | **STANDARD** | SELinux / AppArmor | Mandaatjuurdepääsu kontrolli süsteem – kas see on lubatud ja aktiivne (Enforcing / Permissive / Disabled). |
| **SYS.1.3.A1** | **KÕRG** | AIDE / Tripwire | Failide tervikluse kontrolli tööriistade olemasolu. |

> **NIST CSF** – PROTECT (PR.PT-01, PR.PT-03, PR.AC-06), IDENTIFY (ID.RA-01)

---

### ORP – Organisatsioon ja Personal (Organization & Personnel)

| Meede | Tase | Kontroll | Kirjeldus |
|-------|------|----------|-----------|
| **ORP.4.M22** | **KESK** | auditd / auditpol | Linuxis: kas auditd on paigaldatud ja aktiivne. Windowsis: auditipoliitika olek (auditpol /get). |
| **ORP.4.A1** | **KESK** | Paroolipoliitika – kehtivusaeg | PASS_MAX_DAYS / maximum password age – kas paroolid aeguvad max 90 päeva jooksul. |
| **ORP.4.A1** | **KESK** | Paroolipoliitika – pikkus | Windowsis: minimaalse parooli pikkuse kontroll (>=8 tähemärki). |
| **ORP.4.A1** | **KESK** | Paroolipoliitika – lukustumine | Windowsis: konto lukustumisläve kontroll peale ebaõnnestunud sisselogimisi. |
| **ORP.4.A1** | **STANDARD** | Parooli miinimumvanus | PASS_MIN_DAYS – kas parooli saab kohe uuesti muuta (>=1 päev). |
| **ORP.4.A2** | **KÕRG** | Privilegeeritud kasutajad | Administraatorite rühma liikmete loend (Windows). NOPASSWD reeglite kontroll /etc/sudoers (Linux). |
| **ORP.4.M22** | **KESK** | journald / rsyslog | Linuxis: kas systemd-journald ja rsyslog on aktiivsed. |

> **NIST CSF** – DETECT (DE.AE-03, DE.CM-01), PROTECT (PR.AC-01, PR.AC-02)

---

### NET – Võrk (Network)

| Meede | Tase | Kontroll | Kirjeldus |
|-------|------|----------|-----------|
| **NET.1.M1** | **KESK** | IP edastamine | `ip_forward` – kas süsteem edastab IP pakette (ruuteri roll). |
| **NET.1.M1** | **KESK** | SYN flood kaitse | TCP SYN cookies – kas on lubatud (kaitse SYN flood DoS rünnete vastu). |
| **NET.1.M1** | **KESK** | Võrguliidesed | Aktiivsete liideste tuvastus (`ip addr`). |
| **NET.1.M1** | **KESK** | Marsruutimine | Vaikimisi marsruudi tuvastus (`ip route`). |
| **NET.1.M1** | **KESK** | Tulemüüri reeglid | iptables ahelate ja reeglite arvu kontroll. |
| **NET.1.M1** | **STANDARD** | ICMP redirect | Kas süsteem võtab vastu ICMP redirect pakette (MITM risk). |
| **NET.1.M1** | **STANDARD** | DHCP/DNS | DHCP serveri ja DNS resolveri olemasolu. |
| **NET.1.A1** | **STANDARD** | NAT / MASQUERADE | Kas süsteem kasutab NAT-i (ruuter/gateway). Port forwardimise tuvastus. |
| **NET.1.A1** | **STANDARD** | ARP filter | Kas ARP filter on aktiivne (kaitse ARP spoofingu vastu). |

> **NIST CSF** – IDENTIFY (ID.AM-01, ID.AM-02), PROTECT (PR.PT-04)

---

### INF – Infrastruktuur (Infrastructure)

| Meede | Tase | Kontroll | Kirjeldus |
|-------|------|----------|-----------|
| **INF.1.M1** | **KESK** | Active Directory | Kas süsteem on domeenikontroller (AD). Anonüümse loetlemise piirang. |
| **INF.1.A1** | **KESK** | Varundamine | Varundustööriistade olemasolu (rsync, duplicity, borg, wbadmin). |

> **NIST CSF** – RECOVER (RC.RP-01), PROTECT (PR.DS-04)

---

### APP – Rakendus (Application)

| Meede | Tase | Kontroll | Kirjeldus |
|-------|------|----------|-----------|
| **APP.1.M1** | **KESK** | TLS 1.2 | Windowsis: kas TLS 1.2 on lubatud (SCHANNEL). |
| **APP.1.M1** | **STANDARD** | TLS 1.3 | Windowsis: kas TLS 1.3 on lubatud. |
| **APP.1.M1** | **KESK** | SSL 3.0 | Windowsis: kas SSL 3.0 on keelatud (POODLE ründe kaitse). |

> **NIST CSF** – PROTECT (PR.DS-02, PR.AC-03)

---

## Rollituvastus

Skript tuvastab automaatselt süsteemi rolli hostinime ja süsteemi
parameetrite põhjal:

| Roll | Tuvastus | Käivitatavad auditid |
|------|----------|----------------------|
| **TÖÖJAAM** (klient) | Vaikeväärtus või "client", "pc", "workstation" hostinimes | Linux/Windows audit, tulemüüri audit |
| **SERVER (DC)** | "dc", "domain", "ad" hostinimes või Samba/AD tuvastus | Linux/Windows audit, tulemüüri audit, serveri süvaaudit |
| **SERVER** (faili-/rakendus) | "server", "file", "nas" hostinimes | Linux/Windows audit, tulemüüri audit, serveri süvaaudit |
| **RUUTER** | "ruuter", "router", "gateway", "gw" hostinimes või OpenWrt tuvastus | Linux audit, ruuteri süvaaudit |
| **TULEMÜÜR** | "tulemuur", "firewall", "fw" hostinimes | Linux/Windows audit, tulemüüri süvaaudit |

Kui `ip_forward=1` tuvastatakse Linuxis, käivitatakse automaatselt ka
ruuteri süvaaudit, isegi kui hostinimi seda ei viita.

---

## Väljund

### Terminal (ekraan)

Iga leid kuvatakse real-ajal vormingus:
```
[STAATUS] [MEEDE] KIRJELDUS | SOOVITUS: ...
```

Staatused:
- **OK** – meede on korras, vastab nõudele
- **INFO** – informatiivne teade, ei ole otsene turvaprobleem
- **HIGH** – kõrge riskiga leid, vajab tähelepanu
- **CRITICAL** – kriitiline turvaprobleem, kohene tegutsemine vajalik
- **ERROR** – kontrolli ebaõnnestus (nt käsk puudub)

### Raport (fail)

Tulemused salvestatakse faili:
```
TULEMUSED/34_tulemus_eits_vastavus.txt
```

Raport sisaldab:
1. VALVUR logo ja päis (kuupäev, host, OS, roll)
2. Kõik leiud grupeerituna E-ITS tasemete kaupa (**KESK** → **STANDARD** → **KÕRG**)
3. Kokkuvõtlik tabel iga taseme kohta (OK / INFO / HIGH / CRITICAL)
4. Hinnang iga taseme kohta (VASTAB / OSALISELT / EBAKÕLAKOHANE)
5. NIST CSF 2.0 vastavuse kokkuvõte

---

## Eksamistrateegia

| Masin | Soovitatud tegevus |
|-------|-------------------|
| **itsh-eksam-dc01** | Käivita `34_eits_vastavus.py`. Otsi AD-spetsiifilisi leide (RestrictAnonymous, paroolipoliitika, admin kontod). |
| **itsh-eksam-ruuter** | Käivita `34_eits_vastavus.py`. Skript tuvastab rolli automaatselt ja teostab ruuteri süvaauditi (NAT, iptables, ip_forward). |
| **itsh-eksam-fileserver** | Käivita `34_eits_vastavus.py`. Kontrolli varunduse staatust ja failide tervikluse tööriistu. |
| **itsh-eksam-kali** | Käivita `34_eits_vastavus.py`. Tuvastab Kali rolli, kontrollib tulemüüri, auditd ja turvauuendusi. |
| **client01-03** | Käivita `34_eits_vastavus.py`. Kontrolli Windowsi põhimeetmeid (Defender, UAC, tulemüür, paroolipoliitika). |

### NIST CSF 2.0 Kaardistus (E-ITS 2024)

```
IDENTIFY  → CON.1 (võrgu kaardistus), SYS.1 (süsteemi inventar)
PROTECT   → CON.1.M2 (tulemüür), SYS.1.3.M3 (uuendused),
            ORP.4.A1 (paroolid), INF.1.A1 (varundus)
DETECT    → ORP.4.M22 (logimine), CON.1.A1 (Fail2ban)
RESPOND   → SYS.1.3.A1 (AIDE/Tripwire), kõrge riskiga leidude
            soovitused
RECOVER   → INF.1.A1 (varunduse staatus)
```

---

## Näidisväljund (kokkuvõte)

```
===============================================================================
  E-ITS 2024 VASTAVUSE KOKKUVÕTE
===============================================================================

  [KESK (M) - Baastase]
    OK: 5  |  INFO: 2  |  HIGH: 2  |  CRITICAL: 1
    HINNANG: EBAKÕLAKOHANE - kriitilisi turvaprobleeme

  [STANDARD (A) - Täiendav tase]
    OK: 1  |  INFO: 4  |  HIGH: 7  |  CRITICAL: 0
    HINNANG: OSALISELT VASTAV - kõrge riskiga leidudega

  [KÕRG (S) - Kõrge tase]
    OK: 1  |  INFO: 2  |  HIGH: 0  |  CRITICAL: 0
    HINNANG: VASTAB NÕUETELE

  SÜSTEEMI ROLL: SERVER (DC)
  HOSTNAME: secLAB
  OS: Linux
  KOKKU: 25 kontrolli teostatud
===============================================================================
```

---

## Sõltuvused

- **Python 3** — skript on kirjutatud Python 3-s
- **utils.py** — VALVUR-i ühiskasutatavad abifunktsioonid
- **sudo õigused** — mõned kontrollid vajavad administraatori õigusi
  (UFW, iptables, auditctl, fail2ban)
- **PowerShell** — Windowsi kontrollid kasutavad PowerShell käske

Skript on loodud töötama nii iseseisvalt kui ka `valvurMASTER.py`
kaudu (FAAS 4 moodulina).

---

*E-ITS 2024 – Eesti Infoturbestandard. Vastavushinnang põhineb
automaatsel skaneerimisel. Täpseks hindamiseks vajalik käsitsi
ülevaatus.*
