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
#   |   FAILI NIMI:  51_koond_ajajoon.py                                  |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Ühtse kronoloogilise ajajoone (Super Timeline) looja |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import csv
import re
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("AJAJOON")
    out_dir = utils.get_output_dir()
except Exception:
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()
    out_dir = "TULEMUSED"

LOGO = r"""
###############################################################################
#                 VALVUR FAAS 5: UNIFITSEERITUD AJAJOONE GENERAATOR          #
###############################################################################
"""

def normalize_timestamp(ts_string):
    """
    Normaliseerib erinevad logide ajatemplid ühtseks datetime objektiks,
    et tagada absoluutne kronoloogiline täpsus sorteerimisel.
    """
    if not ts_string:
        return datetime.min
        
    ts_string = str(ts_string).strip()
    
    # Puhastame levinud XML/JSON sümbolid (nt 'T' või 'Z' lõpud) ühilduvuse tagamiseks
    clean_ts = ts_string.replace('T', ' ').replace('Z', '')
    # Eemaldame millisekundite ülejäägid, kui need on liiga pikad (.123456)
    clean_ts = re.sub(r'\.\d+', '', clean_ts)
    
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d.%m.%Y %H:%M:%S",
        "%Y-%m-%d",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_ts, fmt)
        except ValueError:
            continue
            
    # Kui ükski formaat ei sobi, proovime leida reeglipärast kuupäeva tekstist
    try:
        match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', clean_ts)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
    except Exception:
        pass

    return datetime.min


def main():
    print(LOGO)
    out_file = os.path.join(out_dir, '51_tulemus_unified_timeline.csv')
    all_events = []
    all_keys = set()

    # Otsime üles kõik vahetulemuste ja algsete eksportide failid
    csv_files = [f for f in os.listdir(out_dir) if f.endswith('.csv') and f != '51_tulemus_unified_timeline.csv']
    
    print(f"[*] Alustan logiallikate liitmist kataloogist: {out_dir}")
    
    for csv_file in csv_files:
        file_path = os.path.join(out_dir, csv_file)
        # Määrame allika loetavama nime (eemaldame prefiksid)
        allika_nimi = csv_file.replace('raw_eksport_', '').replace('_tulemus_', '')
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    continue
                    
                for row in reader:
                    # Lisame forensiliselt kriitilise allikaviite igale reale
                    row['_Logiallikas'] = allika_nimi
                    all_events.append(row)
                    # Kogume dünaamiliselt kokku kõik võimalikud veerud üle kõigi failide
                    all_keys.update(row.keys())
                    
            print(f"    [+] Liidetud allikas: {csv_file} ({len(all_events)} sündmust kokku)")
        except Exception as e:
            logger.error(f"Viga CSV faili {csv_file} töötlemisel: {e}")

    if not all_events:
        logger.warning("Ühtegi sündmust ei leitud liitmiseks. Ajajoont ei loodud.")
        print("[-] Viga: Liidetavaid andmeid ei leitud.")
        return

    print("[*] Sorteerin sündmusi reaalajas normaliseeritud ajatemplite alusel...")
    # Sorteerimine kasutab intelligentset kuupäeva parsimist, mitte toorest stringivõrdlust
    all_events.sort(key=lambda r: normalize_timestamp(r.get('TimeCreated') or r.get('Aeg') or r.get('Timestamp', '')))

    # Struktureerime väljundi veerud nii, et kõige olulisem info oleks alati vasakul pool
    core_fields = ['TimeCreated', 'Aeg', 'Timestamp', '_Logiallikas', 'EventID', 'Sündmus_ID', 'User', 'Kasutaja', 'Message', 'Detail']
    
    # Sorteerime ülejäänud dünaamilised veerud tähestikulisse järjekorda ja liidame struktuuri
    ordered_fields = [f for f in core_fields if f in all_keys]
    remaining_fields = sorted(list(all_keys - set(ordered_fields)))
    final_fieldnames = ordered_fields + remaining_fields

    try:
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=final_fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(all_events)
            
        logger.info(f"Koond-ajajoon (Super Timeline) edukalt loodud: {out_file} ({len(all_events)} sündmust)")
        print(f"\n[✓] Kronoloogiline master-ajajoon salvestatud: {out_file}")
    except Exception as e:
        logger.error(f"Ajajoone faili kirjutamine nurjus: {e}")
        print(f"[-] Viga faili salvestamisel: {e}")


if __name__ == "__main__":
    main()
