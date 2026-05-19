#!/usr/bin/env python3
import os
import sys
import json
import re
import requests
from urllib.parse import unquote

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("THREAT_INTEL")
    out_dir = utils.get_output_dir()
except:
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()
    out_dir = "TULEMUSED"

LOGO = r"""
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
###############################################################################
"""

# API võtmete laadimine keskkonnamuutujatest (soovitatav CI/CD ja automatiseerimise jaoks)
ABUSEIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")
VIRUSTOTAL_API_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")

# Standardne User-Agent, et vältida skriptide kohest blokeerimist avalike teenuste poolt
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) VALVUR/2.0"}

def get_api_keys_interactive():
    """Küsib võtmeid interaktiivselt ainult siis, kui keskkonnamuutujad on tühjad ja on aktiivne terminal."""
    global ABUSEIPDB_API_KEY, VIRUSTOTAL_API_KEY

    # Kontrollime, kas skript töötab interaktiivses terminalis (mitte taustal/cronis)
    if not sys.stdin.isatty():
        return

    if not ABUSEIPDB_API_KEY or not VIRUSTOTAL_API_KEY:
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
    """Kontrollib IP-aadressi mainet globaalsetes ohubaasides."""
    # Filtreerime välja lokaalsed IP-aadressid enne päringute tegemist
    if ip_address.startswith(("127.", "192.168.", "10.")) or re.match(r'^172\.(1[6-9]|2[0-9]|3[0-1])\.', ip_address):
        return {"IP": ip_address, "Režiim": "Lokaalne", "Sõnum": "Sisevõrgu IP-aadress (Luurest jäetud välja)"}

    print(f"    [>] Analüüsin IP-aadressi: {ip_address}")

    # 1. Prioriteet: AbuseIPDB (kui võti on olemas)
    if ABUSEIPDB_API_KEY:
        url = 'https://api.abuseipdb.com/api/v2/check'
        headers = {'Accept': 'application/json', 'Key': ABUSEIPDB_API_KEY, **HEADERS}
        params = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
        try:
            res = requests.get(url, headers=headers, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json().get('data', {})
                return {
                    "IP": ip_address,
                    "Režiim": "API (AbuseIPDB)",
                    "Ohutase (Abuse Score)": f"{data.get('abuseConfidenceScore', 0)}%",
                    "Riik/Rahvus": data.get('countryCode', 'Teadmata'),
                    "ISP/Sõlm": data.get('isp', 'Teadmata'),
                    "Tüüp": data.get('usageType', 'Teadmata')
                }
        except Exception as e:
            logger.warning(f"AbuseIPDB päring ebaõnnestus IP-le {ip_address}: {e}")

    # 2. Fallback: Tasuta IP-API uuring koos VPN/Proxy tuvastusega
    try:
        res = requests.get(f"http://ip-api.com/json/{ip_address}?fields=status,country,countryCode,isp,proxy,hosting", headers=HEADERS, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                tuyp = "Tavaline kliendi/asutuse IP"
                if data.get("proxy") or data.get("hosting"):
                    tuyp = "⚠️ VPN / Proxy / Pilveserver (Ründaja proovib ennast varjata!)"
                return {
                    "IP": ip_address,
                    "Režiim": "Võtmeta (Avalik luure)",
                    "Ohutase (Abuse Score)": "Teadmata (Võti puudub)",
                    "Riik/Rahvus": f"{data.get('country', 'Teadmata')} ({data.get('countryCode', '??')})",
                    "ISP/Sõlm": data.get('isp', 'Teadmata'),
                    "Tüüp": tuyp
                }
    except Exception as e:
        return {"IP": ip_address, "Viga": f"IP avalik analüüs ebaõnnestus: {str(e)}"}

    return {"IP": ip_address, "Tulemus": "Andmeid ei suudetud hankida."}

def check_hash_osint(file_hash):
    """Kontrollib failiräsi (MD5/SHA1/SHA256) pahavara andmebaasidest."""
    # Puhastame räsi igaks juhuks
    file_hash = file_hash.strip().lower()
    if not re.match(r"^[a-f0-9]{32,64}$", file_hash):
        return {"Räsi": file_hash, "Viga": "Vigane või tundmatu räsi formaat."}

    print(f"    [>] Analüüsin faili räsi: {file_hash}")

    # 1. Prioriteet: VirusTotal v3 API
    if VIRUSTOTAL_API_KEY:
        url = f'https://www.virustotal.com/api/v3/files/{file_hash}'
        headers = {"accept": "application/json", "x-apikey": VIRUSTOTAL_API_KEY, **HEADERS}
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                json_data = res.json()
                stats = json_data.get('data', {}).get('attributes', {}).get('last_analysis_stats', {})
                malicious = stats.get('malicious', 0)
                
                if malicious > 0:
                    tulemus = f"⚠️ KAHJULIK! (Tuvastatud {malicious} viirusetõrje mootori poolt)"
                else:
                    tulemus = "Puhas fail (VirusTotal baasi andmetel)"
                    
                return {
                    "Räsi": file_hash,
                    "Režiim": "API (VirusTotal)",
                    "Tulemus": tulemus,
                    "Pahavara Tüüp": "Kinnitatud oht" if malicious > 0 else "Ohutu"
                }
            elif res.status_code == 404:
                return {"Räsi": file_hash, "Režiim": "API (VirusTotal)", "Tulemus": "Uus või tundmatu fail (Süsteemides pole varem nähtud)."}
        except Exception as e:
            logger.warning(f"VirusTotal päring ebaõnnestus räsile {file_hash}: {e}")

    # 2. Fallback: MalwareBazaar (Tasuta ja piiranguteta pahavaraluure)
    try:
        res = requests.post("https://mb-api.abuse.ch/api/v1/", data={"query": "get_info", "hash": file_hash}, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("query_status") == "ok" and "data" in res_json:
                data = res_json["data"][0]
                return {
                    "Räsi": file_hash,
                    "Režiim": "Võtmeta (MalwareBazaar)",
                    "Tulemus": "⚠️ KAHJULIK! Tuvastatud teadaolev küberründe fail.",
                    "Pahavara Tüüp": f"Perekond: {data.get('signature', 'Teadmata')}"
                }
    except Exception as e:
        logger.error(f"MalwareBazaar päring nurjus räsile {file_hash}: {e}")

    return {"Räsi": file_hash, "Režiim": "Sõltumatu", "Tulemus": "Avalikest andmebaasidest kindlat pahavara vastet ei leitud."}

def check_identity_osint(identity_input):
    """Profileerib kahtlaseid kasutajanimesid või e-maile lekkeandmebaaside kaudu."""
    clean_input = unquote(identity_input).strip()
    print(f"    [>] Profileerin ründaja identiteeti: {clean_input}")

    tuvastatud_andmed = {
        "Sisend": clean_input,
        "Tuvastatud leaks": [],
        "Vihjed profiilile (Vanus/Rahvus)": "Profiil on puhas või tegu on uue ründekontoga."
    }

    # Kasutame tasuta avalikku LeakCheck API-t ründaja profiili rikastamiseks
    url = f"https://api.leakcheck.io/public?check={clean_input}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            res_json = res.json()
            if res_json.get("success"):
                sources = res_json.get("sources", [])
                tuvastatud_andmed["Tuvastatud leaks"] = [s.get('name', 'Tundmatu leke') for s in sources]

                vihjed = []
                sources_str = " ".join(tuvastatud_andmed["Tuvastatud leaks"]).lower()
                
                if any(x in sources_str for x in [".ru", "vkontakte", "yandex", "mail.ru"]):
                    vihjed.append("⚠️ Kõrge tõenäosus: Ründajal on seoseid Vene fookusega platvormidega")
                if any(x in sources_str for x in [".cn", "weibo", "baidu"]):
                    vihjed.append("⚠️ Kõrge tõenäosus: Ründajal on seoseid Hiina fookusega platvormidega")
                if any(x in sources_str for x in ["breached", "raidforums", "exploit.in", "xss"]):
                    vihjed.append("[Aktiivne häkkerifoorumite või lekete keskkondade kasutaja]")

                if vihjed:
                    tuvastatud_andmed["Vihjed profiilile (Vanus/Rahvus)"] = " | ".join(vihjed)
    except Exception as e:
        tuvastatud_andmed["Viga"] = f"Identiteedi profiili koostamine nurjus: {e}"

    return tuvastatud_andmed

def run_osint_enrichment(captured_ips, captured_hashes, captured_identities):
    """Peamine sisenemispunkt andmete rikastamiseks."""
    get_api_keys_interactive()

    osint_raport = {
        "IP_Uuringud": [],
        "Faili_Uuringud": [],
        "Identiteedi_Uuringud": []
    }

    print("\n🚀 [VALVUR FAAS 4: KÄIVITAN AKTIIVSE OSINT VASTULUURE]\n" + "="*60)

    # Dublikaatide eemaldamine unikaalsuse tagamiseks
    unique_ips = list(set([ip for ip in captured_ips if ip]))
    unique_hashes = list(set([h for h in captured_hashes if h]))
    unique_identities = list(set([i for i in captured_identities if i]))

    for ip in unique_ips:
        osint_raport["IP_Uuringud"].append(check_ip_osint(ip))

    for f_hash in unique_hashes:
        osint_raport["Faili_Uuringud"].append(check_hash_osint(f_hash))

    for identity in unique_identities:
        osint_raport["Identiteedi_Uuringud"].append(check_identity_osint(identity))

    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, '33_tulemus_threat_intel_osint.json')
    
    try:
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(osint_raport, f, indent=4, ensure_ascii=False)
        logger.info(f"OSINT rikastamise raport edukalt loodud: {out_file}")
        print(f"\n[✓] OSINT raport salvestatud: {out_file}")
    except Exception as e:
        logger.error(f"OSINT raporti salvestamine ebaõnnestus: {e}")

    print("\n" + "="*60 + "\n[+] Ohuluure ja OSINT analüüs lõpetatud.\n")
    return osint_raport

if __name__ == "__main__":
    print(LOGO)
    # Testandmed kohalikuks kontrolliks
    mock_ips = ["185.220.101.5"]
    mock_hashes = ["44d88612fea8a8f36de82e1278abb02f"]
    mock_identities = ["vladimir34@yandex.ru"]

    raport = run_osint_enrichment(mock_ips, mock_hashes, mock_identities)
    print(json.dumps(raport, indent=4, ensure_ascii=False))
