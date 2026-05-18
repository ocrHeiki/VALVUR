#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
#   |                    -- CENTRAL MASTER LAUNCHER --                    |   #
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  VALVUR_master.py                                     |   #
#   |   LOODUD:      2026-05-18                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Keskne käivitusliides koos kaughalduse               |   #
#   |                eksfiltreerimisega. Käivitab analüüsietapid ja       |   #
#   |                saadab tulemused SCP kaudu Kali masinasse.           |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
###############################################################################
"""

import os
import sys
import platform
import subprocess
import shutil
import socket
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

# =========================================================================
# KONFIGURATSIOON
# =========================================================================
# Need väärtused võib jätta vaikeväärtusteks;
# skript küsib need esmakasutusel interaktiivselt ja salvestab faili.
KALI_IP = ""
KALI_USER = "kali"
KALI_PATH = "/home/kali/Desktop/VALVUR_TULEMUSED"
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".kali_config")
# =========================================================================

LOGO = r"""
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
###############################################################################
"""

logger = utils.setup_logging("MASTER")


def lae_config():
    global KALI_IP, KALI_USER, KALI_PATH
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("KALI_IP="):
                        KALI_IP = line.split("=", 1)[1]
                    elif line.startswith("KALI_USER="):
                        KALI_USER = line.split("=", 1)[1]
                    elif line.startswith("KALI_PATH="):
                        KALI_PATH = line.split("=", 1)[1]
            return True
        except Exception:
            pass
    return False


def salvesta_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write(f"KALI_IP={KALI_IP}\n")
            f.write(f"KALI_USER={KALI_USER}\n")
            f.write(f"KALI_PATH={KALI_PATH}\n")
        print(f"[+] Konfiguratsioon salvestatud: {CONFIG_FILE}")
    except Exception as e:
        print(f"[-] Konfiguratsiooni salvestamine ebaõnnestus: {e}")


class ValvurMaster:
    def __init__(self):
        self.os_type = platform.system()
        self.hostname = socket.gethostname()
        self.scripts_dir = os.path.dirname(os.path.abspath(__file__))
        self.base_dir = os.path.dirname(self.scripts_dir)
        self.result_dir = utils.get_output_dir()
        self.pakendi_nimi = f"VALVUR_{self.hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Kasutame ühtset väljundkausta
        os.environ["VALVUR_OUT"] = self.result_dir

        # Kontrollime keskkonnamuutujat KALI_IP (saab määrata enne käivitust)
        global KALI_IP
        if not KALI_IP and os.environ.get("KALI_IP"):
            KALI_IP = os.environ["KALI_IP"]
            if not os.path.exists(CONFIG_FILE):
                salvesta_config()

    def run_step(self, script_name, args=None):
        script_path = os.path.join(self.scripts_dir, script_name)
        if not os.path.exists(script_path):
            logger.error(f"Faili ei leitud: {script_path}")
            return False
        logger.info(f"Käivitan: {script_name}")
        try:
            env = os.environ.copy()
            env["VALVUR_OUT"] = self.result_dir
            subprocess.run([sys.executable, script_path] + (args or []),
                          check=True, env=env, timeout=600)
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"Ajalimiit ületatud: {script_name}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Moodul {script_name} lõppes veaga: {e}")
            return False
        except Exception as e:
            logger.error(f"Viga moodulis {script_name}: {e}")
            return False

    def kuva_menyy(self, kali_olek):
        print(LOGO)
        print(f"  HOST: {self.hostname}")
        print(f"  OS:   {self.os_type}")
        print(f"  VÄLJUND: {self.result_dir}")
        if kali_olek:
            print(f"  EKSFILTREERIMINE: AKTIIVNE -> {KALI_USER}@{KALI_IP}:{KALI_PATH}")
        else:
            print(f"  EKSFILTREERIMINE: VÄLJAS (tulemused jäävad kohalikku masinasse)")
        print("=" * 70)
        print("  1. FAAS 1+2 – Terviklus + Logifiltreering (KIIRANALÜÜS)")
        print("  2. FAAS 4   – E-ITS 2024 baasturvalisuse audit")
        print("  3. KÕIK MOODULID – Täielik analüüs (FAAS 1–5)")
        print("  4. Ekspordi tulemused käsitsi (ilma uue analüüsita)")
        print("  5. Seadista kaughalduse eksfiltreerimine")
        print("  6. Välju")
        print("=" * 70)

    def setup_kali(self):
        global KALI_IP, KALI_USER, KALI_PATH
        print("\n--- Kaughalduse eksfiltreerimise seadistus ---")
        print(f"  Praegune: {KALI_USER}@{KALI_IP} -> {KALI_PATH}")
        ip = input(f"  Kali IP [{KALI_IP}]: ").strip()
        if ip:
            KALI_IP = ip
        user = input(f"  Kali kasutaja [{KALI_USER}]: ").strip()
        if user:
            KALI_USER = user
        path = input(f"  Kali sihtkaust [{KALI_PATH}]: ").strip()
        if path:
            KALI_PATH = path
        salvesta_config()

    def kogu_raportid(self):
        logger.info("Kogun tulemusi...")
        if not os.path.exists(self.result_dir):
            logger.warning(f"Tulemusi pole: {self.result_dir}")
            return None
        pakend = os.path.join(self.scripts_dir, self.pakendi_nimi)
        shutil.make_archive(pakend, "zip", self.result_dir)
        zip_path = f"{pakend}.zip"
        suurus = os.path.getsize(zip_path)
        logger.info(f"Tulemused pakitud: {zip_path} ({suurus} baiti)")
        return zip_path

    def eksfiltreeri_kalisse(self, zip_path):
        if not KALI_IP:
            print("[-] Eksfiltreerimine pole seadistatud. Vali menüüst 5.")
            return

        if not zip_path or not os.path.exists(zip_path):
            logger.error("Paki faili pole, kogun uuesti...")
            zip_path = self.kogu_raportid()
            if not zip_path:
                return

        print("\n" + "=" * 70)
        print(f"[*] EKSFILTREERIN: {zip_path} -> {KALI_USER}@{KALI_IP}:{KALI_PATH}")
        print("=" * 70)

        if self.os_type == "Windows":
            cmd = ["powershell", "-Command",
                   f"scp -o StrictHostKeyChecking=no -o ConnectTimeout=10 \"{zip_path}\" {KALI_USER}@{KALI_IP}:\"{KALI_PATH}/\""]
        else:
            cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                   zip_path, f"{KALI_USER}@{KALI_IP}:{KALI_PATH}/"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"[✔] TRANSFEER ÕNNESTUS! Tulemused saadetud:")
                print(f"    {KALI_USER}@{KALI_IP}:{KALI_PATH}/{os.path.basename(zip_path)}")
                os.remove(zip_path)
                logger.info("Kohalik pakifail kustutatud")
            else:
                print(f"[-] SCP viga (kood {result.returncode})")
                if result.stderr:
                    for line in result.stderr.splitlines():
                        print(f"    {line}")
                print("[*] Tulemused jäid kohalikku: " + zip_path)
        except FileNotFoundError:
            print("[-] SCP pole paigaldatud!")
            print("    Paigalda: sudo apt install openssh-client")
            print(f"[*] Tulemused jäid kohalikku: {zip_path}")
        except subprocess.TimeoutExpired:
            print(f"[-] Ühendus {KALI_IP}:22 aegus! Kontrolli Kali SSH serverit.")
            print(f"[*] Tulemused jäid kohalikku: {zip_path}")

    def oota_enter(self):
        input("\n  Vajuta Enter...")

    def kiiranalyys(self):
        print("\n" + "=" * 70)
        print("  FAAS 1+2 – Terviklus + Logifiltreering")
        print("=" * 70)
        self.run_step("01_terviklus.py")
        self.run_step("11_turvafiltreering.py")
        self.run_step("12_marksonade_otsing.py")
        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def eits_audit(self):
        print("\n" + "=" * 70)
        print("  FAAS 4 – E-ITS 2024 baasturvalisuse audit")
        print("=" * 70)
        self.run_step("32_kasutajate_audit.py")
        self.run_step("34_eits_vastavus.py")
        self.run_step("31_vorgu_skaneerimine.py")
        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def taielik_analyys(self):
        print("\n" + "=" * 70)
        print("  TÄIELIK ANALÜÜS – KÕIK FAASID (1–5)")
        print("=" * 70)
        logger.info(f"Alustan täielikku analüüsi masinal {self.hostname}")

        logger.info("FAAS 1: Algkäivitus ja andmehõive")
        self.run_step("01_terviklus.py")
        if os.name == "nt":
            self.run_step("02_windows_evtx.py", args=["--live"])
        else:
            self.run_step("03_linux_logid.py")

        logger.info("FAAS 2: Filtreerimine ja tuvastus")
        self.run_step("11_turvafiltreering.py")
        self.run_step("12_marksonade_otsing.py")

        logger.info("FAAS 3: Süvaanalüüs ja deobfuskatsioon")
        self.run_step("21_powershell_decode.py")
        self.run_step("22_kahtlased_failid.py")
        self.run_step("23_linux_syvaanaluus.py")

        logger.info("FAAS 4: Välisluure ja kontekst")
        self.run_step("31_vorgu_skaneerimine.py")
        self.run_step("32_kasutajate_audit.py")
        self.run_step("34_eits_vastavus.py")

        logger.info("FAAS 5: Süntees ja raporteerimine")
        self.run_step("51_koond_ajajoon.py")
        self.run_step("52_genereeri_raport.py")

        logger.info("Analüüs lõpetatud")
        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def ekspordi_kasitsi(self):
        print("\n" + "=" * 70)
        print("  EKSPORDI TULEMUSED (ilma uue analüüsita)")
        print("=" * 70)
        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def run(self):
        lae_config()
        while True:
            self.kuva_menyy(bool(KALI_IP))
            valik = input("  Valik (1-6): ").strip()

            if valik == "1":
                self.kiiranalyys()
            elif valik == "2":
                self.eits_audit()
            elif valik == "3":
                self.taielik_analyys()
            elif valik == "4":
                self.ekspordi_kasitsi()
            elif valik == "5":
                self.setup_kali()
            elif valik == "6":
                print("[-] VALVUR suletakse.")
                break
            else:
                print("[-] Vigane valik!")
            self.oota_enter()


if __name__ == "__main__":
    master = ValvurMaster()
    master.run()
