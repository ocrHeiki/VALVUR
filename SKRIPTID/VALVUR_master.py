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
#   |   FAILI NIMI:  VALVUR_master.py                                     |   #
#   |   LOODUD:      2026-05-18                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Keskne käivitusliides ja automatiseeritud            |   #
#   |                eksfiltreerimine uurija masinasse (Kali/SIEM).       |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import platform
import subprocess
import shutil
import socket
import tempfile
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("MASTER")
except Exception:
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()

# =========================================================================
# GLOBAALNE SEADISTUS
# =========================================================================
KALI_IP = ""
KALI_USER = "kali"
KALI_PATH = "/home/kali/Desktop/VALVUR_TULEMUSED"
CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".kali_config")
# =========================================================================

LOGO = r"""
###############################################################################
#             VALVUR ORKESTRAATOR — KESKNE INTSIDENDI JUHTPULT              #
###############################################################################
"""

def lae_config():
    global KALI_IP, KALI_USER, KALI_PATH
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    if k == "KALI_IP": KALI_IP = v
                    elif k == "KALI_USER": KALI_USER = v
                    elif k == "KALI_PATH": KALI_PATH = v
            return True
        except Exception:
            pass
    return False

def salvesta_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"KALI_IP={KALI_IP}\n")
            f.write(f"KALI_USER={KALI_USER}\n")
            f.write(f"KALI_PATH={KALI_PATH}\n")
        print(f"[+] Konfiguratsioon salvestatud: {CONFIG_FILE}")
    except Exception as e:
        print(f"[-] Seadistuse salvestamine nurjus: {e}")


