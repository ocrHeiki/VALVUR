#!/usr/bin/env python3
import os
import sys
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("MALU_ANALUUS")
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

def find_memory_dumps():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Kontrollime nii skripti kõrval asuvat kui ka ühe taseme võrra kõrgemat kausta
    possible_dirs = [
        os.path.join(base_dir, "MALUDUMPID"),
        os.path.join(base_dir, "..", "MALUDUMPID")
    ]
    
    dumps = []
    for dump_dir in possible_dirs:
        if os.path.exists(dump_dir):
            for f in os.listdir(dump_dir):
                if f.lower().endswith(('.raw', '.mem', '.dmp', '.vmem', '.img')):
                    dumps.append(os.path.join(dump_dir, f))
    return list(set(dumps))

def run_volatility(memory_file, plugin):
    """Käivitab Volatility 3 käsu pikendatud ajalimiidiga."""
    # Määrame käsu nime (mõnes süsteemis vol, mõnes vol3 või python3 vol.py)
    # Kontrollime, mis on süsteemi paigaldatud
    vol_cmd = "vol"
    try:
        subprocess.check_output([vol_cmd, "--help"], stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        try:
            subprocess.check_output(["vol3", "--help"], stderr=subprocess.DEVNULL)
            vol_cmd = "vol3"
        except FileNotFoundError:
            return None

    print(f"    [>] Käivitan: {vol_cmd} -f {os.path.basename(memory_file)} {plugin} (Palun oota...)")
    try:
        # Tõstetud timeout 600 sekundi ehk 10 minuti peale, kuna suured mälutõmmised võtavad aega
        result = subprocess.check_output(
            [vol_cmd, "-f", memory_file, plugin],
            stderr=subprocess.STDOUT, timeout=600
        ).decode(errors='ignore')
        return result
    except subprocess.TimeoutExpired:
        return f"[!] VIGA: Mäluanalüüs aegus ({plugin} võttis rohkem kui 10 minutit)."
    except subprocess.CalledProcessError as e:
        output = e.output.decode(errors='ignore')
        # Kui plugin ei sobi operatsioonisüsteemiga, tagastame veateate spetsiif
