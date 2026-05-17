#!/usr/bin/env python3
"""
###############################################################################
#   VALVUR MASTER CONTROL - Sünkroniseeritud Töövoog                          #
###############################################################################
"""
import os
import sys
import subprocess
import socket
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOSTNAME = socket.gethostname()
RESULT_DIR = os.path.join(BASE_DIR, "TULEMUSED", HOSTNAME)

logger = utils.setup_logging("MASTER")

def run_step(script_name, critical=False, args=None):
    logger.info(f"===> KÄIVITAN: {script_name}")
    script_path = os.path.join(BASE_DIR, "SKRIPTID", script_name)
    if not os.path.exists(script_path):
        logger.error(f"FAILI EI LEITUD: {script_path}")
        if critical: sys.exit(1)
        return False

    env = os.environ.copy()
    env["VALVUR_OUT"] = RESULT_DIR
    try:
        subprocess.run([sys.executable, script_path] + (args or []), check=True, env=env)
        return True
    except Exception as e:
        logger.error(f"VIGA ETAPIS {script_name}: {e}")
        if critical: sys.exit(1)
        return False

if __name__ == "__main__":
    utils.ensure_folders(BASE_DIR)
    os.makedirs(RESULT_DIR, exist_ok=True)
    
    # FAAS 1: ALGKÄIVITUS JA ANDMEHÕIVE (KRIITILINE)
    run_step("01_terviklus.py", critical=True)
    if os.name == "nt":
        run_step("02_windows_evtx.py", critical=True, args=["--live"])
    else:
        run_step("03_linux_logid.py", critical=True)

    # FAAS 2: FILTREERIMINE JA TUUVASTUS
    steps_phase2 = [
        "11_turvafiltreering.py",
        "12_marksonade_otsing.py",
    ]
    for step in steps_phase2:
        run_step(step)

    # FAAS 3: SÜVAANALÜÜS JA DEOBFUSKATSIOON
    steps_phase3 = [
        "21_powershell_decode.py",
        "22_kahtlased_failid.py",
        "23_linux_syvaanaluus.py",
    ]
    for step in steps_phase3:
        run_step(step)

    # FAAS 4: VÄLISLUURE JA KONTEKST
    steps_phase4 = [
        "31_vorgu_skaneerimine.py",
        "32_kasutajate_audit.py",
        "33_threat_intel_osint.py",
        "24_malu_analuus.py",
    ]
    for step in steps_phase4:
        run_step(step)

    # FAAS 5: SÜNTEES JA RAPORTEERIMINE
    run_step("51_koond_ajajoon.py")
    run_step("52_genereeri_raport.py")
    run_step("53_tehniline_raport_pdf.py")

    logger.info(f"KÕIK VALMIS. Tulemused: {RESULT_DIR}")
