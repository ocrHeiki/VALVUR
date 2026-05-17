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
#   |   FAILI NIMI:  53_tehniline_raport_pdf.py                           |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Lõppraporti trükk ja vormistamine juhtkonnale        |   #
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


def generate_pdf():
    try:
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Courier", size=10)
        pdf.cell(200, 10, text="VALVUR - Tehniline Raport", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.cell(200, 10, text=f"Kuupaev: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.ln(10)
        pdf.set_font("Courier", size=8)

        out_dir = utils.get_output_dir()
        summary_path = os.path.join(out_dir, '52_tulemus_koondraport.txt')

        if os.path.exists(summary_path):
            with open(summary_path, 'r', encoding='utf-8') as f:
                for line in f:
                    pdf.cell(200, 5, text=line.rstrip(), new_x="LMARGIN", new_y="NEXT")
        else:
            txt_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.txt')])
            csv_files = sorted([f for f in os.listdir(out_dir) if f.endswith('.csv')])
            pdf.cell(200, 10, text="Tekstifailid:", new_x="LMARGIN", new_y="NEXT")
            for tf in txt_files:
                pdf.cell(200, 5, text=f"  - {tf}", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(5)
            pdf.cell(200, 10, text="CSV failid:", new_x="LMARGIN", new_y="NEXT")
            for cf in csv_files:
                pdf.cell(200, 5, text=f"  - {cf}", new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)
        pdf.cell(200, 10, text="Raport genereeritud VALVUR poolt.", new_x="LMARGIN", new_y="NEXT")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_file = os.path.join(out_dir, f'{timestamp}_valvur_raport.pdf')
        pdf.output(out_file)
        return out_file
    except ImportError:
        logger.warning("fpdf2 pole paigaldatud. Paigaldamiseks: pip install fpdf2")
        return None
    except Exception as e:
        logger.error(f"PDF genereerimine ebaõnnestus: {e}")
        return None


def main():
    logger.info("Genereerin PDF raportit...")
    out_file = generate_pdf()
    if out_file:
        logger.info(f"PDF raport loodud: {out_file}")
    else:
        logger.warning("PDF raportit ei loodud (fpdf2 puudub)")


if __name__ == "__main__":
    main()
