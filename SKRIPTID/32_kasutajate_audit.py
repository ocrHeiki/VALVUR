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
    return
