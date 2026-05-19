#!/usr/bin/env python3
import os
import csv
import platform

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

def live_system_scan():
    print("[*] Alustan süsteemi reaalajas kontrolli...")
    suspicious = []
    exts = ('.exe', '.ps1', '.sh', '.elf', '.bat', '.vbs')
    is_win = platform.system() == "Windows"
    
    # Määrame kontrollitavad teekonnad dünaamiliselt
    paths = [os.environ.get('TEMP', 'C:\\Windows\\Temp'), 'C:\\Users\\Public'] if is_win else ['/tmp', '/var/tmp', '/dev/shm']
    
    for p in paths:
        if not os.path.exists(p): 
            print(f"[-] Kausta ei leitud, hüppan üle: {p}")
            continue
        print(f"[+] Skaneerin kausta: {p}")
        
        # Kasutame try-except plokki, et vältida õiguste (Permission Error) tõttu kokkujooksmist
        try:
            for root, dirs, files in os.walk(p):
                for f in files:
                    if f.lower().endswith(exts):
                        full_path = os.path.join(root, f)
                        suspicious.append({
                            "Type": "LIVE_FILE", 
                            "Path": full_path, 
                            "Reason": "Käivitatav või skriptifail ajutises/avalikus kaustas"
                        })
        except Exception as e:
            print(f"[!] Viga kausta {p} skaneerimisel: {e}")
            continue
            
    return suspicious

def main():
    print(LOGO)
    # Tagame, et väljundkaust on alati olemas
    out_dir = os.environ.get("VALVUR_OUT", "TULEMUSED")
    os.makedirs(out_dir, exist_ok=True)
    
    findings = live_system_scan()
    out_file = os.path.join(out_dir, '22_tulemus_kahtlased_failid.csv')
    
    try:
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['Type', 'Path', 'Reason'])
            writer.writeheader()
            for fnd in findings: 
                writer.writerow(fnd)
        print(f"[+] VALMIS! Leiti {len(findings)} kahtlast viidet. Tulemus: {out_file}")
    except Exception as e:
        print(f"❌ [VIGA] Tulemuste salvestamine ebaõnnestus: {e}")

if __name__ == "__main__":
    main()
