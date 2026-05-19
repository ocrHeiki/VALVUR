#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
###############################################################################
#                                                                             #
#   VALVUR - Ühised tugifunktsioonid ja forensiline andmemudel                #
#                                                                             #
#   KIRJELDUS: Tagab ühtse väljundkausta halduse, lokaalse võrgutuvastuse     #
#              ilma internetita ja püsiva logimise auditijälje jaoks.         #
#                                                                             #
###############################################################################
"""

import os
import sys
import logging
import platform
import socket
from datetime import datetime

class ValvurEvent:
    """Ühtne andmemudel küberintsidentide sündmuste kirjeldamiseks."""
    __slots__ = ['timestamp', 'source', 'event_id', 'severity', 'description', 'mitre_id']
    
    def __init__(self, timestamp, source, event_id, severity, description, mitre_id="N/A"):
        self.timestamp = timestamp
        self.source = source
        self.event_id = event_id
        self.severity = severity
        self.description = description
        self.mitre_id = mitre_id

    def to_dict(self):
        return {
            "Aeg": self.timestamp,
            "Allikas": self.source,
            "ID": self.event_id,
            "Tase": self.severity,
            "Kirjeldus": self.description,
            "MITRE": self.mitre_id
        }


def get_output_dir():
    """Tagastab tsentraalselt määratud väljundkausta tõendite salvestamiseks."""
    out_dir = os.environ.get("VALVUR_OUT")
    
    if not out_dir:
        # Kui keskkonnamuutujat pole, loome kausta tööriista juurkataloogi
        base_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(base_dir, "TULEMUSED")
    
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def setup_logging(name):
    """Seadistab logimise, mis kirjutab paralleelselt konsooli ja faili."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
        
        # 1. Konsooliväljund uurijale reaalis jälgimiseks
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
        # 2. Püsiv logifail väljundkaustas (auditijälg tegevuse kohta)
        try:
            logi_kaust = get_output_dir()
            logi_fail = os.path.join(logi_kaust, "valvur_täitmine.log")
            fh = logging.FileHandler(logi_fail, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"[!] HOIATUS: Logifaili loomine ebaõnnestus: {e}", file=sys.stderr)
            
    return logger


def ensure_folders(base_dir):
    """Veendub vajalike forensiliste alamkaustade olemasolus."""
    for folder in ["LOGID", "TULEMUSED"]:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)


def get_local_subnet():
    """
    Tuvastab masina aktiivse kohaliku alamvõrgu lokaalselt.
    Töötab lollikindlalt ka täielikus võrguisolatsioonis (Air-Gap).
    """
    try:
        # 1. Proovime leida kohaliku IP ilma reaalselt pakette välja saatmata
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Kasutame privaatset IP-aadressi, mis ei tekita liiklust välisvõrku
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        
        if ip != "127.0.0.1":
            return ".".join(ip.split(".")[:-1]) + ".0/24"
    except Exception:
        pass

    # 2. Alternatiivne tuvastus operatsioonisüsteemi hostname kaudu
    try:
        lokaalne_nimi = socket.gethostname()
        ip_nimekiri = socket.getaddrinfo(lokaalne_nimi, None)
        for item in ip_nimekiri:
            ip_kandidaat = item[4][0]
            # Välistame IPv6 ja loopback aadressid
            if ":" not in ip_kandidaat and not ip_kandidaat.startswith("127."):
                return ".".join(ip_kandidaat.split(".")[:-1]) + ".0/24"
    except Exception:
        pass

    # Vaikeväärtus, kui ühtegi reaalset liidest ei tuvastatud
    return "192.168.1.0/24"
