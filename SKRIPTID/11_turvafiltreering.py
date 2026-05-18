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
#   |   FAILI NIMI:  11_turvafiltreering.py                               |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Kriitiliste sündmuste eraldamine logidest.           |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import csv

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

logger = utils.setup_logging("FILTRERING")

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

def filter_security_events():
    print(LOGO)
    in_dir = utils.get_output_dir()
    out_file = os.path.join(in_dir, '11_tulemus_turvafiltreering.csv')
    # Uuendatud ja täispikk kriitiliste sündmuste nimekiri vastavalt SOC standardile
critical_ids = [
    # --- Minu algsed baas-ID-d ---
    4624,  # Edukas sisselogimine (Successful logon)
    4625,  # Ebaõnnestunud sisselogimine (Failed logon)
    4672,  # Administraatori õiguste määramine sisselogimisel (Admin logon)
    4720,  # Uue kasutajakonto loomine (User account created)
    4732,  # Kasutaja lisamine kohalikku turvagruppi (nt Administrators)
    4739,  # Domeeni või auditeerimise poliitika muutmine
    4688,  # Uue protsessi loomine / käivitamine (Process creation)
    1102,  # Security logi tühjendamine (Audit log cleared - Anti-forensics)
    4104,  # PowerShell skriptiploki käivitamine ja sisu logimine (Script Block)
    1000,  # Üldine Linuxi süsteemne sündmus / kaardistus sinu koodis
    
    # --- Uued täiendused leitud dokumendist ---
    4648,  # Sisselogimine eksplitsiitsete kredentsiaalidega (Pass-the-Hash tuvastus)
    4768,  # Kerberos TGT (Ticket Granting Ticket) taotlus (Kerberoasting ründed)
    4769,  # Kerberos teenusepileti taotlus (Külgsuunaline liikumine ehk Lateral Movement)
    4776,  # NTLM autentimise kontrollimine domeenikontrolleri poolt (Brute-force)
    4778,  # RDP sessiooni taasühendamine (Sessiooni kaaperdamine / liikumine)
    4779,  # RDP sessiooni katkestamine (Session disconnected)
    104,   # System logifaili tühjendamine (System log cleared - Anti-forensics)
    4719,  # Süsteemse auditeerimispoliitika muutmine (Logimise väljalülitamine)
    1116,  # Windows Defender: Tuvastati pahavara (Malware detected)
    1117,  # Windows Defender: Pahavara tegevus blokeeriti (Malware blocked)
    5007,  # Windows Defender: Seadete muutmine (Tulemüüri/kaitse deaktiveerimise katse)
    4698,  # A scheduled task was created (Ajastatud toiming LOODI)
    4702,  # A scheduled task was updated (Ajastatud toimingut MUUDETI)
    4699,  # A scheduled task was deleted (Ajastatud toiming KUSTUTATI)
    
]
    all_results = []
    if not os.path.exists(in_dir): return
    csv_files = [f for f in os.listdir(in_dir) if f.startswith('raw_eksport_') and f.endswith('.csv')]
    for file_name in csv_files:
        try:
            with open(os.path.join(in_dir, file_name), mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        if int(row['Id']) in critical_ids:
                            row['OriginalLog'] = file_name
                            all_results.append(row)
                    except: continue
        except: continue
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(out_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"VALMIS! Tulemus salvestatud: {out_file}")

if __name__ == "__main__":
    filter_security_events()
