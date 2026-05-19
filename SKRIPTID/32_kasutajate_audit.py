#!/usr/bin/env python3
"""
###############################################################################
#                                                                             #
#   █████   █████            ████                                             #
#  ▒▒███   ▒▒███            ▒▒███                                             #
#   ▒███    ▒███   ██████    ▒███  █████ █████ █████ ████ ████████             #
#   ▒███    ▒███  ▒▒▒▒▒███   ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███            #
#   ▒▒███   ███    ███████   ▒███  ▒███  ▒███  ▒███ ▒███  ▒███ ▒▒▒             #
#    ▒▒▒█████▒    ███▒▒███   ▒███  ▒▒███ ███    ▒███ ▒███  ▒███                 #
#      ▒▒███     ▒▒████████ █████  ▒▒█████     ▒▒████████ █████                #
#       ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒    ▒▒▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                 #
#                                                                             #
#   =======================================================================   #
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  32_kasutajate_audit.py                               |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Kasutajate tuvastus ja E-ITS turvaaudit              |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import csv
import platform
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("KASUTAJAD_AUDIT")
    out_dir = utils.get_output_dir()
except Exception:
    # Fallback mehhanism juhuks, kui utils pole kättesaadav
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()
    out_dir = "TULEMUSED"

LOGO = r"""
###############################################################################
#             VALVUR - KASUTAJATE JA SÜSTEEMIPOLIITIKATE AUDIT                #
###############################################################################
"""

def extract_users():
    """Tuvastab reaalsed kasutajanimed logifailidest ja süsteemikomponentidest."""
    users = set()
    in_file = os.path.join(out_dir, '11_tulemus_turvafiltreering.csv')
    
    # 1. Kasutajate eraldamine eelmisest turvafiltreeringu CSV raportist
    if os.path.exists(in_file):
        try:
            with open(in_file, mode='r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    msg = row.get('Message', '')
                    if "TargetUserName:" in msg:
                        try:
                            # Puhastame kasutajanime välja
                            raw_user = msg.split("TargetUserName:")[1].split("|")[0].split()[0].strip()
                            # Välistame tühjad ja Windowsi masinakontod (lõpevad $ märgiga)
                            if raw_user and not raw_user.endswith('$'):
                                users.add(raw_user)
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"CSV analüüsil tekkis viga: {e}")
            
    # 2. Kohalike kasutajate tuvastus (Linuxi baasil)
    if os.path.exists("/etc/passwd"):
        try:
            with open("/etc/passwd", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        users.add(line.split(":")[0])
        except Exception as e:
            logger.error(f"/etc/passwd parsimine ebaõnnestus: {e}")
            
    return sorted(list(users))


def check_windows_policies():
    """Windowsi paroolipoliitika kontroll viisil, mis ei sõltu OS-i keelest."""
    results = []
    if platform.system() != "Windows":
        return results
        
    try:
        # Kasutame net accounts väljundit, kuid ei otsi konkreetset teksti, vaid võtame read toorelt infona
        output = subprocess.check_output(["net", "accounts"], timeout=10).decode(errors='ignore')
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        
        # Lisame kontrolli tulemuse struktuurselt
        results.append({
            "Kontroll": "E-ITS CON.1.A1: Paroolipoliitika (Windows)",
            "Staatus": "INFO",
            "Meede": f"Tuvastatud seaded: {lines[0] if lines else 'Kättesaadav'} (Vaata käsitsi üle)"
        })
    except Exception as e:
        logger.error(f"Windowsi poliitika tuvastus nurjus: {e}")
    return results


def check_linux_policies():
    """Linuxi paroolipoliitika (login.defs) kontroll vastavalt E-ITS reeglitele."""
    results = []
    if not os.path.exists("/etc/login.defs"):
        return results
        
    try:
        with open("/etc/login.defs", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if ("PASS_MAX_DAYS" in line or "PASS_MIN_LEN" in line) and not line.startswith("#"):
                    results.append({
                        "Kontroll": f"E-ITS CON.1.A2: Paroolisätted ({line.split()[0]})",
                        "Staatus": "AUDIT",
                        "Meede": f"Aktiivne piirang: {line}"
                    })
    except Exception as e:
        logger.error(f"Linuxi poliitika lugemine nurjus: {e}")
    return results


def check_running_services():
    """Käimasolevate teenuste auditeerimine minimaalsuse põhimõttest lähtuvalt."""
    results = []
    current_os = platform.system()
    try:
        if current_os == "Windows":
            # Kasutame PowerShelli, mis tagab puhta ja keeleülese nimekirja aktiivsetest teenustest
            output = subprocess.check_output(["powershell", "-Command", "Get-Service | Where-Object {$_.Status -eq 'Running'}"], timeout=15).decode(errors='ignore')
        else:
            output = subprocess.check_output(["systemctl", "list-units", "--type=service", "--state=running", "--no-legend"], timeout=15).decode(errors='ignore')
            
        count = len([line for line in output.splitlines() if line.strip()])
        results.append({
            "Kontroll": "E-ITS SYS.1.1.A5: Minimaalsuse põhimõte",
            "Staatus": "OK",
            "Meede": f"Süsteemis töötab aktiivselt {count} teenust. Kontrolli mittevajalikke rakendusi."
        })
    except Exception as e:
        logger.error(f"Teenuste kontroll nurjus: {e}")
    return results


def check_firewall():
    """Tulemüüri seisundi keele- ja platvormiülene tuvastus."""
    results = []
    current_os = platform.system()
    try:
        if current_os == "Windows":
            output = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles"], timeout=10).decode(errors='ignore')
            # Kontrollime režiimi olemasolu sõltumata keelest (tavaliselt ON, Lülitatud sisse vms)
            is_on = "ON" in output.upper() or "LÜLITATUD SISSE" in output.upper() or "ACTIVE" in output.upper()
            status = "OK" if is_on else "HOIATUS"
            meede = "Windows Defender Firewall on aktiivne." if is_on else "Tulemüür võib olla välja lülitatud või valesti seadistatud!"
        else:
            # Linuxis proovime ufw-d, kui see ebaõnnestub või puudub, kontrollime iptables-it
            try:
                output = subprocess.check_output(["sudo", "ufw", "status"], timeout=10).decode(errors='ignore')
                is_on = "active" in output.lower() or "aktiivne" in output.lower()
            except Exception:
                output = subprocess.check_output(["sudo", "iptables", "-L"], timeout=10).decode(errors='ignore')
                is_on = len(output.splitlines()) > 3
                
            status = "OK" if is_on else "HOIATUS"
            meede = "Linuxi paketifilter on aktiivne." if is_on else "Aktiivseid tulemüüri reegleid ei tuvastatud!"
            
        results.append({"Kontroll": "E-ITS NET.3.A1: Tulemüüri rakendamine", "Staatus": status, "Meede": meede})
    except Exception as e:
        results.append({
            "Kontroll": "E-ITS NET.3.A1: Tulemüüri rakendamine",
            "Staatus": "INFO",
            "Meede": f"Automaatne tuvastus piiratud õiguste või puuduva utiliidi tõttu võimatu: {e}"
        })
    return results


def check_audit_policy():
    """Logimis- ja auditipoliitika olemasolu kontroll süsteemis."""
    results = []
    current_os = platform.system()
    try:
        if current_os == "Windows":
            output = subprocess.check_output(["auditpol", "/get", "/category:*"], timeout=10).decode(errors='ignore')
            has_audit = "Success" in output or "Edukus" in output or "No Auditing" not in output
            status = "OK" if has_audit else "HOIATUS"
            meede = "Sündmuste auditeerimine on sisse lülitatud." if has_audit else "Kriitilised auditilogi kategooriad võivad olla keelatud!"
        else:
            auditd_present = os.path.exists("/var/log/audit/audit.log") or os.path.exists("/etc/audit/auditd.conf")
            status = "OK" if auditd_present else "INFO"
            meede = "Süsteemis on tuvastatud auditd komponendid." if auditd_present else "Kohalikku auditd teenust ei leitud vaikimisi kataloogidest."
            
        results.append({"Kontroll": "E-ITS OPS.1.1.A4: Logimise tagamine", "Staatus": status, "Meede": meede})
    except Exception as e:
        results.append({
            "Kontroll": "E-ITS OPS.1.1.A4: Logimise tagamine",
            "Staatus": "INFO",
            "Meede": f"Auditipoliitika kontroll ebaõnnestus: {e}"
        })
    return results


def main():
    print(LOGO)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, '32_tulemus_kasutajate_audit.csv')

    print("[*] Alustan kasutajakontode ja turvapoliitikate kaardistamist...")
    users = extract_users()
    
    audit_results = []
    audit_results += check_windows_policies()
    audit_results += check_linux_policies()
    audit_results += check_running_services()
    audit_results += check_firewall()
    audit_results += check_audit_policy()

    all_rows = []
    # 1. Lisame tuvastatud kontod struktureeritult
    for u in users:
        all_rows.append({"Tüüp": "KASUTAJA", "Nimi": u, "Detail": "Tuvastatud süsteemi logidest või kohalikust konfiguratsioonist."})
        
    # 2. Lisame E-ITS auditi tulemused
    for r in audit_results:
        all_rows.append({"Tüüp": "E-ITS_AUDIT", "Nimi": r["Kontroll"], "Detail": f"[{r['Staatus']}] {r['Meede']}"})

    try:
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Tüüp", "Nimi", "Detail"])
            writer.writeheader()
            writer.writerows(all_rows)
            
        logger.info(f"Kasutajate ja E-ITS audit edukalt valmis: {out_file} ({len(users)} kasutajat, {len(audit_results)} kontrolli)")
        print(f"[✓] Auditeerimine edukalt lõpetatud! Raport salvestatud: {out_file}")
    except Exception as e:
        logger.error(f"Tulemuste kirjutamine faili nurjus: {e}")
        print(f"[-] Viga raporti salvestamisel: {e}")


if __name__ == "__main__":
    main()
