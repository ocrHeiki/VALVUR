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
#   |   PROJEKT:     VALVUR - Remote Launcher (Root Version)              |   #
#   |   FAILI NIMI:  launch_VALVUR.py                                     |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Süsteemi kiirkäivitus virtuaalkeskkonnas koos        |   #
#   |                KALI_IP eksfiltreerimise toe ja veatöötlusega.       |   #
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

def check_command(cmd):
    """Kontrollib, kas vajalik käsk on süsteemis saadaval."""
    return shutil.which(cmd) is not None

def main():
    print("[*] VALVUR BOOTSTRAP ALUSTAB...")

    # 1. Tuvasta KALI_IP (keskkonnamuutujast või käsurealt)
    kali_ip = os.environ.get("KALI_IP", "")
    if not kali_ip and len(sys.argv) > 1:
        # Võtame viimase argumendi juhuks, kui curl või python lisas vahepeal omi lippe
        kali_ip = sys.argv[-1]
        # Lihtne kontroll, et tegu pole skripti nime endaga
        if kali_ip.endswith('.py') or kali_ip == '-c':
            kali_ip = ""

    if kali_ip:
        print(f"[✔] KALI IP: {kali_ip} (Andmete eksfiltreerimine aktiivne)")
    else:
        print("[*] KALI IP: määramata (Andmed salvestatakse ainult lokaalselt)")

    # 2. Kontrolli Git olemasolu (Kriitiline, kuna tõmbame otse repost)
    if not check_command("git"):
        print("[!] VIGA: Süsteemis puudub 'git' käsk. Lähtekoodi pole võimalik alla laadida.")
        print("    Lahendus Linuxis: sudo apt update && sudo apt install -y git")
        sys.exit(1)

    # 3. Ajutise isolatsioonikausta loomine
    work_dir = os.path.join(tempfile.gettempdir(), "VALVUR_LIVE")
    try:
        if os.path.exists(work_dir): 
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)
        os.chdir(work_dir)
    except Exception as e:
        print(f"[-] VIGA: Ei saanud luua ajutist kausta {work_dir}: {e}")
        sys.exit(1)

    # 4. Repositooriumi kiire kloonimine (ainult viimane commit, säästab aega/mahtu)
    print(f"[*] Kloonitakse repositoorium: {REPO_URL}")
    try:
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, "."], check=True)
    except subprocess.CalledProcessError:
        print("[-] VIGA: Git kloonimine ebaõnnestus. Kontrolli võrguühendust või repositooriumi õiguseid.")
        sys.exit(1)

    # 5. Virtuaalkeskkonna (venv) loomine
    print("[*] Luuakse isoleeritud virtuaalkeskkond (venv)...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    except subprocess.CalledProcessError:
        print("\n[!] VIGA: Virtuaalkeskkonna loomine nurjus.")
        if os.name != "nt":
            print("    Süsteemis puudub tõenäoliselt pakett 'python3-venv'.")
            print("    Lahendus: sudo apt install -y python3-venv")
        sys.exit(1)

    # Määrame õige interpretaatori asukoha sõltuvalt OS-ist
    if os.name == "nt":
        python_exe = os.path.join("venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join("venv", "bin", "python")

    # 6. Sõltuvuste paigaldamine (Lisatud fpdf2 raportite jaoks)
    print("[*] Paigaldatakse vajalikud moodulid ja Rich UI...")
    try:
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([python_exe, "-m", "pip", "install", "python-evtx", "python-docx", "rich", "psutil", "fpdf2"], check=True)
    except subprocess.CalledProcessError:
        print("[-] VIGA: Sõltuvuste paigaldamine pip-i kaudu ebaõnnestus.")
        sys.exit(1)

    # 7. Sihtfaili kontroll ja käivitamine
    master_skript = os.path.join("SKRIPTID", "VALVUR_master.py")
    
    # Tõstutundlikkuse fallback (juhuks kui kaust on nt 'skriptid' või 'Skriptid')
    if not os.path.exists(master_skript):
        for kataloog in os.listdir("."):
            if kataloog.lower() == "skriptid" and os.path.isdir(kataloog):
                master_skript = os.path.join(kataloog, "VALVUR_master.py")
                break

    if not os.path.exists(master_skript):
        print(f"[-] VIGA: Põhimoodulit '{master_skript}' ei leitud kloonitud koodibaasist!")
        sys.exit(1)

    print("\n" + "="*65)
    print("    VALVUR KÄIVITUB VIRTUAALKESKKONNAS")
    print("    (Interaktiivne master koos võrgu eksfiltreerimise toega)")
    print("="*65 + "\n")

    # Valmistame ette keskkonnamuutujad alamprotsessi jaoks
    env = os.environ.copy()
    if kali_ip:
        env["KALI_IP"] = kali_ip

    # Käivitame põhimooduli
    subprocess.run([python_exe, master_skript], env=env)


if __name__ == "__main__":
    main()
