#!/usr/bin/env python3
import os
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("VORGU_SCAN")
    out_dir = utils.get_output_dir()
except:
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()
    out_dir = "TULEMUSED"

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

def check_nmap():
    """Kontrollib, kas nmap on süsteemis olemas ja tagastab õige käsurea tee."""
    paths_to_test = ["nmap"]
    
    # Kui oleme Windowsis, proovime ka vaikimisi paigaldusteesid
    if os.name == 'nt':
        paths_to_test.extend([
            r"C:\Program Files (x86)\Nmap\nmap.exe",
            r"C:\Program Files\Nmap\nmap.exe"
        ])
        
    for path in paths_to_test:
        try:
            subprocess.check_output([path, "--version"], stderr=subprocess.DEVNULL)
            return path
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return None

def run_nmap_scan():
    print(LOGO)
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "31_tulemus_vorgu_skaneerimine.txt")
    
    # Proovime dünaamiliselt hankida alamvõrgu
    try:
        target = utils.get_local_subnet()
    except:
        target = "192.168.1.0/24" # Turvaline fallback uurimiskeskkondade jaoks
        
    nmap_path = check_nmap()
    if not nmap_path:
        msg = "[-] Nmap-i ei leitud süsteemist! Paigaldamiseks:\n    Linux: sudo apt install nmap\n    Windows: laadi alla nmap.org lehelt"
        logger.error("Nmap tarkvara puudub süsteemist.")
        print(msg)
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(msg)
        return

    logger.info(f"Alustan võrgu skaneerimist sihtmärgiga: {target}")
    print(f"[+] Tuvastati sihtmärk: {target}")
    print(f"[+] Kasutan Nmap asukohta: {nmap_path}")
    print("    [*] Teostan kombineeritud hostide avastamist ja pordikontrolli (Palun oota)...")

    try:
        # -F: Kiire pordiskaneering (top 100 levinumat porti, nt 22, 80, 443, 445, 3389)
        # --open: Kuvab ainult reaalselt avatud pordid
        # -PE: ICMP Echo request hostide paremaks leidmiseks
        cmd = [nmap_path, "-F", "--open", "-PE", target]
        
        # Tõstetud timeout 10 minuti (600s) peale, kuna pordikontroll võtab aega
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=600).decode(errors='ignore')
        
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("============================================================\n")
            f.write(f"           VALVUR - VÕRGUSKANEERIMISE RAPORT ({target})     \n")
            f.write("============================================================\n\n")
            f.write(result)
            
        logger.info(f"Võrguskaneering edukalt lõpetatud. Tulemused: {out_file}")
        print(f"[✓] Skaneerimine edukalt lõpetatud! Raport salvestatud: {out_file}")
        
    except subprocess.TimeoutExpired:
        logger.error("Skaneerimine aegus (ületati 10 minuti piirang)")
        print("❌ VIGA: Skaneerimine võttis liiga kaua aega (>600s). Alamvõrk on liiga suur või võrk ummistunud.")
    except subprocess.CalledProcessError as e:
        error_msg = e.output.decode(errors='ignore')
        if "requires root privileges" in error_msg.lower():
            logger.error("Nmap vajab administraatori / root õigusi.")
            print("❌ VIGA: Antud Nmap skaneeringu tüüp vajab administraatori (root/sudo) õigusi!")
        else:
            logger.error(f"Nmap viga: {error_msg}")
            print(f"❌ VIGA Nmap käivitamisel: {error_msg}")
    except Exception as e:
        logger.error(f"Skaneerimine ebaõnnestus: {e}")
        print(f"❌ Ootamatu viga: {e}")

if __name__ == "__main__":
    run_nmap_scan()
