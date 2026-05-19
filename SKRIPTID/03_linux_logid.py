#!/usr/bin/env python3
import os
import sys
import csv
import re

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("LINUX_CSV")
    out_dir = utils.get_output_dir()
except:
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

def parse_linux_logs():
    print(LOGO)
    os.makedirs(out_dir, exist_ok=True)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Universaalne otsing: kontrollib reaalselt eksisteerivaid asukohti
    base_search_dirs = [
        "/var/log",
        os.path.join(base_dir, "..", "LOGID"),
        os.path.join(base_dir, "LOGID"),
        base_dir # Fallback: otsi otse skripti jooksvast kaustast
    ]
    
    ignore_extensions = ('.gz', '.xz', '.zip', '.1', '.2', '.3', '.wtmp', '.btmp', '.lastlog', '.journal', '.csv', '.py', '.txt')
    headers = ['TimeCreated', 'Id', 'LevelDisplayName', 'Message', 'MachineName', 'RecordId']
    count = 0
    log_files_to_process = []

    # 1. Samm: Kogume kokku kõik potentsiaalsed Linuxi logifailid rekursiivselt
    for d in base_search_dirs:
        if not os.path.exists(d): continue
        for root, dirs, files in os.walk(d):
            if "TULEMUSED" in root: continue # Ära skaneeri väljundkausta
            for file in files:
                if file.endswith(ignore_extensions) or file.startswith('.'):
                    continue
                # Kontrollime faili sisu kiirelt üle, et tegu poleks Windowsi EVTX-iga
                if file.lower().endswith('.evtx'):
                    continue
                log_files_to_process.append(os.path.join(root, file))

    # Eemaldame duplikaadid, kui kaustad kattuvad
    log_files_to_process = list(set(log_files_to_process))

    if not log_files_to_process:
        print("[-] Ühtegi tekstipõhist Linuxi logifaili ei leitud.")
        return

    # 2. Samm: Töötleme leitud failid läbi
    for log_path in log_files_to_process:
        # Puhastame failinime platvormiüleselt (eemaldame mõlemad kaldkriipsud ja kettatähised)
        clean_name = log_path.replace(':', '').replace('\\', '_').replace('/', '_')
        out_csv = os.path.join(out_dir, f"raw_eksport_linux_{clean_name}.csv")
        
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
                    if len(parts) >= 5 and re.match(r'^[A-Z][a-z]{2}$', parts[0]) and re.match(r'^\d+$', parts[1]):
                        time_str = f"{parts[0]} {parts[1]} {parts[2]}"
                        machine = parts[3]
                        msg = parts[4]
                    else:
                        # Fallback (nt Audit logid, veebiserverid või ilma päiseta read)
                        time_str = "Unknown"
                        machine = "Unknown"
                        msg = line

                    event_id = "1000"
                    
                    # Turvaintsidentide kaardistamine (ühtlustame Windowsi Event ID-dega)
                    if any(k in msg for k in ["Accepted password", "session opened", "Accepted publickey"]): 
                        event_id = "4624" # Edukas sisselogimine
                    elif any(k in msg for k in ["Failed password", "authentication failure", "FAILED su"]): 
                        event_id = "4625" # Ebaõnnestunud sisselogimine
                    elif any(k in msg for k in ["new user", "useradd", "groupadd"]): 
                        event_id = "4720" # Kasutaja/grupi loomine
                    elif "COMMAND=" in msg and "sudo" in line.lower():
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
            print(f"[!] Õigused puuduvad faili lugemiseks: {log_path}")
        except Exception as e:
            print(f"[!] Viga faili {log_path} töötlemisel: {e}")
