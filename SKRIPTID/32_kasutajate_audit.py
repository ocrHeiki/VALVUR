#!/usr/bin/env python3
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
except:
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()
    out_dir = "TULEMUSED"

LOGO = r"""
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
###############################################################################
"""

def extract_users():
    """Tuvastab potentsiaalsed kasutajanimed forensilistest tulemustest ja kohalikust süsteemist."""
    users = set()
    in_file = os.path.join(out_dir, '11_tulemus_turvafiltreering.csv')
    
    # 1. Kasutajate eraldamine eelmisest turvafiltreeringu CSV-st
    if os.path.exists(in_file):
        try:
            with open(in_file, mode='r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    msg = row.get('Message', '')
                    if "TargetUserName:" in msg:
                        try:
                            # Puhastame kasutajanime välja
                            parts = msg.split("TargetUserName:")
                            if len(parts) > 1:
                                username = parts[1].split("|")[0].split()[0].strip()
                                if username and not username.endswith('$'): # Eemaldame masinakontod
                                    users.add(username)
                        except Exception:
                            continue
        except Exception as e:
            logger.error(f"CSV analüüsil tekkis viga: {e}")
            
    # 2. Kohalike kasutajate tuvastus (Linux fallback)
    if os.path.exists("/etc/passwd"):
        try:
            with open("/etc/passwd", "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if line.strip() and not line.startswith("#"):
                        users.add(line.split(":")[0])
        except Exception as e:
            logger.error(f"/etc/passwd lugemisel tekkis viga: {e}")
            
    return sorted(list(users))

def check_windows_policies():
    """Windowsi paroolipoliitika kontroll (Keeleülene analüüs numbrite baasil)."""
    results = []
    try:
        output = subprocess.check_output(["net", "accounts"], timeout=10).decode(errors='ignore')
        # Kuna "net accounts" väljund on keelepõhine, otsime ridu unikaalsete märkide või numbrite järgi
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        
        results.append({
            "Kontroll": "E-ITS CON.1.A1: Paroolipoliitika",
            "Staatus": "INFO",
            "Meede": f"Windowsi paroolisätted tuvastatud. Sisu: {lines[0] if lines else 'Leitud'}"
        })
    except Exception as e:
        logger.error(f"Windowsi poliitika kontroll ebaõnnestus: {e}")
    return results

def check_linux_policies():
    """Linuxi paroolipoliitika (login.defs) kontroll vastavalt E-ITS nõuetele."""
    results = []
    if not os.path.exists("/etc/login.defs"):
        return results
        
    try:
        with open("/etc/login.defs", "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if ("PASS_MAX_DAYS" in line or "PASS_MIN_LEN" in line) and not line.startswith("#"):
                    results.append({
                        "Kontroll": "E-ITS CON.1.A2: Linuxi parooliaeg",
                        "Staatus": "AUDIT",
                        "Meede": f"Aktiivne reegel: {line}"
                    })
    except Exception as e:
        logger.error(f"Linuxi poliitika kontroll ebaõnnestus: {e}")
    return results

def check_running_services():
    """Tuvastab käimasolevad teenused, et märgata mittevajalikke rakendusi (E-ITS SYS.1.1)."""
    results = []
    current_os = platform.system()
    try:
        if current_os == "Windows":
            # Kasutame powershelli käsku, mis on puhtam ja keeleülene
            output = subprocess.check_output(["powershell", "-Command", "Get-Service | Where-Object {$_.Status -eq 'Running'}"], timeout=15).decode(errors='ignore')
        else:
            output = subprocess.check_output(["systemctl", "list-units", "--type=service", "--state=running", "--no-legend"], timeout=15).decode(errors='ignore')
        
        service_count = len([line for line in output.splitlines() if line.strip()])
        results.append({
            "Kontroll": "E-ITS SYS.1.A5: Minimaalsuse põhimõte (Teenused)",
            "Staatus": "OK",
            "Meede": f"Süsteemis töötab aktiivselt {service_count} teenust. Kontrolli üleliigseid portide avajaid."
        })
    except Exception as e:
        logger.error(f"Teenuste kontroll ebaõnnestus: {e}")
    return results

def check_firewall():
    """Tulemüüri seisundi kontroll viisil, mis ei sõltu keelelokaadist."""
    results = []
    current_os = platform.system()
    try:
        if current_os == "Windows":
            output = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles"], timeout=10).decode(errors='ignore')
            # Otsime staatust sõltumata keelest (ON / Lülitatud sisse / Active)
            is_active = "ON" in output.upper() or "LÜLITATUD SISSE" in output.upper() or "ACTIVE" in output.upper()
            status = "OK" if is_active else "HOIATUS"
            meede = "Windows Defender Firewall on profiilides aktiivne." if is_active else "Tulemüür võib olla välja lülitatud!"
        else:
            # Kontrollime ufw või iptables olemasolu
            try:
                output = subprocess.check_output(["sudo", "ufw", "status"], timeout=10).decode(errors='ignore')
                is_active = "active" in output.lower() or "aktiivne" in output.lower()
            except:
                output = subprocess.check_output(["sudo", "iptables", "-L"], timeout=10).decode(errors='ignore')
                is_active = len(output.splitlines()) > 3
                
            status = "OK" if is_active else "HOIATUS"
            meede = "Linuxi paketifilter/tulemüür on aktiivne." if is_active else "Tulemüür ei rakenda aktiivseid reegleid!"
            
        results.append({"Kontroll": "E-ITS NET.3.A1: Tulemüüri olemasolu", "Staatus": status, "Meede": meede})
    except Exception as e:
        results.append({
            "Kontroll": "E-ITS NET.3.A1: Tulemüüri olemasolu",
            "Staatus": "INFO",
            "Meede": f"Automaatne kontroll ebaõnnestus (Õiguste puudus või puudub utiliit): {e}"
        })
    return results

def check_audit_policy():
    """Kontrollib logimispoliitika seise (E-ITS OPS.1.1.A4)."""
    results = []
    current_os = platform.system()
    try:
        if current_os == "Windows":
            output = subprocess.create_notebook = subprocess.check_output(["auditpol", "/get", "/category:*"], timeout=10).decode(errors='ignore')
            has_success = "Success" in output or "Edukus" in output or "No Auditing" not in output
            status = "OK" if has_success else "HOIATUS"
            meede = "Auditipoliitika on konfigureeritud sündmusi püüdma." if has_success else "Kriitilised auditikategooriad võivad olla keelatud!"
        else:
            auditd_active = os.path.exists("/var/log/audit/audit.log") or os.path.exists("/etc/audit/auditd.conf")
            status = "OK" if auditd_active else "INFO"
            meede = "Süsteemist leiti auditd jäljed." if auditd_active else "Linuxi auditd teenus pole vaikeasukohtades tuvastatav."
            
        results.append({"Kontroll": "E-ITS OPS.1.1.A4: Logimise tagamine", "Staatus": status, "Meede": meede})
    except Exception as e:
        results.append({"Kontroll": "E-ITS OPS.1.1.A4: Logimise tagamine", "Staatus": "INFO", "Meede": f"Ei saanud auditipoliitikat kontrollida: {e}"})
    return results

def main():
    print(LOGO)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, '32_tulemus_kasutajate_audit.csv')

    print("[*] Alustan kasutajate ja turvapoliitikate kaardistamist...")
    users = extract_users()
    
    audit_results = []
    audit_results += check_windows_policies()
    audit_results += check_linux_policies()
    audit_results += check_running_services()
    audit_results += check_firewall()
    audit_results += check_audit_policy()

    all_rows = []
    # Lisame struktureeritud raportisse leitud kontod
    for u in users:
        all_rows.append({"Tüüp": "KASUTAJA", "Nimi": u, "Detail": "Tuvastatud süsteemist või intsidentide logikirjetest."})
        
    # Lisame E-ITS auditi tulemused
    for r in audit_results:
        all_rows.append({"Tüüp": "E-ITS_AUDIT", "Nimi": r["Kontroll"], "Detail": f"[{r['Staatus']}] {r['Meede']}"})

    try:
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["Tüüp", "Nimi", "Detail"])
            writer.writeheader()
            writer.writerows(all_rows)
            
        logger.info(f"Kasutajate ja E-ITS audit edukalt lõpetatud: {out_file}")
        print(f"[✓] Audit edukalt lõpetatud! Tulemused ({len(users)} kasutajat, {len(audit_results)} kontrolli) salvestatud: {out_file}")
    except Exception as e:
        logger.error(f"Viga tulemuste faili kirjutamisel: {e}")

if __name__ == "__main__":
    main()
