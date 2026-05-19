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
#   |   FAILI NIMI:  52_genereeri_raport.py                               |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Koondraporti koostamine ja NIST CSF 2.0 kaardistus   |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import json
import csv
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("RAPORT")
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
#                  VALVUR - DIGITAALFORENSIKA KOONDRAPORT                     #
###############################################################################
"""

def count_csv_rows(file_path):
    """Loeb turvaliselt kokku CSV faili andmeridade arvu (ilma päiseta)."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            return max(0, sum(1 for _ in reader) - 1)
    except Exception:
        return 0

def summarize_json(file_path):
    """Annab JSON faili sisust intelligentse struktuurse kokkuvõtte ilma mälu koormamata."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        if isinstance(data, dict):
            keys_summary = ", ".join(list(data.keys())[:5])
            if len(data.keys()) > 5:
                keys_summary += "..."
            return f"Objekt (Atribuudid: {len(data.keys())} tk -> {keys_summary})"
        elif isinstance(data, list):
            return f"Massiiv ({len(data)} kirjet/indikaatorit)"
        return "Tundmatu JSON struktuur"
    except Exception as e:
        return f"Viga struktuuri lugemisel: {e}"

def main():
    print(LOGO)
    # Kasutame .md laiendit puhta ja loetava hierarhia tagamiseks
    out_file = os.path.join(out_dir, '52_tulemus_koondraport.md')

    # Filtreerime failide loendist välja raporti enda, et vältida andmereostust ja lõputuid tsükleid
    all_files = os.listdir(out_dir)
    txt_files = sorted([f for f in all_files if f.endswith('.txt') and 'koondraport' not in f])
    csv_files = sorted([f for f in all_files if f.endswith('.csv') and 'koondraport' not in f])
    json_files = sorted([f for f in all_files if f.endswith('.json')])

    # Dünaamiline indikaatorite kontroll NIST CSF 2.0 ja E-ITS sidumiseks
    has_triage = any('turvafiltreering' in f or 'unified_timeline' in f for f in csv_files)
    has_audit = any('audit' in f for f in csv_files or f in txt_files)
    has_timeline = any('unified_timeline' in f for f in csv_files)

    print(f"[*] Koondan andmeid kataloogist: {out_dir} ...")

    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write("# VALVUR — INTSIDENDI SÜVAANALÜÜSI KOONDRAPORT\n\n")
            f.write(f"**Genereerimise aeg:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
            f.write(f"**Uurimise koodnimetus:** VALVUR-DFIR-{datetime.now().strftime('%Y%m%d')}\n\n")
            f.write("---\n\n")

            ## 1. Täitevkokkuvõte
            f.write("## 1. Täitevkokkuvõte (Executive Summary)\n")
            f.write("Käesolev raport koondab süsteemi VALVUR poolt tuvastatud digitaalforensika (DFIR) leiud. ")
            f.write("Analüüsitud on süsteemipoliitikaid, kasutajakontosid ning kogutud sündmuslogisid, ")
            f.write("et tuvastada anomaaliaid ja ründemustreid.\n\n")

            ## 2. CSV Sündmuslogide ja Triage statistika
            f.write("## 2. Tuvastatud sündmused ja logiallikad\n")
            f.write("Süsteemi poolt töödeldud ja filtreeritud struktureeritud andmemahtude kokkuvõte:\n\n")
            f.write("| Logifail / Raport | Andmeridade arv | Olek / Tähendus |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            for csv_file in csv_files:
                file_path = os.path.join(out_dir, csv_file)
                rows = count_csv_rows(file_path)
                status = "Kriitiline" if rows > 0 and "tulemus" in csv_file else "Algne andmestik"
                f.write(f"| `{csv_file}` | {rows} rida | {status} |\n")
            f.write("\n")

            ## 3. Tekstipõhised logid ja uurimismärkmed
            f.write("## 3. Analüüsi tekstiväljundid ja uurimismärkmed\n")
            if txt_files:
                for txt_file in txt_files:
                    file_path = os.path.join(out_dir, txt_file)
                    size_kb = round(os.path.getsize(file_path) / 1024, 2)
                    f.write(f"* **`{txt_file}`** ({size_kb} KB) — Staatiline raport või logiväljavõte.\n")
            else:
                f.write("*Tekstipõhiseid eraldiseisvaid uurimismärkmeid ei tuvastatud.*\n")
            f.write("\n")

            ## 4. JSON Struktuuri ja IOC kokkuvõte
            f.write("## 4. Süsteemi JSON konfiguratsioonid ja IOC indikaatorid\n")
            if json_files:
                for js_file in json_files:
                    summary = summarize_json(os.path.join(out_dir, js_file))
                    f.write(f"* **`{js_file}`**: {summary}\n")
            else:
                f.write("*Struktureeritud JSON ohuluure (Threat Intel) faile ei leitud.*\n")
            f.write("\n")

            ## 5. NIST CSF 2.0 ja E-ITS vastavushindamine
            f.write("## 5. Rahvusvaheliste raamistike ja E-ITS vastavushindamine\n")
            f.write("Tööriista VALVUR läbiviidud kontrollide dünaamiline vastavus küberturvalisuse standarditele:\n\n")
            
            # IDENTIFY
            f.write(f"* **IDENTIFY (Tuvasta):** {'[TÄIDETUD] Kasutajakontod ja süsteemi põhikomponendid on kaardistatud.' if has_audit else '[PUUDULIK] Süsteemi varasid ja kasutajaid ei auditeeritud.'}\n")
            # PROTECT
            f.write(f"* **PROTECT (Kaitse):** {'[TÄIDETUD] Tulemüürireeglid, paroolipoliitikad ja aktiivsed teenused on kontrollitud vastavalt E-ITS nõuetele.' if has_audit else '[PUUDULIK] Kaitsesätteid ja süsteemipoliitikaid pole kontrollitud.'}\n")
            # DETECT
            f.write(f"* **DETECT (Tuvasta ründed):** {'[TÄIDETUD] Logifiltrid ja ohuloo indikaatorid on rakendatud.' if has_triage else '[PUUDULIK] Sündmuste logianalüüsi filtrid rakendamata.'}\n")
            # RESPOND
            f.write("* **RESPOND (Reageeri):** [TÄIDETUD] Käesolev automaatne koondraport on koostatudintsidendi lahendamise toetamiseks.\n")
            # RECOVER
            f.write(f"* **RECOVER (Taasta):** {'[TÄIDETUD] Unifitseeritud kronoloogiline ajajoon (Super Timeline) on loodud süsteemi terviklikkuse taastamiseks.' if has_timeline else '[PUUDULIK] Kronoloogilist ajajoont taastamise toeks ei genereeritud.'}\n")

        logger.info(f"Koondraport edukalt salvestatud: {out_file}")
        print(f"[✓] Analüüsi master-raport on valmis! Asukoht: {out_file}")
        
    except Exception as e:
        logger.error(f"Koondraporti koondamine ebaõnnestus: {e}")
        print(f"[-] Viga raporti loomisel: {e}")

if __name__ == "__main__":
    main()
