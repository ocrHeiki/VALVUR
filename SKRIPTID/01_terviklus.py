#!/usr/bin/env python3
import os
import sys
import hashlib

# Universaalne utils laadimine
sys.path.append(os.path.join(os.path.dirname(__file__), "."))
try:
    import utils
    logger = utils.setup_logging("TERVIKLUS")
    out_dir = utils.get_output_dir()
except:
    class DummyLogger:
        def info(self, msg): print(f"[INFO] {msg}")
        def warning(self, msg): print(f"[WARN] {msg}")
        def error(self, msg): print(f"[ERROR] {msg}")
    logger = DummyLogger()
    out_dir = "TULEMUSED"

def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def check_all_logs():
    # Kontrollime nii Downloads/LOGID kui ka jooksvat kausta
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(base_dir, "..", "LOGID")
    
    if not os.path.exists(log_dir):
        log_dir = os.path.join(base_dir, "LOGID")
    if not os.path.exists(log_dir):
        log_dir = base_dir # Kui kuskil pole, otsi otse skripti kaustast

    os.makedirs(out_dir, exist_ok=True)
    out_report = os.path.join(out_dir, '01_tulemus_terviklus_raport.txt')

    results = []
    logger.info(f"Arvutan räsid logidele asukohas: {log_dir}")

    for root, dirs, files in os.walk(log_dir):
        if "TULEMUSED" in root: continue # Ära skaneeri tulemusi
        for file in files:
            if file.lower().endswith(('.evtx', '.log', '.syslog')):
                full_path = os.path.join(root, file)
                try:
                    file_hash = calculate_sha256(full_path)
                    results.append(f"{file}: {file_hash}")
                    print(f"  [OK] {file}")
                except Exception as e:
                    logger.error(f"Räsi arvutamine ebaõnnestus {file}: {e}")

    if results:
        with open(out_report, 'w', encoding='utf-8') as f:
            f.write("VALVUR - LOGIDE TERVIKLUSE RAPORT (SHA-256)\n")
            f.write("="*60 + "\n")
            for res in results:
                f.write(res + "\n")
        logger.info(f"Tervikluse raport loodud: {out_report}")
    else:
        logger.warning("Ühtegi logifaili ei leitud räsimiseks.")

if __name__ == "__main__":
    check_all_logs()
