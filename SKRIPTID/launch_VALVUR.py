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
#   |   PROJEKT:     VALVUR - Remote Launcher                             |   #
#   |   FAILI NIMI:  launch_VALVUR.py                                     |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Süsteemi kiirkäivitus ja automatiseeritud            |   #
#   |                keskkonna bootstrap (võrgu ja venv kontrolliga).     |   #
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
import urllib.request

REPO_URL = "https://github.com/ocrHeiki/RAKO.git"
SUBDIR = os.path.join("materjalid", "infoturbeHALDAMINE", "VALVUR")

LOGO = r"""
###############################################################################
#                    VALVUR AUTOMATED LIVE BOOTSTRAPPER                       #
###############################################################################
"""

def check_command(cmd):
    """Kontrollib käsu olemasolu süsteemis."""
    return shutil.which(cmd) is not None

def test_internet_connection():
    """Kontrollib, kas masinal on ühendus välismaailmaga (GitHub/PyPI)."""
    try:
        # Testime kiiret päringut GitHubi suunal (timeout 3 sekundit)
        urllib.request.urlopen("https://github.com", timeout=3)
        return True
    except Exception:
        return False

def main():
    print(LOGO)
    print("[*] VALVUR BOOTSTRAP ALUSTAB...")

    # 1. Kontrolli võrguühendust (Kriitiline isoleeritud keskkondade puhul)
    online = test_internet_connection()
    if not online:
        print("[!] HOIATUS: Internetiühendus puudub või GitHub on blokeeritud!")
        print("[*] Forensiline režiim: Otsitakse kohalikku koodibaasi ilma kloonimiseta...")
        
        # Kontrollime, kas skript käivitati otse VALVUR kaustast, kus master on juba olemas
        if os.path.exists("VALVUR_master.py"):
            print("[✔] Tuvastati kohalik 'VALVUR_master.py'. Käivitan lokaalselt...")
            subprocess.run([sys.executable, "VALVUR_master.py"])
            sys.exit(0)
        else:
            print("[-] VIGA: Internet puudub ja kohalikku 'VALVUR_master.py' faili ei leitud!")
            print("    Kopeeri VALVUR-i täispakett mälupulgalt lokaalselt sihtmärki.")
            sys.exit(1)

    # 2. Kontrolli git olemasolu
    if not check_command("git"):
        print("[!] VIGA: Git pole paigaldatud, kuid võrk nõuab kloonimist.")
        print("    Paigaldamiseks: sudo apt install git (või kasuta lokaalset paketti)")
        sys.exit(1)

    # 3. Ajutise töökausta ettevalmistus
    work_dir = os.path.join(tempfile.gettempdir(), "VALVUR_LIVE")
    print(f"[*] Valmistatakse ette ajutine kataloog: {work_dir}")
    
    try:
        if os.path.exists(work_dir): 
            shutil.rmtree(work_dir)
        os.makedirs(work_dir)
        os.chdir(work_dir)
    except Exception as e:
        print(f"[-] VIGA: Töökausta ettevalmistamine nurjus: {e}")
        sys.exit(1)

    # 4. Repositooriumi kloonimine
    print(f"[*] Kloonitakse repositoorium: {REPO_URL}")
    try:
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, "."], check=True)
    except subprocess.CalledProcessError:
        print("[-] VIGA: Repositooriumi kloonimine ebaõnnestus.")
        sys.exit(1)

    # Liigume VALVUR-i alamkataloogi
    if os.path.exists(SUBDIR):
        os.chdir(SUBDIR)
    else:
        print(f"[-] VIGA: Repositooriumi struktuur on vigane. Puudub kaust: {SUBDIR}")
        sys.exit(1)

    # 5. Virtuaalkeskkonna (venv) loomine koos veatöötlusega
    print("[*] Luuakse isoleeritud virtuaalkeskkond (venv)...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
    except subprocess.CalledProcessError:
        print("\n[!] VIGA: Virtuaalkeskkonna loomine ebaõnnestus!")
        if os.name != "nt":
            print("    Tõenäoliselt puudub süsteemne 'python3-venv' pakett.")
            print("    Lahendus: sudo apt update && sudo apt install python3-venv")
        sys.exit(1)

    # Määrame õige Pythoni tee virtuaalkeskkonnas
    if os.name == "nt":
        python_exe = os.path.join("venv", "Scripts", "python.exe")
    else:
        python_exe = os.path.join("venv", "bin", "python")

    # 6. Sõltuvuste paigaldamine
    print("[*] Paigaldatakse analüüsiks vajalikud moodulid...")
    try:
        subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([python_exe, "-m", "pip", "install", "python-evtx", "python-docx", "rich", "psutil", "fpdf2"], check=True)
    except subprocess.CalledProcessError:
        print("[-] VIGA: Sõltuvuste paigaldamine pip-i kaudu ebaõnnestus.")
        sys.exit(1)

    # 7. Dünaamiline sihtfaili kontroll ja käivitus
    print("\n" + "="*70)
    print("      VALVUR ON VALMIS JA KÄIVITUB ISOLEERITUD KESKKONNAS")
    print("="*70 + "\n")

    # Kontrollime failinimede variatsioone (tõstutundlikkuse kaitse)
    sihtfailid = ["VALVUR_master.py", "valvurMASTER.py", "VALVUR_master.py"]
    käivitatav_skript = None

    for fail in sihtfailid:
        # Kontrollime otse kaustast ja võimaliku alakataloogi seest
        if os.path.exists(fail):
            käivitatav_skript = fail
            break
        elif os.path.exists(os.path.join("SKRIPT_2", fail)):
            käivitatav_skript = os.path.join("SKRIPT_2", fail)
            break

    if käivitatav_skript:
        print(f"[*] Käivitan master-mooduli: {käivitatav_skript}")
        subprocess.run([python_exe, käivitatav_skript])
    else:
        print("[-] VIGA: Keskset käivitusfaili (VALVUR_master.py) ei leitud ajutisest kaustast!")
        sys.exit(1)


if __name__ == "__main__":
    main()
