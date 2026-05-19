#!/usr/bin/env python3
import os
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    in_dir = utils.get_output_dir()
except:
    in_dir = "TULEMUSED"

def filter_security_events():
    out_file = os.path.join(in_dir, '11_tulemus_turvafiltreering.csv')
    critical_ids = [4624, 4625, 4672, 4720, 4732, 4739, 4688, 1102, 4104, 1000, 4648, 4768, 4769, 4776, 4778, 4779, 104, 4719, 1116, 1117, 5007, 4698, 4702, 4699, 5140, 5145]
    
    all_results = []
    if not os.path.exists(in_dir): 
        print(f"[!] Sisendkausta {in_dir} ei eksisteeri.")
        return
        
    csv_files = [f for f in os.listdir(in_dir) if f.startswith('raw_eksport_') and f.endswith('.csv')]
    for file_name in csv_files:
        try:
            with open(os.path.join(in_dir, file_name), mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        if int(row['Id']) in critical_ids:
                            row['OriginalLog'] = file_name
                            all_results.append(row)
                        except: continue
        except Exception as e: 
            print(f"[!] Viga faili {file_name} lugemisel: {e}")
            continue

    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"VALMIS! Kriitilised sündmused filtreeritud: {out_file}")
    else:
        print("[!] Hoiatus: Ühtegi ründe-ID-le vastavat kirjet ei leitud toorandmetest.")

if __name__ == "__main__":
    filter_security_events()
