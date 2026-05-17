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
#   |   FAILI NIMI:  33_threat_intel_osint.py                             |   #
#   |   LOODUD:      2026-05-15                                           |   #
#   |   AUTOR:       Heiki Rebane                                         |   #
#   |   KIRJELDUS:   OSINT & Profiler: AbuseIPDB, VirusTotal, LeakCheck   |   #
#   |                                                                     |   #
#   =======================================================================   #
#                                                                             #
###############################################################################
"""

import os
import sys
import json
import re
import requests
from urllib.parse import unquote

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

ABUSEIPDB_API_KEY = ""
VIRUSTOTAL_API_KEY = ""

def get_api_keys_interactive():
    global ABUSEIPDB_API_KEY, VIRUSTOTAL_API_KEY

    print("\n--- [VALVUR OSINT API SEADISTUS] ---")
    print("Kui sul pole API võtmeid, vajuta Enter - VALVUR jätkab tasuta parsimisrežiimis.")

    if not ABUSEIPDB_API_KEY:
        voti = input("Sisesta AbuseIPDB API võti (või Enter): ").strip()
        if voti: ABUSEIPDB_API_KEY = voti

    if not VIRUSTOTAL_API_KEY:
        voti = input("Sisesta VirusTotal API võti (või Enter): ").strip()
        if voti: VIRUSTOTAL_API_KEY = voti
    print("------------------------------------\n")

def check_ip_osint(ip_address):
    print(f"[*] Analüüsin IP-aadressi: {ip_address}")

    if ABUSEIPDB_API_KEY:
        url = 'https://api.abuseipdb.com/api/v2/check'
        headers = {'Accept': 'application/json', 'Key': ABUSEIPDB_API_KEY}
        params = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
        try:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()['data']
                return {
                    "IP": ip_address,
                    "Režiim": "API (Süvaanalüüs)",
                    "Ohutase (Abuse Score)": f"{data['abuseConfidenceScore']}%",
                    "Riik/Rahvus": data['countryCode'],
                    "ISP/Sõlm": data['isp'],
                    "Tüüp": data['usageType']
                }
        except Exception:
            pass

    try:
        res = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,countryCode,country,regionName,isp,org,mobile,proxy,hosting")
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                tüüp = "Tavaline kliendi IP"
                if data.get("proxy") or data.get("hosting"):
                    tüüp = "⚠️ VPN / Proxy / Pilveserver (Ründaja varjab ennast!)"
                return {
                    "IP": ip_address,
                    "Režiim": "Võtmeta (Avalik luure)",
                    "Ohutase (Abuse Score)": "Teadmata (Võti puudub)",
                    "Riik/Rahvus": f"{data['country']} ({data['countryCode']})",
                    "ISP/Sõlm": data['isp'],
                    "Tüüp": tüüp
                }
    except Exception as e:
        return {"IP": ip_address, "Viga": f"IP analüüs ebaõnnestus: {str(e)}"}

def check_hash_osint(file_hash):
    print(f"[*] Analüüsin faili räsi: {file_hash}")

    if VIRUSTOTAL_API_KEY:
        url = f'https://www.virustotal.com/api/v3/files/{file_hash}'
        headers = {"accept": "application/json", "x-apikey": VIRUSTOTAL_API_KEY}
        try:
            res = requests.get(url, headers=headers)
            if res.status_code == 200:
                stats = res.json()['data']['attributes']['last_analysis_stats']
                return {
                    "Räsi": file_hash,
                    "Režiim": "API (VirusTotal)",
                    "Tulemus": f"⚠️ KAHJULIK! (Tuvastatud {stats['malicious']} viirusetõrje poolt)",
                    "Pahavara Tüüp": "Kinnitatud oht"
                }
            elif res.status_code == 404:
                return {"Räsi": file_hash, "Režiim": "API", "Tulemus": "Puhas või uus tundmatu fail (Süsteemides pole varem nähtud)"}
        except Exception:
            pass

    try:
        res = requests.post("https://mb-api.abuse.ch/api/v1/", data={"query": "get_info", "hash": file_hash})
        if res.status_code == 200 and res.json().get("query_status") == "ok":
            data = res.json()["data"][0]
            return {
                "Räsi": file_hash,
                "Režiim": "Võtmeta (MalwareBazaar)",
                "Tulemus": "⚠️ KAHJULIK! Tuvastatud küberründe fail.",
                "Pahavara Tüüp": f"Perekond: {data.get('signature', 'Teadmata')}"
            }
        else:
            return {"Räsi": file_hash, "Režiim": "Võtmeta", "Tulemus": "Avalikest andmebaasidest kindlat pahavara vastet ei leitud."}
    except Exception as e:
        return {"Räsi": file_hash, "Viga": f"Faili OSINT ebaõnnestus: {str(e)}"}

def check_identity_osint(identity_input):
    print(f"[*] Profileerin ründaja identiteeti: {identity_input}")

    clean_input = unquote(identity_input).strip()

    url = f"https://api.leakcheck.io/public?check={clean_input}"
    tuvastatud_andmed = {
        "Sisend": clean_input,
        "Tuvastatud leaks": [],
        "Vihjed profiilile (Vanus/Rahvus)": "Kogutakse..."
    }

    try:
        res = requests.get(url)
        if res.status_code == 200 and res.json().get("success"):
            sources = res.json().get("sources", [])
            tuvastatud_andmed["Tuvastatud leaks"] = [s['name'] for s in sources]

            for s in tuvastatud_andmed["Tuvastatud leaks"]:
                s_lower = s.lower()
                if ".ru" in s_lower or "vkontakte" in s_lower or "yandex" in s_lower:
                    tuvastatud_andmed["Vihjed profiilile (Vanus/Rahvus)"] = "⚠️ Kõrge tõenäosus: Vene juured / Rahvus (Seos Vene platvormidega)"
                elif ".cn" in s_lower or "weibo" in s_lower:
                    tuvastatud_andmed["Vihjed profiilile (Vanus/Rahvus)"] = "⚠️ Kõrge tõenäosus: Hiina juured / Rahvus"
                elif "breached" in s_lower or "raidforums" in s_lower:
                    tuvastatud_andmed["Vihjed profiilile (Vanus/Rahvus)"] += " [Aktiivne häkkerifoorumite kasutaja]"

            if not sources:
                tuvastatud_andmed["Tulemus"] = "Konto on puhas või tegu on eritellimusel loodud ründeprofiiliga."
        else:
            tuvastatud_andmed["Tulemus"] = "Avalik profiiliotsing ei andnud otseseid tulemusi."

    except Exception as e:
        tuvastatud_andmed["Viga"] = str(e)

    return tuvastatud_andmed

def run_osint_enrichment(captured_ips, captured_hashes, captured_identities):
    get_api_keys_interactive()

    osint_raport = {
        "IP_Uuringud": [],
        "Faili_Uuringud": [],
        "Identiteedi_Uuringud": []
    }

    print("\n🚀 [VALVUR FAAS 4: KÄIVITAN AKTIIVSE OSINT VASTULUURE]\n" + "="*50)

    for ip in captured_ips:
        osint_raport["IP_Uuringud"].append(check_ip_osint(ip))

    for f_hash in captured_hashes:
        osint_raport["Faili_Uuringud"].append(check_hash_osint(f_hash))

    for identity in captured_identities:
        osint_raport["Identiteedi_Uuringud"].append(check_identity_osint(identity))

    out_dir = utils.get_output_dir()
    out_file = os.path.join(out_dir, '33_tulemus_threat_intel_osint.json')
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(osint_raport, f, indent=4, ensure_ascii=False)
    print(f"[+] OSINT raport salvestatud: {out_file}")
    print("\n" + "="*50 + "\n[+] OSINT Süvaanalüüs lõpetatud. Andmed saadetud Faasi 5 (Raporteerimine).\n")
    return osint_raport

if __name__ == "__main__":
    mock_ips = ["185.220.101.5"]
    mock_hashes = ["44d88612fea8a8f36de82e1278abb02f"]
    mock_identities = ["vladimir34@yandex.ru"]

    raport = run_osint_enrichment(mock_ips, mock_hashes, mock_identities)

    print(json.dumps(raport, indent=4, ensure_ascii=False))
