#!/usr/bin/env python3
import os
import sys
import csv
from difflib import SequenceMatcher

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    in_dir = utils.get_output_dir()
except:
    in_dir = "TULEMUSED"

def fuzzy_match(a, b):
    return SequenceMatcher(None, a, b).ratio()

def search_suspicious_keywords():
    out_file = os.path.join(in_dir, '12_tulemus_kahtlased_marksonad.csv')
    attack_mapping = {"mimikatz": ("T1003", "Credential Dumping"), "whoami": ("T1033", "Discovery"), "vssadmin": ("T1490", "Ransomware")}
    all_results = []
    
    if not os.path.exists(in_dir): return
    filtered = os.path.join(in_dir, '11_tulemus_turvafiltreering.csv')
    
    if os.path.exists(filtered):
        csv_files = ['11_tulemus_turvafiltreering.csv']
    else:
        csv_files = [f for f in os.listdir(in_dir) if f.startswith('raw_eksport_') and f.endswith('.csv')]
        
    for file_name in csv_files:
        try:
            with open(os.path.join(in_dir, file_name), mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    msg = row.get('Message', '').lower()
                    for word, info in attack_mapping.items():
                        if word in msg or any(fuzzy_match(word, w) > 0.7 for w in msg.split() if len(w) > 3):
                            row['MatchedKeyword'] = word
                            row['MITRE_ID'] = info[0]
                            row['Attack_Type'] = info[1]
                            all_results.append(row)
                            break
        except: continue

    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"[+] Tuvastati {len(all_results)} ründeindikaatorit märksõnade abil: {out_file}")
    else:
        print("[!] Märksõnade põhjal ühtegi rünnet ei tuvastatud.")

if __name__ == "__main__":
    search_suspicious_keywords()
