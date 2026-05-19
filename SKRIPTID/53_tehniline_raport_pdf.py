#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
#   |   FAILI NIMI:  53_tehniline_raport_pdf.py                           |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Lõppraporti trükk ja vormistamine juhtkonnale        |   #
#   |                (Veakindel UTF-8 ja text-wrap tugi)                  |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

logger = utils.setup_logging("PDF_RAPORT")

def sanitize_text_for_pdf(text):
    """
    Saneerib teksti asendades sümbolid, mida standardne PDF Courier font ei toeta.
    See hoiab ära UnicodeEncodeError krahhi raporti genereerimisel.
    """
    # Eesti keele ja levinumate sümbolite ohutu teisendamine (kui fpdf ei toeta native UTF-8)
    replacements = {
        'õ': 'o', 'Õ': 'O', 'ä': 'a', 'Ä': 'A',
        'ö': 'o', 'Ö': 'O', 'ü': 'u', 'Ü': 'U',
        'š': 's', 'Š': 'S', 'ž': 'z', 'Ž': 'Z',
        '–': '-', '—': '-', '”': '"', '“': '"', '’': "'"
    }
    for search, replace in replacements.items():
        text = text.replace(search, replace)
    
    # Eemaldame kõik muud mitte-ASCII sümbolid, asendades need küsimärgiga
    return text.encode('ascii', 'replace').decode('ascii')


def generate_pdf():
    try:
        from fpdf import FPDF
        
        # Initsialiseerime PDF-i automaatse leheküljemurdmisega (Auto Page Break)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Tiitel
        pdf.set_font("Courier", style='B', size=14)
        pdf.cell(0, 10, text="VALVUR - Tehniline Intsidendiraport", new_x="LMARGIN", new_y="NEXT", align="C")
        
        pdf.set_font("Courier", size=10)
        pdf.cell(0, 10, text=f"Raporti genereerimise aeg: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)

        out_dir = utils.get_output_dir()
        summary_path = os.path.join(out_dir, '52_tulemus_koondraport.txt')

        pdf.set_font("Courier", size=9)

        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                for line in f:
                    clean_line = sanitize_text_for_pdf(line.rstrip())
                    # Kasutame multi_cell, mis murrab liiga pikad read automaatselt!
                    pdf.multi_cell(0, 5, text=clean_line)
        else:
            pdf.cell(0, 10, text="[!] Koondraporti faili ei leitud. Kuvatakse logitud väljundfailid:", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            
            txt_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.txt')])
            csv_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.csv')])
            
            pdf.set_font("Courier", style='B', size=10)
            pdf.cell(0, 8, text="Tekstifailid:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Courier", size=9)
            for tf in txt_files:
                pdf.cell(0, 5, text=f"  - {sanitize_text_for_pdf(tf)}", new_x="LMARGIN", new_y="NEXT")
            
            pdf.ln(5)
            pdf.set_font("Courier", style='B', size=10)
            pdf.cell(0, 8, text="CSV failid:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Courier", size=9)
            for cf in csv_files:
                pdf.cell(0, 5, text=f"  - {sanitize_text_for_pdf(cf)}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)
        pdf.set_font("Courier", style='I', size=8)
        pdf.cell(0, 10, text="Raport genereeritud VALVUR digitaalforensika raamistiku poolt.", new_x="LMARGIN", new_y="NEXT", align="C")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_file = os.path.join(out_dir, f'{timestamp}_valvur_raport.pdf')
        pdf.output(out_file)
        
        return out_file

    except ImportError:
        logger.warning("fpdf2 moodul pole paigaldatud. PDF-i ei genereerita. (pip install fpdf2)")
        return None
    except Exception as e:
        logger.error(f"Ootamatu viga PDF-i genereerimisel: {e}")
        return None


def main():
    logger.info("Genereerin PDF raportit...")
    out_file = generate_pdf()
    if out_file:
        logger.info(f"[+] PDF raport edukalt loodud: {out_file}")
    else:
        logger.warning("[-] PDF raportit ei loodud.")


if __name__ == "__main__":
    main()