class ValvurMaster:
    def __init__(self):
        self.os_type = platform.system()
        self.hostname = socket.gethostname()
        self.scripts_dir = os.path.dirname(os.path.abspath(__file__))
        self.result_dir = utils.get_output_dir() if 'utils' in sys.modules else "TULEMUSED"
        self.pakendi_nimi = f"VALVUR_{self.hostname}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        os.environ["VALVUR_OUT"] = self.result_dir

        global KALI_IP
        if not KALI_IP and os.environ.get("KALI_IP"):
            KALI_IP = os.environ["KALI_IP"]
        if not KALI_IP and os.environ.get("SSH_CLIENT"):
            KALI_IP = os.environ["SSH_CLIENT"].split()[0]
            logger.info(f"KALI IP tuvastatud SSH_CLIENT-ist: {KALI_IP}")
        
        if KALI_IP and not os.path.exists(CONFIG_FILE):
            salvesta_config()

    def run_step(self, script_name, args=None):
        """Käivitab alam-mooduli ja tagastab selle õnnestumise staatuse."""
        script_path = os.path.join(self.scripts_dir, script_name)
        if not os.path.exists(script_path):
            logger.error(f"Kriitilist moodulit ei leitud: {script_path}")
            return False
            
        logger.info(f"KÄIVITAN MOODULI: {script_name}")
        try:
            env = os.environ.copy()
            env["VALVUR_OUT"] = self.result_dir
            # Kasutame sys.executable tagamaks, et käivitatakse samas virtuaalkeskkonnas
            subprocess.run([sys.executable, script_path] + (args or []),
                           check=True, env=env, timeout=600)
            return True
        except subprocess.TimeoutExpired:
            logger.error(f"Ajalimiit (10 min) ületatud moodulil: {script_name}")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Moodul {script_name} lõpetas veakoodiga: {e.returncode}")
            return False
        except Exception as e:
            logger.error(f"Ootamatu viga mooduli {script_name} täitmisel: {e}")
            return False

    def kuva_menyy(self, kali_olek):
        print(LOGO)
        print(f"  UURITAV HOST: {self.hostname} ({self.os_type})")
        print(f"  LOKAALNE VÄLJUNDKAUST: {self.result_dir}")
        if kali_olek:
            print(f"  EKSFILTREERIMISE SIHT: {KALI_USER}@{KALI_IP}:{KALI_PATH}")
        else:
            print(f"  EKSFILTREERIMINE: MITTEAKTIIVNE (Tulemused salvestatakse kohalikult)")
        print("=" * 75)
        print("  1. FAAS 1+2 – Terviklus + Logifiltreering (Kiiranalüüs)")
        print("  2. FAAS 4   – E-ITS baasturvalisuse audit")
        print("  3. KÕIK FAASID – Täielik süvaanalüüs (Faasid 1–5 järjestikku)")
        print("  4. Paki ja eksfiltreeri praegused tulemused käsitsi")
        print("  5. Seadista kaughalduse / Kali sihtmärgi parameetrid")
        print("  6. Välju raamistikust")
        print("=" * 75)

    def setup_kali(self):
        global KALI_IP, KALI_USER, KALI_PATH
        print("\n--- Kaughalduse eksfiltreerimise seadistamine ---")
        ip = input(f"  Kali/Uurija IP [{KALI_IP}]: ").strip()
        if ip: KALI_IP = ip
        user = input(f"  SSH Kasutaja [{KALI_USER}]: ").strip()
        if user: KALI_USER = user
        path = input(f"  Sihtkoha kaust [{KALI_PATH}]: ").strip()
        if path: KALI_PATH = path
        salvesta_config()

    def kogu_raportid(self):
        """Pakib andmed forensiliselt turvalises kohas (süsteemi Temp kaustas)."""
        logger.info("Alustan kogutud tõendite ja raportite pakkimist...")
        if not os.path.exists(self.result_dir) or not os.listdir(self.result_dir):
            logger.warning("Väljundkaust on tühi. Pole andmeid, mida pakkida.")
            return None
            
        # Loome ZIP faili süsteemi Temp kataloogi, et säilitada tööriistakausta puhtus
        temp_dir = tempfile.gettempdir()
        pakend_path = os.path.join(temp_dir, self.pakendi_nimi)
        
        try:
            arhiiv = shutil.make_archive(pakend_path, "zip", self.result_dir)
            logger.info(f"Tõendid edukalt pakitud faili: {arhiiv} ({os.path.getsize(arhiiv)} baiti)")
            return arhiiv
        except Exception as e:
            logger.error(f"Arhiivi loomine nurjus: {e}")
            return None

    def eksfiltreeri_kalisse(self, zip_path):
        if not KALI_IP:
            print("[-] Transfeeri sihtmärk seadistamata! Vali menüüst punkt 5.")
            return

        if not zip_path or not os.path.exists(zip_path):
            return

        print(f"\n[*] EKSFILTREERIN TÕENDID: {os.path.basename(zip_path)} -> {KALI_USER}@{KALI_IP}")

        # Lollikindel argumentide listi edastus ilma ohtliku powershell string-parsinguta
        if self.os_type == "Windows":
            cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
                   zip_path, f"{KALI_USER}@{KALI_IP}:{KALI_PATH}/"]
        else:
            cmd = ["scp", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=15",
                   zip_path, f"{KALI_USER}@{KALI_IP}:{KALI_PATH}/"]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
            if result.returncode == 0:
                print("[✔] TRANSFEER ÕNNESTUS! Fail on turvaliselt üle kantud.")
                try:
                    os.remove(zip_path)
                    logger.info("Ajutine kohalik arhiiv turvalisuse kaalutlustel kustutatud.")
                except Exception:
                    pass
            else:
                print(f"[-] SCP ülekanne ebaõnnestus (Kood: {result.returncode})")
                if result.stderr:
                    print(f"    Vea detailid: {result.stderr.strip()}")
                print(f"[*] Arhiiv säilitati turvaliselt kohalikus temp-kaustas: {zip_path}")
        except FileNotFoundError:
            print("[-] Süsteemist ei leitud OpenSSH klienti (scp)!")
            print(f"[*] Tulemused on päästetud siia: {zip_path}")
        except subprocess.TimeoutExpired:
            print(f"[-] Ühendus aegus! Kontrolli, et Kali masinas ({KALI_IP}) töötab SSH teenus.")
            print(f"[*] Tulemused on päästetud siia: {zip_path}")

    def oota_enter(self):
        input("\n  Jätkamiseks vajuta Enter...")

    def kiiranalyys(self):
        print("\n" + "=" * 75)
        print("  KÄIVITAN: FAAS 1+2 (Kiiranalüüs ja logifiltreering)")
        print("=" * 75)
        if self.run_step("01_terviklus.py"):
            self.run_step("11_turvafiltreering.py")
            self.run_step("12_marksonade_otsing.py")
        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def eits_audit(self):
        print("\n" + "=" * 75)
        print("  KÄIVITAN: FAAS 4 (E-ITS 2024 baasturvalisuse audit)")
        print("=" * 75)
        self.run_step("32_kasutajate_audit.py")
        self.run_step("34_eits_vastavus.py")
        self.run_step("31_vorgu_skaneerimine.py")
        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def taielik_analyys(self):
        print("\n" + "=" * 75)
        print("  KÄIVITAN TÄIELIKU VEA- JA SÕLTUVUSKONTROLLIGA TÖÖVOO (Faasid 1–5)")
        print("=" * 75)
        
        # Järjestikused etapid. Kui eelmine kriitiline samm kukub kokku, peatatakse kett.
        tookava = [
            ("01_terviklus.py", None),
            ("02_windows_evtx.py" if os.name == "nt" else "03_linux_logid.py", ["--live"] if os.name == "nt" else None),
            ("11_turvafiltreering.py", None),
            ("12_marksonade_otsing.py", None),
            ("21_powershell_decode.py", None),
            ("22_kahtlased_failid.py", None),
            ("23_linux_syvaanaluus.py" if os.name != "nt" else None, None),
            ("31_vorgu_skaneerimine.py", None),
            ("32_kasutajate_audit.py", None),
            ("34_eits_vastavus.py", None),
            ("51_koond_ajajoon.py", None),
            ("52_genereeri_raport.py", None)
        ]

        for skript, args in tookava:
            if not skript: 
                continue
            onnestus = self.run_step(skript, args)
            if not onnestus and skript in ["01_terviklus.py", "11_turvafiltreering.py", "51_koond_ajajoon.py"]:
                logger.error(f"Kriitilise mooduli {skript} viga! Peatan ohutuse tagamiseks ahela.")
                print(f"\n[-] Analüüs katkestati rikke tõttu moodulis: {skript}")
                break

        zip_path = self.kogu_raportid()
        self.eksfiltreeri_kalisse(zip_path)

    def run(self):
        lae_config()
        while True:
            self.kuva_menyy(bool(KALI_IP))
            valik = input("  Sisesta valik (1-6): ").strip()

            if valik == "1":
                self.kiiranalyys()
            elif valik == "2":
                self.eits_audit()
            elif valik == "3":
                self.taielik_analyys()
            elif valik == "4":
                zip_path = self.kogu_raportid()
                self.eksfiltreeri_kalisse(zip_path)
            elif valik == "5":
                self.setup_kali()
            elif valik == "6":
                print("[*] VALVUR orkestraator suletakse. Kohtumiseni küberrindel!")
                break
            else:
                print("[-] Vigane valik, proovi uuesti.")
            self.oota_enter()


if __name__ == "__main__":
    master = ValvurMaster()
    master.run()
