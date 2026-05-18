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
#   |                                                                     |   #
#   |   PROJEKT:     VALVUR - Intsidendi süvaanalüüs                      |   #
#   |   FAILI NIMI:  34_eits_vastavus.py                                  |   #
#   |   LOODUD:      2026-05-18                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Infosüsteemi baasturvalisuse kontroll (E-ITS 2024).  |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import platform
import subprocess
from datetime import datetime

class EITSAuditor:
    def __init__(self):
        self.os_type = platform.system()
        self.report_path = "EITS_vastavusraport_team10.txt"
        self.findings = []
        
        # Suur VALVUR logo, mida kuvatakse terminalis ja kirjutatakse raporti päisesse
        self.logo = r"""
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

    def log_finding(self, status, meede, kirjeldus):
        log_line = f"[{status}] [{meede}] {kirjeldus}"
        self.findings.append(log_line)
        print(log_line)

    def audit_linux(self):
        print(self.logo)
        print("[*] Alustan Linuxi süsteemi auditit (E-ITS 2024)...")
        print("-" * 79)
        
        # 1. Meede CON.1.M2 - Tulemüüri (UFW) kontroll
        try:
            ufw_status = subprocess.check_output(["sudo", "ufw", "status"], stderr=subprocess.STDOUT).decode()
            if "inactive" in ufw_status.lower():
                self.log_finding("CRITICAL", "CON.1.M2 (Võrgutulemüür)", "Kohalik tulemüür UFW on DEAKTIVEERITUD! Süsteem on võrgus haavatav.")
            else:
                self.log_finding("OK", "CON.1.M2 (Võrgutulemüür)", "UFW tulemüür on aktiivne. Kontrolli lubatud porte manuaalselt (netstat).")
        except Exception as e:
            self.log_finding("ERROR", "CON.1.M2", f"Ei saanud UFW staatust kontrollida: {str(e)}")

        # 2. Meede SYS.1.3.M1 - /tmp kausta failiõigused ja käivituspiirangud
        if os.path.exists("/tmp"):
            mode = os.stat("/tmp").st_mode
            if not (mode & 0o1000): # Sticky bit puudu
                self.log_finding("HIGH", "SYS.1.3.M1 (Linuxi turve)", "/tmp kaustal puudub Sticky Bit! Kasutajad saavad üksteise faile kustutada.")
            else:
                self.log_finding("OK", "SYS.1.3.M1 (Linuxi turve)", "/tmp kausta Sticky Bit on korras.")

        # 3. Meede ORP.4.M22.S1 - Veebirakenduse logide asukoht (/var/www auditeerimine)
        web_root = "/var/www/html"
        if os.path.exists(web_root):
            self.log_finding("INFO", "ORP.4.M22.S1 (Logid)", f"Veebijuurikas {web_root} tuvastatud. Kontrolli käsitsi 'mc' abil rakenduse siseseid logisid ja õigusi.")
            
        self.kirjuta_raport()

    def audit_windows(self):
        print(self.logo)
        print("[*] Alustan Windowsi süsteemi auditit (E-ITS 2024)...")
        print("-" * 79)
        
        # 1. Meede CON.1.M2 - Windows Firewall staatus
        try:
            fw_check = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles", "state"]).decode(errors='ignore')
            if "OFF" in fw_check:
                self.log_finding("CRITICAL", "CON.1.M2 (Võrgutulemüür)", "Windows Firewall on profiilides VÄLJA LÜLITATUD!")
            else:
                self.log_finding("OK", "CON.1.M2 (Võrgutulemüür)", "Windows Firewall on aktiivne.")
        except Exception as e:
            self.log_finding("ERROR", "CON.1.M2", f"Tulemüüri kontroll ebaõnnestus: {str(e)}")

        # 2. Meede SYS.1.1.M1 / ORP.4.M22.A6 - Avatud võrgujagamised (SMB shares)
        try:
            shares = subprocess.check_output(["net", "share"]).decode(errors='ignore')
            self.log_finding("INFO", "SYS.1.1.M1 (Ühiskasutus)", "Aktiivsed võrgujagamised kaardistatud. Kontrolli õigusi (compmgmt.msc).")
        except Exception as e:
            self.log_finding("ERROR", "SYS.1.1.M1", f"Võrgujagamiste kontroll nurjus: {str(e)}")

        self.kirjuta_raport()

    def annotations_header(self, f):
        f.write("===============================================================================\n")
        f.write(f"|  PROJEKT:     VALVUR - Intsidendi süvaanalüüs                               |\n")
        f.write(f"|  RAPORT:      E-ITS 2024 VASTAVUSRAPORT                                     |\n")
        f.write(f"|  MEESKOND:    TEAM 10                                                       |\n")
        f.write(f"|  GENEREERITUD: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<61} |\n")
        f.write("===============================================================================\n\n")

    def kirjuta_raport(self):
        with open(self.report_path, "w", encoding="utf-8") as f:
            f.write(self.logo + "\n")
            self.annotations_header(f)
            for finding in self.findings:
                f.write(finding + "\n")
        print("-" * 79)
        print(f"[+] Audit lõpetatud! Raport salvestatud asukohta: {self.report_path}")

if __name__ == "__main__":
    auditor = EITSAuditor()
    if auditor.os_type == "Linux":
        auditor.audit_linux()
    elif auditor.os_type == "Windows":
        auditor.audit_windows()
    else:
        print(f"[-] Toetamata operatsioonisüsteem: {auditor.os_type}")
