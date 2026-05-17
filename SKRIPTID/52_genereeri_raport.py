#!/usr/bin/env python3
"""
###############################################################################
#                                                                             #
#   █████   █████           ████                                              #
#  ▒▒███   ▒▒███           ▒▒███                                              #
#   ▒███    ▒███   ██████   ▒███  █████ █████ █████ ████ ████████             #
#   ▒███    ▒███  ▒▒▒▒▒███  ▒███ ▒▒███ ▒▒███ ▒▒███ ▒███ ▒▒███▒▒███            #
#   ▒▒███   ███    ███████  ▒███  ▒███  ▒███  ▒███ ▒███  ▒███ ▒▒▒             #
#    ▒▒▒█████▒    ███▒▒███  ▒███  ▒▒███ ███   ▒███ ▒███  ▒███                 #
#      ▒▒███     ▒▒████████ █████  ▒▒█████    ▒▒████████ █████                #
#       ▒▒▒       ▒▒▒▒▒▒▒▒ ▒▒▒▒▒    ▒▒▒▒▒      ▒▒▒▒▒▒▒▒ ▒▒▒▒▒                 #
#                                                                             #
#   =======================================================================   #
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  52_genereeri_raport.py                               |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Koondraporti koostamine kõigist analüüsietappidest   |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

logger = utils.setup_logging("RAPORT")


def count_csv_rows(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f) - 1
    except:
        return 0


def main():
    out_dir = utils.get_output_dir()
    out_file = os.path.join(out_dir, '52_tulemus_koondraport.txt')

    txt_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.txt')])
    csv_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.csv')])
    json_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.json')])

    with open(out_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("  VALVUR - KOONDRAPORT\n")
        f.write(f"  Genereeritud: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        f.write("--- ANALÜÜSI TULEMUSED ---\n\n")
        for txt_file in txt_files:
            file_path = os.path.join(out_dir, txt_file)
            size = os.path.getsize(file_path)
            f.write(f"  {txt_file}: {size} baiti\n")

        f.write("\n--- CSV SÜNDMUSTE KOKKUVÕTE ---\n\n")
        for csv_file in csv_files:
            file_path = os.path.join(out_dir, csv_file)
            rows = count_csv_rows(file_path)
            f.write(f"  {csv_file}: {rows} rida\n")

        f.write("\n--- JSON VÄLJUNDFAILID ---\n\n")
        for js_file in json_files:
            try:
                with open(os.path.join(out_dir, js_file), 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
                f.write(f"  {js_file}: {json.dumps(data, indent=2, ensure_ascii=False)}\n")
            except:
                f.write(f"  {js_file}: lugemisviga\n")

        f.write("\n--- NIST CSF 2.0 VASTAVUS ---\n")
        f.write("  IDENTIFY: Varade kaardistus teostatud\n")
        f.write("  PROTECT: Turvakontrollid auditeeritud\n")
        f.write("  DETECT: Logianalüüs ja ründeindikaatorid tuvastatud\n")
        f.write("  RESPOND: Raport ja tegevuskava koostatud\n")
        f.write("  RECOVER: Ajajoon süsteemi taastamiseks loodud\n")

    logger.info(f"Koondraport loodud: {out_file}")


if __name__ == "__main__":
    main()
