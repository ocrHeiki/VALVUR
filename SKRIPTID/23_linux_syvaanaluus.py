#!/usr/bin/env python3
import os
import sys
import re
import csv
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("LINUX_SYVA")
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
#   █████   █████             ████                                             #
#  ▒▒███   ▒▒███             ▒▒███                                             #
#   ▒███    ▒███   ██████    ▒███  █████ █████ █████ ████ ████████             #
#   ▒███    ▒███  ▒▒▒▒▒███   ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███            #
#   ▒▒███   ███    ███████   ▒███  ▒███  ▒███  ▒███ ▒███  ▒███ ▒▒▒             #
#    ▒▒▒█████▒    ███▒▒███   ▒███  ▒▒███ ███    ▒███ ▒███  ▒███                 #
#      ▒▒███     ▒▒████████ █████  ▒▒█████     ▒▒████████ █████                #
#       ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒    ▒▒▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                 #
#                                                                             #
###############################################################################
"""

def detect_log_tampering(log_path):
    """
    Tuvastab anomaaliad logifailis:
    1. Kronoloogiline tagasihüpe (kellaajaga manipuleerimine / log injection)
    2. Null-baidid (faili lohakas kustutamine/wiping)
    3. Massiivsed logipraod (rohkem kui 12 tundi tühjust aktiivses logis)
    """
    anomalies = []
    pattern = re.compile(r'^(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})')
    last_dt = None
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                # 1. Kontrolli null-baite
                if '\x00' in line:
                    anomalies.append({
                        "EventID": "TAMPER_NULL",
                        "Kirjeldus": "Tuvastati NULL-baidid (Logi manipuleerimine/rikkumine)",
                        "User": "UNKNOWN", "SourceIP": "UNKNOWN",
                        "Detail": f"Rida {line_num} sisaldab binaarset tühjust."
                    })
                    continue
                
                m = pattern.match(line)
                if m:
                    time_str = m.group(1)
                    try:
                        current_year = datetime.now().year
                        dt = datetime.strptime(f"{current_year} {time_str}", "%Y %b %d %H:%M:%S")
                        
                        if last_dt:
                            diff = (dt - last_dt).total_seconds()
                            
                            # Kui aeg läheb tagasi, on logi manipuleeritud
                            if diff < 0:
                                anomalies.append({
                                    "EventID": "TAMPER_TIME_INVERSION",
                                    "Kirjeldus": "Kronoloogiline anomaalia (Aeg liigub tagasi!)",
                                    "User": "SYSTEM", "SourceIP": "LOCAL",
                                    "Detail": f"Rida {line_num}: Aeg hüppas tagasi! {last_dt} -> {dt}"
                                })
                            # Logipraod (rohkem kui 12 tundi)
                            elif diff > 43200:
                                anomalies.append({
                                    "EventID": "TAMPER_GAP",
                                    "Kirjeldus": "Kriitiline logipraeg (Süsteem oli pikalt pime)",
                                    "User": "SYSTEM", "SourceIP": "LOCAL",
                                    "Detail": f"Logis on auk: {last_dt} kuni {dt} ({diff/3600:.1f} tundi)"
                                })
                        last_dt = dt
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Logi tervikluse kontroll nurjus {log_path}: {e}")
    
    return anomalies

def analyze_ssh_logins(log_path):
    """
    Süvaanalüüsib SSH ja õiguste kõrgendamise kirjeid.
    """
    results = []
    
    patterns = [
        (r'Accepted\s+(password|publickey)\s+for\s+(\S+)\s+from\s+(\S+)\s+port', '4624', 'Edukas SSH sisselogimine'),
        (r'Failed\s+password\s+for\s+(invalid user\s+)?(\S+)\s+from\s+(\S+)\s+port', '4625', 'Ebaõnnestunud parool'),
        (r'Invalid\s+user\s+(\S+)\s+from\s+(\S+)\s+port', '4625', 'SSH rünre (Olematu kasutaja)'),
        (r'Connection\s+closed\s+by\s+authenticating\s+user\s+(\S+)\s+(\S+)\s+port', '4625', 'SSH ühendus katkes keset autentimist'),
        (r'sudo:\s+(\S+)\s+:\s+TTY=.*\s+;\s+USER=(\S+)\s+;\s+COMMAND=(.*)', '4688', 'Sudo käsu käivitamine')
    ]
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_str = line.strip()
                for pattern, event_id, desc in patterns:
                    m = re.search(pattern, line_str, re.IGNORECASE)
                    if m:
                        user, source_ip = "UNKNOWN", "LOCAL"
                        try:
                            if event_id == '4624':
                                user = m.group(2)
                                source_ip = m.group(3)
                            elif 'Failed' in pattern or 'Invalid' in pattern or 'Connection' in pattern:
                                # Turvaline viis indeksite leidmiseks ilma kokku jooksmata
                                idx = m.lastindex
                                if idx and idx >= 2:
                                    source_ip = m.group(idx)
                                    user = m.group(idx - 1)
                            elif 'sudo' in pattern:
                                user = f"{m.group(1)} -> {m.group(2)}"
                                source_ip = "LOCAL"
                                desc = f"Sudo: {m.group(3)[:50]}"
                        except Exception:
                            # Kui parsimine ebaõnnestub, säilitame vaikimisi väärtused, et logirida kaduma ei läheks
                            pass
                        
                        results.append({
                            "EventID": event_id,
                            "Kirjeldus": desc,
                            "User": user,
                            "SourceIP": source_ip,
                            "Detail": line_str
                        })
                        break
    except Exception as e:
        logger.error(f"SSH sündmuste analüüs nurjus: {e}")
    return results

def main():
    print(LOGO)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, '23_tulemus_linux_syvaanaluus.csv')
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Universaalsed ja paindlikud asukohad
    possible_paths = [
        "/var/log/auth.log",
        "/var/log/secure",
        os.path.join(base_dir, "..", "LOGID", "auth.log"),
        os.path.join(base_dir, "..", "LOGID", "secure"),
        os.path.join(base_dir, "LOGID", "auth.log"),
        os.path.join(base_dir, "LOGID", "secure"),
        os.path.join(base_dir, "auth.log"),
        os.path.join(base_dir, "secure")
    ]
    
    active_logs = [p for p in possible_paths if os.path.exists(p)]
    # Eemaldame topeltväärtused
    active_logs = list(set(active_logs))
    
    if not active_logs:
        logger.warning("[-] Ühtegi autentimislogi (auth.log / secure) ei leitud analüüsimiseks!")
        return

    all_results = []
    for log_path in active_logs:
        logger.info(f"[+] Alustan faili analüüsi: {log_path}")
        all_results += analyze_ssh_logins(log_path)
        all_results += detect_log_tampering(log_path)

    if all_results:
        headers = ["EventID", "Kirjeldus", "User", "SourceIP", "Detail"]
        try:
            with open(out_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(all_results)
            logger.info(f"[✓] Linuxi süvaanalüüs lõpetatud: {out_file} ({len(all_results)} leidu)")
        except Exception as e:
            logger.error(f"❌ Viga tulemuste faili kirjutamisel: {e}")
    else:
        logger.warning("[-] Analüüsi käigus ei tuvastatud ühtegi anomaaliat ega sündmust.")

if __name__ == "__main__":
    main()
