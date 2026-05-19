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
#   |   FAILI NIMI:  03_linux_logid.py                                    |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Linuxi logide rekursiivne kogumine ja parsimine.     |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import csv
import re

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

logger = utils.setup_logging("LINUX_CSV")

def parse_linux_logs():
    print(LOGO)
    out_dir = utils.get_output_dir()
    if not os.path.exists(out_dir): os.makedirs(out_dir, exist_ok=True)

    # Põhikaustad, mida uurida
    base_search_dirs = [
        "/var/log", 
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "LOGID")
    ]
    
    # Faililaiendid, mida me EI taha avada (arhiivid, pööratud logid, binaarid)
    ignore_extensions = ('.gz', '.xz', '.zip', '.1', '.2', '.3', '.wtmp', '.btmp', '.lastlog', '.journal')

    headers = ['TimeCreated', 'Id', 'LevelDisplayName', 'Message', 'MachineName', 'RecordId']
    count = 0

    log_files_to_process = []

    # 1. Samm: Kogume kokku kõik potentsiaalsed logifailid rekursiivselt
    for d in base_search_dirs:
        if not os.path.exists(d): continue
        for root, dirs, files in os.walk(d):
            for file in files:
                if file.endswith(ignore_extensions):
                    continue
                log_files_to_process.append(os.path.join(root, file))

    if not log_files_to_process:
        print("[-] Ühtegi tekstipõhist logifaili ei leitud.")
        return

    # 2. Samm: Töötleme leitud failid läbi
    for log_path in log_files_to_process:
        # Puhastame failinime väljundi jaoks (nt /var/log/nginx/access.log -> nginx_access.log)
        safe_name = log_path.replace('/var/log/', '').replace('/', '_')
        out_csv = os.path.join(out_dir, f"raw_eksport_linux_{safe_name}.csv")
        
        print(f"Konverteerin: {log_path} -> {out_csv}")
        
        try:
            with open(log_path, 'r', encoding='utf-8', errors='ignore') as f_in, \
                 open(out_csv, 'w', newline='', encoding='utf-8') as f_out:
                
                writer = csv.DictWriter(f_out, fieldnames=headers)
                writer.writeheader()
                
                for i, line in enumerate(f_in):
                    line = line.strip()
                    if not line: continue
                    
                    parts = line.split(maxsplit=4)
                    
                    # Kontrollime, kas rida vastab klassikalisele syslogi formaadile (Kuu Päev Kell)
                    # nt: "May 19 12:00:00"
                    if len(parts) >= 5 and re.match(r'^[A-Z][a-z]{2}$', parts[0]) and re.match(r'^\d+$', parts[1]):
                        time_str = f"{parts[0]} {parts[1]} {parts[2]}"
                        machine = parts[3]
                        msg = parts[4]
                    else:
                        # Fallback (nt Nginx, Apache, Audit logide jaoks)
                        time_str = "Unknown"
                        machine = "Unknown"
                        msg = line

                    event_id = "1000"
                    
                    # Turvaintsidentide kaardistamine (ühtlustame Windowsi Event ID-dega)
                    if "Accepted password" in msg or "session opened" in msg or "Accepted publickey" in msg: 
                        event_id = "4624" # Edukas sisselogimine
                    elif "Failed password" in msg or "authentication failure" in msg or "FAILED su" in msg: 
                        event_id = "4625" # Ebaõnnestunud sisselogimine
                    elif "new user" in msg or "useradd" in msg: 
                        event_id = "4720" # Kasutaja loomine
                    elif "COMMAND=" in msg and "sudo" in line:
                        event_id = "4688" # Protsessi loomine / privilegeeritud käsk

                    writer.writerow({
                        'TimeCreated': time_str, 
                        'Id': event_id, 
                        'LevelDisplayName': 'Info', 
                        'Message': msg, 
                        'MachineName': machine, 
                        'RecordId': str(i)
                    })
                    count += 1
                    
        except PermissionError:
            logger.warning(f"Õigused puuduvad faili lugemiseks: {log_path} (Kasuta 'sudo')")
        except Exception as e:
            logger.error(f"Viga faili {log_path} töötlemisel: {e}")
            continue

    print(f"[+] Kokku konverteeritud {count} logirida.")

if __name__ == "__main__":
    parse_linux_logs()
