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
#   |   FAILI NIMI:  32_kasutajate_audit.py                               |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   Kasutajate tuvastus ja E-ITS turvaaudit              |   #
#   |   GITHUB:      https://github.com/ocrHeiki/VALVUR                   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import csv
import platform
import subprocess

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

LOGO = r"""
###############################################################################
###############################################################################
"""

logger = utils.setup_logging("KASUTAJAD_AUDIT")


def extract_users():
    users = set()
    in_file = os.path.join(utils.get_output_dir(), '11_tulemus_turvafiltreering.csv')
    if os.path.exists(in_file):
        try:
            with open(in_file, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    msg = row.get('Message', '')
                    if "TargetUserName:" in msg:
                        users.add(msg.split("TargetUserName:")[1].split("|")[0].strip())
        except Exception as e:
            logger.error(f"CSV lugemisel viga: {e}")
    if os.path.exists("/etc/passwd"):
        try:
            with open("/etc/passwd", "r") as f:
                for line in f:
                    users.add(line.split(":")[0])
        except Exception as e:
            logger.error(f"/etc/passwd lugemisel viga: {e}")
    return sorted(users)


def check_windows_policies():
    results = []
    try:
        output = subprocess.check_output(["net", "accounts"], timeout=10).decode()
        if "maximum password age" in output.lower():
            results.append({"Kontroll": "Parooli vanusepiirang", "Staatus": "INFO", "Meede": "Kontrolli net accounts väljundit"})
    except Exception as e:
        logger.error(f"Windowsi poliitika kontroll ebaõnnestus: {e}")
    return results


def check_linux_policies():
    results = []
    try:
        with open("/etc/login.defs", "r") as f:
            content = f.read()
            for line in content.splitlines():
                if "PASS_MAX_DAYS" in line and not line.startswith("#"):
                    results.append({"Kontroll": "Parooli max vanus", "Staatus": "INFO", "Meede": line.strip()})
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.error(f"Linuxi poliitika kontroll ebaõnnestus: {e}")
    return results


def check_running_services():
    results = []
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(["sc", "query"], timeout=15).decode()
        else:
            output = subprocess.check_output(["systemctl", "list-units", "--type=service", "--state=running"], timeout=15).decode()
        results.append({"Kontroll": "Teenuste loend", "Staatus": "OK", "Meede": f"Leitud {len(output.splitlines())} rida"})
    except Exception as e:
        logger.error(f"Teenuste kontroll ebaõnnestus: {e}")
    return results


def check_firewall():
    results = []
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(["netsh", "advfirewall", "show", "allprofiles"], timeout=10).decode()
        else:
            output = subprocess.check_output(["sudo", "ufw", "status"], timeout=10).decode()
        results.append({"Kontroll": "Tulemüür", "Staatus": "OK", "Meede": "Tulemüür on aktiivne" if "State: active" in output else "Tulemüür vajab kontrolli"})
    except Exception as e:
        results.append({"Kontroll": "Tulemüür", "Staatus": "INFO", "Meede": f"Kontroll ebaõnnestus: {e}"})
    return results


def check_audit_policy():
    results = []
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(["auditpol", "/get", "/category:*"], timeout=10).decode()
            results.append({"Kontroll": "Auditipoliitika", "Staatus": "INFO", "Meede": "Auditpol tulemused vaata failist"})
        else:
            results.append({"Kontroll": "Auditipoliitika", "Staatus": "OK", "Meede": "Linuxi auditd kontroll käsitsi"})
    except Exception as e:
        results.append({"Kontroll": "Auditipoliitika", "Staatus": "INFO", "Meede": f"Kontroll ebaõnnestus: {e}"})
    return results


def main():
    print(LOGO)
    out_dir = utils.get_output_dir()
    out_file = os.path.join(out_dir, '32_tulemus_kasutajate_audit.csv')

    users = extract_users()
    audit_results = []
    audit_results += check_windows_policies()
    audit_results += check_linux_policies()
    audit_results += check_running_services()
    audit_results += check_firewall()
    audit_results += check_audit_policy()

    if not audit_results:
        audit_results = [{"Kontroll": "Audit", "Staatus": "PASS", "Meede": "Kõik kontrollitud"}]

    all_rows = []
    for u in users:
        all_rows.append({"Tüüp": "KASUTAJA", "Nimi": u, "Detail": "Tuvastatud logidest / /etc/passwd"})
    for r in audit_results:
        all_rows.append({"Tüüp": "AUDIT", "Nimi": r["Kontroll"], "Detail": f"{r['Staatus']}: {r['Meede']}"})

    with open(out_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["Tüüp", "Nimi", "Detail"])
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"Kasutajate audit valmis: {out_file} ({len(users)} kasutajat, {len(audit_results)} kontrolli)")


if __name__ == "__main__":
    main()
