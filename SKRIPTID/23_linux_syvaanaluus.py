#!/usr/bin/env python3
"""
###############################################################################
#                                                                             #
#   █████   █████             ████                                            #
#  ▒▒███   ▒▒███             ▒▒███                                            #
#   ▒███    ▒███   ██████    ▒███  █████ █████ █████ ████ ████████            #
#   ▒███    ▒███  ▒▒▒▒▒███   ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███           #
#   ▒▒███   ███    ███████   ▒███  ▒███  ▒███  ▒███ ▒███  ▒███ ▒▒▒            #
#    ▒▒▒█████▒    ███▒▒███   ▒███  ▒▒███ ███   ▒███ ▒███  ▒███                #
#      ▒▒███     ▒▒████████ █████   ▒▒█████    ▒▒████████ █████               #
#       ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒     ▒▒▒▒▒      ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                #
#                                                                             #
#   =======================================================================   #
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  23_linux_syvaanaluus.py                              |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Linuxi autentimislogide (auth/secure) süvaanalüüs,   |   #
#   |                kellamanipulatsiooni ja SSH rünnete tuvastus.        |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import re
import csv
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

LOGO = r"""
###############################################################################
#                                                                             #
#   █████   █████             ████                                            #
#  ▒▒███   ▒▒███             ▒▒███                                            #
#   ▒███    ▒███   ██████    ▒███  █████ █████ █████ ████ ████████            #
#   ▒███    ▒███  ▒▒▒▒▒███   ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███           #
#   ▒▒███   ███    ███████   ▒███  ▒███  ▒███  ▒███ ▒███  ▒███ ▒▒▒            #
#    ▒▒▒█████▒    ███▒▒███   ▒███  ▒▒███ ███   ▒███ ▒███  ▒███                #
#      ▒▒███     ▒▒████████ █████   ▒▒█████    ▒▒████████ █████               #
#       ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒     ▒▒▒▒▒      ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                #
#                                                                             #
###############################################################################
"""

logger = utils.setup_logging("LINUX_SYVA")

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
                # 1. Kontrolli null-baite (tüüpiline märk logi purustamisest ründaja poolt)
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
                        # Kuna syslogis pole aastat, määrame praeguse aasta (2026)
                        current_year = datetime.now().year
                        dt = datetime.strptime(f"{current_year} {time_str}", "%Y %b %d %H:%M:%S")
                        
                        if last_dt:
                            diff = (dt - last_dt).total_seconds()
                            
                            # Kui aeg läheb tagasi (ja pole aasta vahetus), on logi muudetud või rünnatud
                            if diff < 0:
                                anomalies.append({
                                    "EventID": "TAMPER_TIME_INVERSION",
                                    "Kirjeldus": "Kronoloogiline anomaalia (Aeg liigub tagasi!)",
                                    "User": "SYSTEM", "SourceIP": "LOCAL",
                                    "Detail": f"Rida {line_num}: Aeg hüppas tagasi! {last_dt} -> {dt}"
                                })
                            # Tõstame piiri 12 tunni peale (43200 sek), et vähendada tühiseid logipragusid
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
    Eraldab kasutaja ja IP-aadressi struktureeritud kujul.
    """
    results = []
    
    # Laiendatud regex mustrid koos nimeliste gruppidega (?P<user>...) lihtsamaks parsimiseks
    patterns = [
        # Edukas sisselogimine parooliga või võtmega
        (r'Accepted\s+(password|publickey)\s+for\s+(\S+)\s+from\s+(\S+)\s+port', '4624', 'Edukas SSH sisselogimine'),
        # Ebaõnnestunud parool
        (r'Failed\s+password\s+for\s+(invalid user\s+)?(\S+)\s+from\s+(\S+)\s+port', '4625', 'Ebaõnnestunud parool'),
        # Olematu kasutajaga õngitsemine (Brute Force indikaator)
        (r'Invalid\s+user\s+(\S+)\s+from\s+(\S+)\s+port', '4625', 'SSH rünre (Olematu kasutaja)'),
        # Ründaja suleti enne autentimist tagant ära
        (r'Connection\s+closed\s+by\s+authenticating\s+user\s+(\S+)\s+(\S+)\s+port', '4625', 'SSH ühendus katkes keset autentimist'),
        # Sudo käsud (Privilege Escalation jälgimine)
        (r'sudo:\s+(\S+)\s+:\s+TTY=.*\s+;\s+USER=(\S+)\s+;\s+COMMAND=(.*)', '4688', 'Sudo käsu käivitamine')
    ]
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_str = line.strip()
                for pattern, event_id, desc in patterns:
                    m = re.search(pattern, line_str, re.IGNORECASE)
                    if m:
                        # Vaikimisi väärtused
                        user, source_ip = "UNKNOWN", "LOCAL"
                        
                        # Võtame väärtused vastavalt leitud reegli gruppidele
                        if event_id == '4624': # Accepted
                            user = m.group(2)
                            source_ip = m.group(3)
                        elif 'Failed' in pattern or 'Invalid' in pattern:
                            user = m.group(m.lastindex - 1)
                            source_ip = m.group(m.lastindex)
                        elif 'sudo' in pattern:
                            user = f"{m.group(1)} -> {m.group(2)}" # kes -> kelleks
                            source_ip = "LOCAL"
                            desc = f"Sudo: {m.group(3)[:50]}" # Lisame käsu alguse kirjelduseks
                        
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
    out_dir = utils.get_output_dir()
    out_file = os.path.join(out_dir, '23_tulemus_linux_syvaanaluus.csv')
    
    # Otsime läbi potentsiaalsed logifailid (nii Ubuntu kui CentOS süsteemid)
    possible_paths = [
        "/var/log/auth.log",   # Ubuntu/Debian
        "/var/log/secure",     # CentOS/RHEL/Rocky
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LOGID", "auth.log"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LOGID", "secure")
    ]
    
    active_logs = [p for p in possible_paths if os.path.exists(p)]
    
    if not active_logs:
        logger.error("[-] Ühtegi autentimislogi (auth.log / secure) ei leitud!")
        return

    all_results = []
    
    for log_path in active_logs:
        logger.info(f"[+] Alustan faili analüüsi: {log_path}")
        
        # 1. Käivita SSH/Sudo sündmuste analüüs
        all_results += analyze_ssh_logins(log_path)
        
        # 2. Käivita logi tervikluse kontroll (tampering)
        all_results += detect_log_tampering(log_path)

    if all_results:
        # Salvestame tulemused CSV-sse. Päises on nüüd eraldi User ja SourceIP!
        headers = ["EventID", "Kirjeldus", "User", "SourceIP", "Detail"]
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_results)
        logger.info(f"[✓] Linuxi süvaanalüüs edukalt lõpetatud: {out_file} ({len(all_results)} leidu)")
    else:
        logger.warning("[-] Analüüsi käigus ei tuvastatud ühtegi relevantset sündmust.")

if __name__ == "__main__":
    main()
