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
#   |   PROJEKT:     VALVUR - Remote Launcher                             |   #
#   |   FAILI NIMI:  launch_VALVUR.py                                     |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Süsteemi kiirkäivitus virtuaalkeskkonnas (venv).     |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import subprocess
import shutil
import tempfile

REPO_URL = "https://github.com/ocrHeiki/VALVUR.git"

def main():
    # KALI_IP saab määrata:
    #   1) keskkonnamuutujana:  KALI_IP=192.168.1.100 python3 -c "$(curl ...)"
    #   2) käsurea argumendina: python3 -c "$(curl ...)" 192.168.1.100
    kali_ip = os.environ.get("KALI_IP", "")
    if not kali_ip and len(sys.argv) > 1:
        kali_ip = sys.argv[1]

    print("[*] VALVUR BOOTSTRAP ALUSTAB...")
    if kali_ip:
        print(f"[*] KALI IP: {kali_ip} (eksfiltreerimine aktiivne)")
    else:
        print("[*] KALI IP: määramata (seadistad hiljem menüüst)")

    work_dir = os.path.join(tempfile.gettempdir(), "VALVUR_LIVE")
    if os.path.exists(work_dir): shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    os.chdir(work_dir)

    print(f"[*] Kloonitakse repositoorium: {REPO_URL}")
    subprocess.run(["git", "clone", REPO_URL, "."], check=True)

    print("[*] Luuakse isoleeritud virtuaalkeskkond (venv)...")
    subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)

    if os.name == "nt":
        python_exe = os.path.join("venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join("venv", "bin", "python")

    print("[*] Paigaldatakse sõltuvused ja Rich UI...")
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([python_exe, "-m", "pip", "install", "python-evtx", "python-docx", "rich", "psutil"], check=True)

    print("\n" + "="*60)
    print("   VALVUR KÄIVITUB VIRTUAALKESKKONNAS")
    print("   (interaktiivne master koos SCP eksfiltreerimisega)")
    print("="*60 + "\n")

    # Edasta KALI_IP alamprotsessi
    env = os.environ.copy()
    if kali_ip and not env.get("KALI_IP"):
        env["KALI_IP"] = kali_ip
    subprocess.run([python_exe, "SKRIPTID/VALVUR_master.py"], env=env)

if __name__ == "__main__":
    main()
