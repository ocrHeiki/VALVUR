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
#   |   KIRJELDUS:   E-ITS 2024 baasturvalisuse kontroll (kesk/standard/  |   #
#   |                kõrg). Analüüsib Windowsi, Linuxi, serveri,          |   #
#   |                tulemüüri ja ruuteri turvaseisundit.                 |   #
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
import socket
import re
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "."))
import utils

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

logger = utils.setup_logging("EITS")

EITS_LEVELS = {
    "kesk": "KESK (M) - Baastase - kohustuslikud meetmed",
    "standard": "STANDARD (A) - Täiendav tase - soovituslikud meetmed",
    "korg": "KÕRG (S) - Kõrge tase - spetsiifilised meetmed"
}

class EITSAuditor:
    def __init__(self):
        self.os_type = platform.system()
        self.hostname = socket.gethostname()
        self.findings = []
        self.summary = {"kesk": {"OK": 0, "CRITICAL": 0, "HIGH": 0, "INFO": 0, "POLE KONTROLLITUD": 0},
                        "standard": {"OK": 0, "CRITICAL": 0, "HIGH": 0, "INFO": 0, "POLE KONTROLLITUD": 0},
                        "korg": {"OK": 0, "CRITICAL": 0, "HIGH": 0, "INFO": 0, "POLE KONTROLLITUD": 0}}
        self.role = self._detect_role()

    def _detect_role(self):
        role = "TÖÖJAAM"
        host = self.hostname.lower()
        if any(x in host for x in ["dc", "domain", "ad"]):
            role = "SERVER (DC)"
        elif any(x in host for x in ["server", "file", "nas"]):
            role = "SERVER (faili-/rakendusserver)"
        elif any(x in host for x in ["ruuter", "router", "gateway", "gw"]):
            role = "RUUTER"
        elif any(x in host for x in ["tulemuur", "firewall", "fw"]):
            role = "TULEMÜÜR"
        elif any(x in host for x in ["kali", "kali"]):
            role = "RÜNDAJA (Kali)"
        elif any(x in host for x in ["client", "workstation", "pc"]):
            role = "TÖÖJAAM (klient)"
        if os.path.exists("/etc/openwrt_release") or os.path.exists("/etc/lede_release"):
            role = "RUUTER (OpenWrt)"
        try:
            if os.name == "nt":
                output = subprocess.check_output(["nltest", "/DSREGINFO"], stderr=subprocess.DEVNULL, timeout=5).decode(errors="ignore")
                if "DC" in output or "Domain Controller" in output:
                    role = "SERVER (DC)"
            else:
                if os.path.exists("/etc/samba/smb.conf"):
                    with open("/etc/samba/smb.conf") as f:
                        if "domain controller" in f.read().lower():
                            role = "SERVER (DC)"
        except Exception:
            pass
        return role

    def log_finding(self, status, meede, eits_tase, kirjeldus, soovitus=""):
        log_line = f"[{status:<8}] [{meede:<20}] [{eits_tase:<5}] {kirjeldus}"
        if soovitus:
            log_line += f" | SOOVITUS: {soovitus}"
        self.findings.append({
            "staatus": status,
            "meede": meede,
            "eits_tase": eits_tase,
            "kirjeldus": kirjeldus,
            "soovitus": soovitus
        })
        if eits_tase in self.summary:
            if status in self.summary[eits_tase]:
                self.summary[eits_tase][status] += 1
        print(log_line)

    def run_cmd(self, cmd, timeout=10):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return ""
        except FileNotFoundError:
            return ""
        except PermissionError:
            return ""
        except Exception:
            return ""

    def audit_linux(self):
        print(f"\n[*] Linuxi süsteemi audit (E-ITS 2024) - roll: {self.role}")
        print("-" * 79)

        self._linux_firewall()
        self._linux_tmp_sticky()
        self._linux_password_policy()
        self._linux_ssh()
        self._linux_auditd()
        self._linux_updates()
        self._linux_selinux_apparmor()
        self._linux_services()
        self._linux_sysctl()
        self._linux_sudo()
        self._linux_fail2ban()
        self._linux_aide()
        self._linux_malware_scan()

    def _linux_firewall(self):
        ufw = self.run_cmd(["sudo", "ufw", "status"])
        iptables = self.run_cmd(["sudo", "iptables", "-L", "-n"])
        nftables = self.run_cmd(["sudo", "nft", "list", "ruleset"])

        if "active" in ufw.lower() and "Status: active" in ufw:
            self.log_finding("OK", "CON.1.M2 (Tulemüür)", "kesk",
                           "UFW tulemüür on aktiivne")
        elif "Status: active" in ufw:
            self.log_finding("OK", "CON.1.M2 (Tulemüür)", "kesk",
                           "UFW tulemüür on aktiivne")
        elif iptables and "Chain" in iptables:
            self.log_finding("OK", "CON.1.M2 (Tulemüür)", "kesk",
                           "iptables reeglid on aktiivsed (UFW puudub)")
        elif "table ip" in nftables or "table inet" in nftables:
            self.log_finding("OK", "CON.1.M2 (Tulemüür)", "kesk",
                           "nftables reeglid on aktiivsed")
        else:
            self.log_finding("CRITICAL", "CON.1.M2 (Tulemüür)", "kesk",
                           "Tulemüür EI OLE aktiivne! Süsteem on võrgus kaitsmata.",
                           "Paigalda ja konfigureeri UFW või iptables")

        if iptables:
            policy_accept = iptables.count("Chain") > 0
            if "policy ACCEPT" in iptables:
                self.log_finding("INFO", "CON.1.M1 (Võrgu segmenteerimine)", "standard",
                               "Mõne iptables ahela vaikepoliitika on ACCEPT - lubab kogu liiklust",
                               "Muuda vaikepoliitikad väärtuseks DROP")

    def _linux_tmp_sticky(self):
        checks = [
            ("/tmp", "SYS.1.3.M1 (/tmp kaitse)", "kesk",
             "/tmp kaust", "Paigalda sticky bit: chmod +t /tmp"),
            ("/var/tmp", "SYS.1.3.M1 (/var/tmp kaitse)", "kesk",
             "/var/tmp kaust", "Paigalda sticky bit: chmod +t /var/tmp"),
            ("/dev/shm", "SYS.1.3.M1 (/dev/shm kaitse)", "korg",
             "/dev/shm kaust", "Paigalda sticky bit: chmod +t /dev/shm"),
        ]
        for path, meede, tase, desc, sov in checks:
            if os.path.exists(path):
                mode = os.stat(path).st_mode
                if not (mode & 0o1000):
                    self.log_finding("HIGH", meede, tase,
                                   f"{desc} puudub Sticky Bit! Kasutajad saavad üksteise faile kustutada.", sov)
                else:
                    self.log_finding("OK", meede, tase, f"{desc} Sticky Bit on korras")

    def _linux_password_policy(self):
        if os.path.exists("/etc/login.defs"):
            try:
                with open("/etc/login.defs") as f:
                    content = f.read()
                max_days = 99999
                min_days = 0
                warn_age = 7
                for line in content.splitlines():
                    if line.startswith("PASS_MAX_DAYS"):
                        max_days = int(line.split()[-1])
                    elif line.startswith("PASS_MIN_DAYS"):
                        min_days = int(line.split()[-1])
                    elif line.startswith("PASS_WARN_AGE"):
                        warn_age = int(line.split()[-1])
                if max_days > 90:
                    self.log_finding("HIGH", "ORP.4.A1 (Paroolipoliitika)", "kesk",
                                   f"PASS_MAX_DAYS={max_days} päeva (soovitus: <=90)",
                                   "Muuda /etc/login.defs: PASS_MAX_DAYS 90")
                else:
                    self.log_finding("OK", "ORP.4.A1 (Paroolipoliitika)", "kesk",
                                   f"PASS_MAX_DAYS={max_days} (korras)")
                if min_days < 1:
                    self.log_finding("INFO", "ORP.4.A1 (Paroolipoliitika)", "standard",
                                   f"PASS_MIN_DAYS={min_days} (soovitus: >=1)",
                                   "Muuda: PASS_MIN_DAYS 1")
                if warn_age < 7:
                    self.log_finding("INFO", "ORP.4.A1 (Paroolipoliitika)", "standard",
                                   f"PASS_WARN_AGE={warn_age} (soovitus: >=7)",
                                   "Muuda: PASS_WARN_AGE 7")
            except Exception as e:
                self.log_finding("ERROR", "ORP.4.A1 (Paroolipoliitika)", "kesk",
                               f"/etc/login.defs lugemisviga: {e}")
        if self.run_cmd(["which", "chage"]):
            try:
                output = subprocess.check_output(["chage", "-l", "root"], timeout=5).decode(errors="ignore")
                if "never" in output.lower() or "does not expire" in output.lower():
                    self.log_finding("INFO", "ORP.4.A1 (Root parool)", "standard",
                                   "Root kasutaja paroolil puudub aegumistähtaeg",
                                   "Kaalu root parooli aegumise seadmist")
            except Exception:
                pass

    def _linux_ssh(self):
        sshd_configs = ["/etc/ssh/sshd_config", "/etc/ssh/sshd_config.d/"]
        found = False
        for cfg in ["/etc/ssh/sshd_config"]:
            if os.path.exists(cfg):
                found = True
                try:
                    with open(cfg) as f:
                        content = f.read()
                    if "PermitRootLogin yes" in content and not content.split("#")[0].count("PermitRootLogin no"):
                        self.log_finding("HIGH", "CON.1.A1 (SSH turve)", "standard",
                                       "SSH root sisselogimine on LUBATUD",
                                       "Muuda: PermitRootLogin no")
                    else:
                        self.log_finding("OK", "CON.1.A1 (SSH turve)", "standard",
                                       "SSH root sisselogimine on keelatud")
                    if "PasswordAuthentication yes" in content and not content.split("#")[0].count("PasswordAuthentication no"):
                        self.log_finding("INFO", "CON.1.A1 (SSH autentimine)", "korg",
                                       "SSH parooliga autentimine on lubatud",
                                       "Kaalu SSH võtmega autentimist: PasswordAuthentication no")
                    else:
                        self.log_finding("OK", "CON.1.A1 (SSH autentimine)", "korg",
                                       "SSH parooliga autentimine keelatud (ainult võtmed)")
                    if "Port " in content:
                        for line in content.splitlines():
                            if line.strip().startswith("Port ") and not line.strip().startswith("#"):
                                port = line.split()[-1]
                                if port != "22":
                                    self.log_finding("OK", "CON.1.A1 (SSH port)", "standard",
                                                   f"SSH port on muudetud: {port} (turvalisem)")
                                break
                except Exception as e:
                    self.log_finding("ERROR", "CON.1.A1 (SSH kontroll)", "standard",
                                   f"SSH kontrolli viga: {e}")
        if not found:
            self.log_finding("INFO", "CON.1.A1 (SSH turve)", "standard",
                           "SSH ei tundu olevat paigaldatud või puudub standardne konfiguratsioon")

    def _linux_auditd(self):
        auditd = self.run_cmd(["which", "auditctl"])
        if auditd:
            status = self.run_cmd(["sudo", "auditctl", "-s"])
            if "enabled 1" in status.lower() or "enabled 2" in status.lower():
                self.log_finding("OK", "ORP.4.M22 (auditd)", "kesk",
                               "auditd on aktiivne ja logib sündmusi")
            else:
                self.log_finding("HIGH", "ORP.4.M22 (auditd)", "kesk",
                               "auditd on paigaldatud, kuid MITTE AKTIIVNE",
                               "Käivita: sudo auditctl -e 1")
        else:
            self.log_finding("HIGH", "ORP.4.M22 (auditd)", "kesk",
                           "auditd POLE paigaldatud! Puudub sündmuste logimine",
                           "Paigalda: apt install auditd või yum install audit")
        syslog = self.run_cmd(["which", "rsyslogd"])
        if syslog:
            self.log_finding("OK", "ORP.4.M22 (rsyslog)", "kesk",
                           "rsyslog on paigaldatud")
        journal = self.run_cmd(["which", "journalctl"])
        if journal:
            self.log_finding("OK", "ORP.4.M22 (journald)", "kesk",
                           "systemd-journald on aktiivne")

    def _linux_updates(self):
        pkg_managers = [
            (["which", "apt"], ["apt", "list", "--upgradable"], "APT"),
            (["which", "yum"], ["yum", "check-update"], "YUM"),
            (["which", "dnf"], ["dnf", "check-update"], "DNF"),
            (["which", "zypper"], ["zypper", "list-updates"], "Zypper"),
        ]
        pkg_found = False
        for which_cmd, check_cmd, name in pkg_managers:
            if self.run_cmd(which_cmd):
                pkg_found = True
                updates = self.run_cmd(check_cmd, timeout=30)
                lines = [l for l in updates.splitlines() if l.strip() and not l.startswith("Listing...") and not l.startswith("Reading") and not name == "APT"]
                if name == "APT":
                    count = sum(1 for l in updates.splitlines() if "/" in l and "upgradable" in l)
                elif name in ("YUM", "DNF"):
                    count = len([l for l in updates.splitlines() if l.strip() and not l.startswith(("Loaded", "Last", "Error", "Repositories"))])
                else:
                    count = len([l for l in updates.splitlines() if "|" in l and "patch" in l.lower()])
                if count == 0 or updates.strip() == "":
                    self.log_finding("OK", "SYS.1.3.M3 (Turvauuendused)", "kesk",
                                   f"{name}: turvauuendused on ajakohased")
                else:
                    self.log_finding("INFO", "SYS.1.3.M3 (Turvauuendused)", "kesk",
                                   f"{name}: {count} uuendust on saadaval",
                                   "Käivita: sudo apt upgrade (või vastav paketihaldur)")
                break
        if not pkg_found:
            self.log_finding("INFO", "SYS.1.3.M3 (Turvauuendused)", "kesk",
                           "Paketihaldurit ei tuvastatud")

    def _linux_selinux_apparmor(self):
        selinux = self.run_cmd(["which", "getenforce"])
        if selinux:
            status = self.run_cmd(["sudo", "getenforce"]).strip()
            if status == "Enforcing":
                self.log_finding("OK", "SYS.1.3.A1 (SELinux)", "standard",
                               f"SELinux: {status}")
            elif status == "Permissive":
                self.log_finding("HIGH", "SYS.1.3.A1 (SELinux)", "standard",
                               f"SELinux: {status} - ainult logib, EI KAITSE",
                               "Muuda: setenforce 1 ja /etc/selinux/config")
            elif status == "Disabled":
                self.log_finding("HIGH", "SYS.1.3.A1 (SELinux)", "standard",
                               "SELinux on KEELATUD",
                               "Luba SELinux /etc/selinux/config")
        apparmor = self.run_cmd(["which", "aa-status"])
        if apparmor:
            status = self.run_cmd(["sudo", "aa-status"])
            if "apparmor module is loaded" in status:
                self.log_finding("OK", "SYS.1.3.A1 (AppArmor)", "standard",
                               "AppArmor on aktiivne")
            else:
                self.log_finding("HIGH", "SYS.1.3.A1 (AppArmor)", "standard",
                               "AppArmor on paigaldatud, kuid EI OLE AKTIIVNE",
                               "Laadi moodul: sudo systemctl restart apparmor")
        if not selinux and not apparmor:
            self.log_finding("HIGH", "SYS.1.3.A1 (Mandaatjuurdepääsu kontroll)", "standard",
                           "SELinux ega AppArmor pole paigaldatud! Puudub mandaatjuurdepääsu kontroll",
                           "Paigalda SELinux või AppArmor")

    def _linux_services(self):
        services = self.run_cmd(["systemctl", "list-units", "--type=service", "--state=running"], timeout=15)
        lines = [l for l in services.splitlines() if l.strip() and ".service" in l]
        self.log_finding("INFO", "SYS.1.1.A6 (Teenuste audit)", "standard",
                        f"Süsteemil on {len(lines)} teenust töös")
        dangerous_services = ["telnet", "rsh", "rlogin", "vsftpd", "tftp", "nfs-kernel-server"]
        for svc in dangerous_services:
            svc_check = self.run_cmd(["systemctl", "is-active", svc], timeout=5)
            if "active" in svc_check:
                self.log_finding("HIGH", "SYS.1.1.A6 (Ohtlik teenus)", "standard",
                               f"Ohtlik teenus {svc} on AKTIIVNE",
                               "Keela: sudo systemctl disable --now " + svc)
        listening = self.run_cmd(["ss", "-tlnp"])
        if listening:
            ports = re.findall(r":(\d+)", listening)
            open_ports = [int(p) for p in ports if p.isdigit()]
            if open_ports:
                self.log_finding("INFO", "CON.1.M1 (Avatud pordid)", "kesk",
                               f"Avatud TCP pordid: {', '.join(str(p) for p in sorted(set(open_ports)))}")
                if 22 in open_ports:
                    self.log_finding("OK", "CON.1.M1 (SSH port)", "kesk",
                                   "SSH (22) on avatud")
                if 23 in open_ports:
                    self.log_finding("CRITICAL", "CON.1.M1 (Telnet)", "kesk",
                                   "Telnet (23) on avatud! Krüpteerimata ühendus",
                                   "Keela telnet ja kasuta SSHd")
                if 21 in open_ports:
                    self.log_finding("HIGH", "CON.1.M1 (FTP)", "standard",
                                   "FTP (21) on avatud - krüpteerimata andmeedastus",
                                   "Kasuta SFTP või FTPS")

    def _linux_sysctl(self):
        ip_forward = self.run_cmd(["sysctl", "-n", "net.ipv4.ip_forward"]).strip()
        if ip_forward == "1":
            self.log_finding("INFO", "NET.1.M1 (IP edastamine)", "standard",
                           "IP edastamine (ip_forward) on LUBATUD - süsteem toimib ruuterina",
                           "Kui pole vaja, keela: sysctl -w net.ipv4.ip_forward=0")
        icmp_redirect = self.run_cmd(["sysctl", "-n", "net.ipv4.conf.all.accept_redirects"]).strip()
        if icmp_redirect == "1":
            self.log_finding("INFO", "NET.1.M1 (ICMP redirect)", "standard",
                           "ICMP redirectite vastuvõtmine on LUBATUD (MITM risk)",
                           "Keela: sysctl -w net.ipv4.conf.all.accept_redirects=0")
        tcp_syncookies = self.run_cmd(["sysctl", "-n", "net.ipv4.tcp_syncookies"]).strip()
        if tcp_syncookies == "1":
            self.log_finding("OK", "NET.1.M1 (SYN flood kaitse)", "kesk",
                           "TCP SYN cookies on aktiivne (kaitse SYN flood rünnete vastu)")
        else:
            self.log_finding("HIGH", "NET.1.M1 (SYN flood kaitse)", "kesk",
                           "TCP SYN cookies EI OLE aktiivne",
                           "Luba: sysctl -w net.ipv4.tcp_syncookies=1")

    def _linux_sudo(self):
        sudoers = self.run_cmd(["sudo", "cat", "/etc/sudoers"])
        if "NOPASSWD" in sudoers and "ALL" in sudoers:
            self.log_finding("HIGH", "ORP.4.A2 (Sudo õigused)", "korg",
                           "Leitud laiaulatuslik NOPASSWD reegel sudoersis",
                           "Eemalda laiad NOPASSWD reeglid, kasuta täpseid õigusi")

    def _linux_fail2ban(self):
        fail2ban = self.run_cmd(["which", "fail2ban-client"])
        if fail2ban:
            status = self.run_cmd(["sudo", "fail2ban-client", "status"], timeout=5)
            if "|- Number of jail:" in status:
                self.log_finding("OK", "CON.1.A1 (Fail2ban)", "standard",
                               "Fail2ban on aktiivne ja kaitseb SSH-d")
            else:
                self.log_finding("INFO", "CON.1.A1 (Fail2ban)", "standard",
                               "Fail2ban on paigaldatud kuid ei pruugi olla aktiivne",
                               "Käivita: sudo systemctl start fail2ban")
        else:
            self.log_finding("INFO", "CON.1.A1 (Fail2ban)", "standard",
                           "Fail2ban pole paigaldatud",
                           "Kaalu paigaldamist: apt install fail2ban")

    def _linux_aide(self):
        aide = self.run_cmd(["which", "aide"])
        if aide:
            self.log_finding("OK", "SYS.1.3.A1 (AIDE)", "korg",
                           "AIDE failide tervikluse kontroll on paigaldatud")
        tripwire = self.run_cmd(["which", "tripwire"])
        if tripwire:
            self.log_finding("OK", "SYS.1.3.A1 (Tripwire)", "korg",
                           "Tripwire failide tervikluse kontroll on paigaldatud")
        if not aide and not tripwire:
            self.log_finding("INFO", "SYS.1.3.A1 (Failide terviklus)", "korg",
                           "Failide tervikluse kontroll (AIDE/Tripwire) pole paigaldatud",
                           "Kaalu paigaldamist: apt install aide")

    def _linux_malware_scan(self):
        clamav = self.run_cmd(["which", "clamscan"])
        if clamav:
            self.log_finding("OK", "SYS.1.1.M1 (Viirustõrje)", "kesk",
                           "ClamAV on paigaldatud")
        chkrootkit = self.run_cmd(["which", "chkrootkit"])
        if chkrootkit:
            self.log_finding("OK", "SYS.1.1.M1 (Rootkit tuvastus)", "standard",
                           "chkrootkit on paigaldatud")
        rkhunter = self.run_cmd(["which", "rkhunter"])
        if rkhunter:
            self.log_finding("OK", "SYS.1.1.M1 (Rootkit tuvastus)", "standard",
                           "rkhunter on paigaldatud")

    def audit_windows(self):
        print(f"\n[*] Windowsi süsteemi audit (E-ITS 2024) - roll: {self.role}")
        print("-" * 79)

        self._windows_firewall()
        self._windows_defender()
        self._windows_password_policy()
        self._windows_audit_policy()
        self._windows_smb()
        self._windows_rdp()
        self._windows_updates()
        self._windows_services()
        self._windows_shares()
        self._windows_uac()
        self._windows_admin_accounts()
        self._windows_winrm()

    def _windows_firewall(self):
        fw = self.run_cmd(["netsh", "advfirewall", "show", "allprofiles", "state"])
        if "OFF" in fw.upper():
            self.log_finding("CRITICAL", "CON.1.M2 (Windows Firewall)", "kesk",
                           "Windows Firewall on VÄLJA LÜLITATUD kõigis profiilides!",
                           "Luba: netsh advfirewall set allprofiles state on")
        elif "ON" in fw.upper():
            self.log_finding("OK", "CON.1.M2 (Windows Firewall)", "kesk",
                           "Windows Firewall on aktiivne")
        else:
            profiles = {"Domain": "ON", "Private": "ON", "Public": "ON"}
            for line in fw.splitlines():
                for p in profiles:
                    if p in line:
                        if "OFF" in line.upper():
                            profiles[p] = "OFF"
            off_profiles = [p for p, v in profiles.items() if v == "OFF"]
            if off_profiles:
                self.log_finding("HIGH", "CON.1.M2 (Windows Firewall)", "kesk",
                               f"Tulemüür on VÄLJA LÜLITATUD profiilis: {', '.join(off_profiles)}",
                               "Luba: netsh advfirewall set <profiil> state on")
            else:
                self.log_finding("OK", "CON.1.M2 (Windows Firewall)", "kesk",
                               "Windows Firewall on aktiivne")

    def _windows_defender(self):
        mp = self.run_cmd(["powershell", "-Command", "Get-MpComputerStatus | Select-Object -Property RealTimeProtectionEnabled, AntivirusEnabled"], timeout=15)
        if "True" in mp:
            self.log_finding("OK", "SYS.1.1.M1 (Windows Defender)", "kesk",
                           "Windows Defender reaalajakaitse on AKTIIVNE")
        elif "False" in mp:
            self.log_finding("HIGH", "SYS.1.1.M1 (Windows Defender)", "kesk",
                           "Windows Defender reaalajakaitse EI OLE AKTIIVNE",
                           "Luba: Set-MpPreference -DisableRealtimeMonitoring $false")
        else:
            self.log_finding("INFO", "SYS.1.1.M1 (Windows Defender)", "kesk",
                           "Windows Defender olekut ei õnnestunud kontrollida")

    def _windows_password_policy(self):
        accounts = self.run_cmd(["net", "accounts"])
        lines = accounts.splitlines()
        for line in lines:
            line_lower = line.lower()
            if "maximum password age" in line_lower:
                days = 0
                for part in line.split("|"):
                    if "maximum" in part.lower():
                        days_part = part.split(":")[-1].strip()
                        try:
                            days = int(days_part.split()[0])
                        except ValueError:
                            days = -1
                if days > 90 or days == -1:
                    self.log_finding("HIGH", "ORP.4.A1 (Parooli vanus)", "kesk",
                                   f"Parooli maksimaalne vanus: {days} päeva (soovitus: <=90)",
                                   "Muuda: net accounts /maxpwage:90")
                elif days == 0:
                    self.log_finding("HIGH", "ORP.4.A1 (Parooli vanus)", "kesk",
                                   "Paroolid EI AEGU kunagi (max age = 0)",
                                   "Muuda: net accounts /maxpwage:90")
                else:
                    self.log_finding("OK", "ORP.4.A1 (Parooli vanus)", "kesk",
                                   f"Parooli maksimaalne vanus: {days} päeva (korras)")
            elif "minimum password length" in line_lower:
                length = 0
                for part in line.split("|"):
                    if "minimum" in part.lower():
                        try:
                            length = int(part.split(":")[-1].strip())
                        except ValueError:
                            length = -1
                if length < 8:
                    self.log_finding("HIGH", "ORP.4.A1 (Parooli pikkus)", "kesk",
                                   f"Minimaalne parooli pikkus: {length} (soovitus: >=8)",
                                   "Muuda: net accounts /minpwlen:8")
                else:
                    self.log_finding("OK", "ORP.4.A1 (Parooli pikkus)", "kesk",
                                   f"Minimaalne parooli pikkus: {length} (korras)")
            elif "lockout threshold" in line_lower:
                threshold = 0
                for part in line.split("|"):
                    if "lockout" in part.lower():
                        try:
                            threshold = int(part.split(":")[-1].strip())
                        except ValueError:
                            threshold = -1
                if threshold == 0:
                    self.log_finding("HIGH", "ORP.4.A1 (Lukustumislävi)", "kesk",
                                   "Konto lukustumine EI OLE SEADISTATUD (0 ebaõnnestunud katset)",
                                   "Muuda: net accounts /lockoutthreshold:5")
                else:
                    self.log_finding("OK", "ORP.4.A1 (Lukustumislävi)", "kesk",
                                   f"Konto lukustumislävi: {threshold} (korras)")

    def _windows_audit_policy(self):
        auditpol = self.run_cmd(["auditpol", "/get", "/category:*"], timeout=15)
        if "Success" in auditpol or "Failure" in auditpol:
            success_count = auditpol.count("Success")
            failure_count = auditpol.count("Failure")
            no_audit = auditpol.count("No Auditing")
            self.log_finding("OK", "ORP.4.M22 (Auditipoliitika)", "kesk",
                           f"Auditipoliitika on konfigureeritud. Edu: {success_count}, Ebaõnnestumine: {failure_count}, Puudub: {no_audit}")
            if no_audit > 20:
                self.log_finding("INFO", "ORP.4.M22 (Auditipoliitika)", "standard",
                               f"{no_audit} auditeerimiskategoorias puudub logimine",
                               "Kaalu täielikumat auditeerimist: auditpol /set /category:*")
        else:
            self.log_finding("INFO", "ORP.4.M22 (Auditipoliitika)", "kesk",
                           "Auditipoliitika olekut ei õnnestunud hinnata")

    def _windows_smb(self):
        smb = self.run_cmd(["sc", "query", "lanmanserver"])
        if "RUNNING" in smb:
            self.log_finding("INFO", "SYS.1.1.A6 (SMB jagamised)", "standard",
                           "SMB server (lanmanserver) on töös. Kontrolli jagamisi käsitsi.")
            shares = self.run_cmd(["net", "share"])
            admin_shares = ["ADMIN$", "C$", "IPC$"]
            found_admin = [s for s in admin_shares if s in shares]
            if found_admin:
                self.log_finding("INFO", "SYS.1.1.A6 (Admin jagamised)", "standard",
                               f"Administratiivsed jagamised: {', '.join(found_admin)}")
            smb1 = self.run_cmd(["powershell", "-Command", "Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol"], timeout=15)
            if "True" in smb1:
                self.log_finding("HIGH", "CON.1.A1 (SMB1)", "standard",
                               "SMB1 protokoll on VEEL LUBATUD (väga vana ja ebaturvaline)",
                               "Keela: Set-SmbServerConfiguration -EnableSMB1Protocol $false")

    def _windows_rdp(self):
        rdp = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\System\\CurrentControlSet\\Control\\Terminal Server').fDenyTSConnections"], timeout=10)
        if "0" in rdp.strip():
            self.log_finding("INFO", "CON.1.A1 (RDP)", "standard",
                           "RDP on LUBATUD (võimalik ründepind)",
                           "Kui pole vajalik, keela RDP")
            nla = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Terminal Server\\WinStations\\RDP-Tcp').UserAuthentication"], timeout=10)
            if "1" in nla.strip():
                self.log_finding("OK", "CON.1.A1 (RDP NLA)", "standard",
                               "RDP nõuab võrgu taseme autentimist (NLA)")
            else:
                self.log_finding("HIGH", "CON.1.A1 (RDP NLA)", "standard",
                               "RDP EI nõua võrgu taseme autentimist (NLA puudub)",
                               "Luba NLA: Set-ItemProperty -Path ... -Name UserAuthentication -Value 1")
        elif "1" in rdp.strip():
            self.log_finding("OK", "CON.1.A1 (RDP)", "standard",
                           "RDP on keelatud")

    def _windows_updates(self):
        wu = self.run_cmd(["powershell", "-Command", "Get-WUApiVersion"], timeout=10)
        updates = self.run_cmd(["powershell", "-Command", "Get-WUList | Select-Object -First 5"], timeout=30)
        if wu:
            self.log_finding("OK", "SYS.1.3.M3 (Windows Update)", "kesk",
                           "Windows Update API on kättesaadav")
        hotfixes = self.run_cmd(["powershell", "-Command", "Get-HotFix | Measure-Object | Select-Object -ExpandProperty Count"], timeout=15)
        if hotfixes:
            count = hotfixes.strip()
            self.log_finding("INFO", "SYS.1.3.M3 (Paigaldatud uuendused)", "kesk",
                           f"Paigaldatud {count} turvauuendust")
        last_check = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update').LastWaitTimeout"], timeout=10)
        if not last_check.strip():
            self.log_finding("INFO", "SYS.1.3.M3 (WSUS/GPO)", "kesk",
                           "Windows Update konfiguratsiooni ei saa hinnata (GPO võib juhtida)")

    def _windows_services(self):
        services_text = self.run_cmd(["sc", "query"], timeout=30)
        running = services_text.count("STATE") - services_text.count("STATE") // 2
        self.log_finding("INFO", "SYS.1.1.A6 (Windows teenused)", "standard",
                        f"Töös olevate teenuste arv: {running}")
        dangerous_win_svc = ["TlntSvr", "RemoteRegistry"]
        for svc in dangerous_win_svc:
            status = self.run_cmd(["sc", "query", svc])
            if "RUNNING" in status:
                self.log_finding("HIGH", "SYS.1.1.A6 (Ohtlik teenus)", "standard",
                               f"Ohustatud teenus {svc} on töös",
                               "Keela: sc stop " + svc + " && sc config " + svc + " start= disabled")

    def _windows_shares(self):
        shares = self.run_cmd(["net", "share"])
        share_list = [s.split()[0] for s in shares.splitlines() if s.strip() and not s.startswith(("Share name", "---", "The command", "")) and s.strip() != ""]
        if len(share_list) > 5:
            self.log_finding("INFO", "SYS.1.1.A6 (Jagamised)", "standard",
                           f"Süsteemil on {len(share_list)} jagamist. Kontrolli vajalikkust käsitsi.")

    def _windows_uac(self):
        uac = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System').EnableLUA"], timeout=10)
        if "1" in uac.strip():
            self.log_finding("OK", "SYS.1.1.M1 (UAC)", "kesk",
                           "User Account Control (UAC) on lubatud")
        else:
            self.log_finding("HIGH", "SYS.1.1.M1 (UAC)", "kesk",
                           "User Account Control (UAC) on KEELATUD!",
                           "Luba: EnableLUA=1 registrivõtmes")

    def _windows_admin_accounts(self):
        admins = self.run_cmd(["powershell", "-Command", "Get-LocalGroupMember -Group Administrators | Select-Object Name, PrincipalSource"], timeout=15)
        if admins:
            admin_users = [l.strip() for l in admins.splitlines() if l.strip() and not l.startswith(("Name", "---", "")) and "Name" not in l]
            self.log_finding("INFO", "ORP.4.A2 (Admin kontod)", "korg",
                           f"Administraatorite rühma liikmed ({len([a for a in admin_users if a])}): kontrolli käsitsi")
            if len([a for a in admin_users if a]) > 3:
                self.log_finding("INFO", "ORP.4.A2 (Admin kontod)", "korg",
                               f"Rohkem kui 3 administraatorit - kaalu vähendamist",
                               "Eemalda mittevajalikud admin õigused")

    def _windows_winrm(self):
        winrm = self.run_cmd(["powershell", "-Command", "Test-WSMan"], timeout=10)
        if winrm and "wsmid" in winrm.lower():
            self.log_finding("INFO", "CON.1.A1 (WinRM)", "standard",
                           "WinRM on aktiivne - kaugjuhtimine WMI kaudu",
                           "Kui pole vajalik: Disable-PSRemoting")

    def audit_server(self):
        print(f"\n[*] Serveri süvaaudit (E-ITS 2024) - roll: {self.role}")
        print("-" * 79)

        if self.os_type == "Windows":
            self._server_ad_audit()
        self._server_backup_check()
        self._server_dns_check()
        self._server_tls_check()

    def _server_ad_audit(self):
        dc_check = self.run_cmd(["powershell", "-Command", "Get-ADDomainController | Select-Object Name, Site, OperatingSystem"], timeout=15)
        if dc_check:
            self.log_finding("OK", "INF.1.M1 (AD domeenikontroller)", "kesk",
                           "Active Directory domeenikontroller tuvastatud")
            forest_mode = self.run_cmd(["powershell", "-Command", "(Get-ADForest).ForestMode"], timeout=15)
            if forest_mode:
                self.log_finding("INFO", "INF.1.M1 (AD metsa tase)", "kesk",
                               f"AD metsa tase: {forest_mode.strip()}")
            anon_enum = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Lsa').RestrictAnonymous"], timeout=10)
            if "1" in anon_enum.strip():
                self.log_finding("OK", "INF.1.M1 (Anonüümne loetlemine)", "kesk",
                               "Anonüümne AD loetlemine on piiratud")
            else:
                self.log_finding("HIGH", "INF.1.M1 (Anonüümne loetlemine)", "kesk",
                               "Anonüümne AD loetlemine on VÕIMALIK",
                               "Sea RestrictAnonymous=1 ja RestrictAnonymousSAM=1")
        else:
            self.log_finding("INFO", "INF.1.M1 (AD kontroll)", "kesk",
                           "Active Directory pole tuvastatud või PowerShell pole saadaval")

    def _server_backup_check(self):
        if self.os_type == "Windows":
            wbadmin = self.run_cmd(["wbadmin", "get", "versions"], timeout=15)
            if wbadmin and "version" in wbadmin.lower():
                self.log_finding("OK", "INF.1.A1 (Varundamine)", "kesk",
                               "Windows Backup on konfigureeritud")
            else:
                self.log_finding("INFO", "INF.1.A1 (Varundamine)", "kesk",
                               "Windows Backup pole konfigureeritud või pole saadaval",
                               "Kaalu varunduse seadistamist")
        else:
            rsync = self.run_cmd(["which", "rsync"])
            duplicity = self.run_cmd(["which", "duplicity"])
            borg = self.run_cmd(["which", "borg"])
            if rsync or duplicity or borg:
                tools = [t for t in ["rsync", "duplicity", "borg"] if self.run_cmd(["which", t])]
                self.log_finding("OK", "INF.1.A1 (Varundamine)", "kesk",
                               f"Varundustööriistad tuvastatud: {', '.join(tools)}")
            else:
                self.log_finding("INFO", "INF.1.A1 (Varundamine)", "kesk",
                               "Varundustööriistu pole tuvastatud",
                               "Kaalu rsync/duplicity/borg paigaldamist")

    def _server_dns_check(self):
        if self.os_type != "Windows":
            return
        dns = self.run_cmd(["powershell", "-Command", "Get-DnsServerZone | Select-Object ZoneName, ZoneType"], timeout=15)
        if dns:
            self.log_finding("OK", "INF.1.M1 (DNS server)", "kesk",
                           "DNS server on tuvastatud")
            if "Secondary" in dns:
                self.log_finding("INFO", "INF.1.M1 (DNS tsoonid)", "standard",
                               "DNS sekundaartsoonid tuvastatud - kontrolli ülekandeid")

    def _server_tls_check(self):
        if self.os_type == "Windows":
            schannel = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.2\\Client').Enabled"], timeout=10)
            if "1" in schannel.strip():
                self.log_finding("OK", "APP.1.M1 (TLS 1.2)", "kesk",
                               "TLS 1.2 on lubatud (SCHANNEL)")
            tls13 = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\TLS 1.3\\Client').Enabled"], timeout=10)
            if "1" in tls13.strip():
                self.log_finding("OK", "APP.1.M1 (TLS 1.3)", "standard",
                               "TLS 1.3 on lubatud")
            ssl30 = self.run_cmd(["powershell", "-Command", "(Get-ItemProperty 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\SecurityProviders\\SCHANNEL\\Protocols\\SSL 3.0\\Client').Disabled"], timeout=10)
            if "1" in ssl30.strip():
                self.log_finding("OK", "APP.1.M1 (SSL 3.0)", "kesk",
                               "SSL 3.0 on keelatud (POODLE ründe kaitse)")

    def audit_firewall(self):
        print(f"\n[*] Tulemüüri süvaaudit (E-ITS 2024) - roll: {self.role}")
        print("-" * 79)

        if self.os_type == "Linux":
            self._fw_iptables_rules()
            self._fw_default_policies()
            self._fw_nat_rules()
        elif self.os_type == "Windows":
            self._fw_windows_rules()

    def _fw_iptables_rules(self):
        iptables = self.run_cmd(["sudo", "iptables", "-L", "-n", "-v"], timeout=15)
        if "Chain" in iptables:
            chains = iptables.split("Chain ")
            for chain_block in chains[1:]:
                chain_name = chain_block.split(" ")[0]
                policy = "ACC" if "ACCEPT" in chain_block.split("\n")[0] else "DROP" if "DROP" in chain_block else "N/A"
                rules = len([l for l in chain_block.splitlines() if l.strip() and not l.startswith("Chain") and "target" not in l.lower() and "pkts" not in l.lower()])
                self.log_finding("INFO", "NET.1.M1 (Tulemüür)", "kesk",
                               f"Ahel {chain_name}: poliitika={policy}, reegleid={rules}")
        if iptables.count("DROP") > 0:
            self.log_finding("OK", "NET.1.M1 (Tulemüüri DROP)", "kesk",
                           "Tulemüür kasutab DROP reegleid (vaikimisi keelduv)")
        if iptables.count("REJECT") > 0:
            self.log_finding("OK", "NET.1.M1 (Tulemüüri REJECT)", "kesk",
                           "Tulemüür kasutab REJECT reegleid")

    def _fw_default_policies(self):
        iptables_pol = self.run_cmd(["sudo", "iptables", "-L"], timeout=10)
        for chain in ["INPUT", "FORWARD", "OUTPUT"]:
            for line in iptables_pol.splitlines():
                if line.strip().startswith("Chain " + chain):
                    if "DROP" in line or "REJECT" in line:
                        self.log_finding("OK", "NET.1.M1 (Vaikepoliitika)", "kesk",
                                       f"Ahel {chain} vaikepoliitika on DROP/REJECT - turvaline")
                    elif "ACCEPT" in line:
                        self.log_finding("INFO", "NET.1.M1 (Vaikepoliitika)", "standard",
                                       f"Ahel {chain} vaikepoliitika on ACCEPT (kõik lubatud)",
                                       "Kaalu vaikepoliitika muutmist DROP-ks")

    def _fw_nat_rules(self):
        nat = self.run_cmd(["sudo", "iptables", "-t", "nat", "-L", "-n"], timeout=10)
        if "MASQUERADE" in nat:
            self.log_finding("INFO", "NET.1.A1 (NAT/MASQUERADE)", "standard",
                           "NAT MASQUERADE on aktiivne - süsteem toimib ruuterina/gatewayna")
            self.role = "RUUTER/TULEMÜÜR (NAT)"
        if "DNAT" in nat or "REDIRECT" in nat:
            self.log_finding("INFO", "NET.1.A1 (NAT port forwarding)", "standard",
                           "NAT port forwardimine on aktiivne - pordid suunatakse sisevõrku",
                           "Kontrolli, et avatud on ainult vajalikud pordid")
        if "SNAT" in nat:
            self.log_finding("INFO", "NET.1.A1 (NAT SNAT)", "standard",
                           "NAT SNAT on aktiivne")

    def _fw_windows_rules(self):
        rules_in = self.run_cmd(["netsh", "advfirewall", "firewall", "show", "rule", "name=all", "dir=in"], timeout=30)
        rules_out = self.run_cmd(["netsh", "advfirewall", "firewall", "show", "rule", "name=all", "dir=out"], timeout=30)
        in_rules = len([l for l in rules_in.splitlines() if "Rule Name:" in l])
        out_rules = len([l for l in rules_out.splitlines() if "Rule Name:" in l])
        self.log_finding("INFO", "NET.1.M1 (Tulemüüri reeglid)", "kesk",
                       f"Sisse: {in_rules} reeglit, Välja: {out_rules} reeglit")
        if in_rules > 50:
            self.log_finding("INFO", "NET.1.M1 (Tulemüüri reeglid)", "standard",
                           f"Sissepoole reegleid on palju ({in_rules}) - võimalik liigne keerukus",
                           "Kaalu reeglite auditeerimist ja puhastamist")

    def audit_router(self):
        print(f"\n[*] Ruuteri süvaaudit (E-ITS 2024) - roll: {self.role}")
        print("-" * 79)

        if self.os_type == "Linux":
            self._router_ip_forward()
            self._router_arp()
            self._router_dhcp()
            self._router_dns_resolver()
            self._router_interfaces()

    def _router_ip_forward(self):
        ip_forward = self.run_cmd(["sysctl", "-n", "net.ipv4.ip_forward"]).strip()
        if ip_forward == "1":
            self.log_finding("OK", "NET.1.M1 (IP edastamine)", "kesk",
                           "IP edastamine on lubatud - süsteem toimib ruuterina (normaalne)")
            if os.path.exists("/proc/sys/net/ipv6/conf/all/forwarding"):
                ip6_forward = self.run_cmd(["sysctl", "-n", "net.ipv6.conf.all.forwarding"]).strip()
                if ip6_forward == "1":
                    self.log_finding("INFO", "NET.1.M1 (IPv6 edastamine)", "standard",
                                   "IPv6 edastamine on samuti lubatud")

    def _router_arp(self):
        arp = self.run_cmd(["arp", "-n"])
        if arp:
            arp_entries = [l for l in arp.splitlines() if l.strip() and not l.startswith("Address")]
            self.log_finding("INFO", "NET.1.M1 (ARP tabel)", "kesk",
                           f"ARP tabelis {len(arp_entries)} kirjet")
        arp_filter = self.run_cmd(["sysctl", "-n", "net.ipv4.conf.all.arp_filter"]).strip()
        if arp_filter == "1":
            self.log_finding("OK", "NET.1.A1 (ARP filter)", "standard",
                           "ARP filter on aktiivne (kaitse ARP spoofingu vastu)")

    def _router_dhcp(self):
        if self.run_cmd(["which", "dhcpd"]) or self.run_cmd(["which", "dnsmasq"]):
            dhcp = self.run_cmd(["systemctl", "is-active", "isc-dhcp-server"])
            if "active" in dhcp:
                self.log_finding("OK", "NET.1.M1 (DHCP server)", "kesk",
                               "DHCP server on aktiivne")
            dnsmasq = self.run_cmd(["systemctl", "is-active", "dnsmasq"])
            if "active" in dnsmasq:
                self.log_finding("OK", "NET.1.M1 (DHCP/DNS)", "kesk",
                               "dnsmasq (DHCP+DNS) on aktiivne")
        else:
            self.log_finding("INFO", "NET.1.M1 (DHCP)", "kesk",
                           "DHCP serverit pole tuvastatud (võib olla teises seadmes)")

    def _router_dns_resolver(self):
        resolve = self.run_cmd(["systemctl", "is-active", "systemd-resolved"])
        if "active" in resolve:
            self.log_finding("OK", "NET.1.M1 (DNS resolver)", "kesk",
                           "systemd-resolved on aktiivne")
        if os.path.exists("/etc/resolv.conf"):
            try:
                with open("/etc/resolv.conf") as f:
                    resolv = f.read()
                    nameservers = re.findall(r"nameserver\s+(\S+)", resolv)
                    if nameservers:
                        for ns in nameservers:
                            if ns.startswith("8.8.") or ns.startswith("1.1.") or ns.startswith("9.9."):
                                self.log_finding("OK", "NET.1.M1 (DNS)", "kesk",
                                               f"DNS: {ns} (avalik DNS server)")
                            else:
                                self.log_finding("OK", "NET.1.M1 (DNS)", "kesk",
                                               f"DNS: {ns} (kohalik DNS server)")
            except Exception as e:
                pass

    def _router_interfaces(self):
        interfaces = self.run_cmd(["ip", "addr"])
        if interfaces:
            ifaces = re.findall(r"\d+:\s+(\w+)", interfaces)
            up_interfaces = []
            blocks = interfaces.split("\n")
            for line in blocks:
                if "state UP" in line:
                    m = re.match(r"\d+:\s+(\w+)", line)
                    if m:
                        up_interfaces.append(m.group(1))
            self.log_finding("INFO", "NET.1.M1 (Võrguliidesed)", "kesk",
                           f"Aktiivsed liidesed: {', '.join(up_interfaces)}")
        routes = self.run_cmd(["ip", "route"])
        if routes:
            default_gw = [l for l in routes.splitlines() if l.startswith("default")]
            if default_gw:
                self.log_finding("OK", "NET.1.M1 (Marsruutimine)", "kesk",
                               f"Vaikimisi marsruut: {default_gw[0]}")

    def kokkuvotte_analyys(self):
        print("\n" + "=" * 79)
        print("  E-ITS 2024 VASTAVUSE KOKKUVÕTE")
        print("=" * 79)

        tase_names = {"kesk": "KESK (M) - Baastase",
                      "standard": "STANDARD (A) - Täiendav tase",
                      "korg": "KÕRG (S) - Kõrge tase"}

        overall_status = {"kesk": True, "standard": True, "korg": True}
        for tase, stats in self.summary.items():
            print(f"\n  [{tase_names[tase]}]")
            print(f"    OK: {stats['OK']}  |  INFO: {stats['INFO']}  |  "
                  f"HIGH: {stats['HIGH']}  |  CRITICAL: {stats['CRITICAL']}  |  "
                  f"POLE KONTROLLITUD: {stats['POLE KONTROLLITUD']}")
            if stats.get("CRITICAL", 0) > 0:
                print(f"    HINNANG: ✔ Keskmeetme nõuded osaliselt TÄITMATA (kriitilisi leide)")
                overall_status[tase] = False
            elif stats.get("HIGH", 0) > 0:
                print(f"    HINNANG: ⚠ Keskmeetme nõuded täidetud, kuid on kõrge riskiga leide")
            else:
                print(f"    HINNANG: ✓ Keskmeetme nõuded täidetud")

        print(f"\n  SÜSTEEMI ROLL: {self.role}")
        print(f"  HOSTNAME: {self.hostname}")
        print(f"  OS: {self.os_type} ({platform.version() if self.os_type == 'Windows' else platform.release()})")
        print(f"  AUDITI AEG: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        total_findings = sum(sum(v.values()) for v in self.summary.values())
        print(f"\n  KOKKU: {total_findings} kontrolli teostatud")
        print("=" * 79)

    def kirjuta_raport(self):
        out_dir = utils.get_output_dir()
        out_file = os.path.join(out_dir, "34_tulemus_eits_vastavus.txt")

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(LOGO + "\n")
            f.write("=" * 79 + "\n")
            f.write(f"|  PROJEKT:     VALVUR - Intsidendi süvaanalüüs" + " " * 28 + "|\n")
            f.write(f"|  RAPORT:      E-ITS 2024 VASTAVUSRAPORT" + " " * 38 + "|\n")
            f.write(f"|  SÜSTEEM:     {self.hostname:<53} |\n")
            f.write(f"|  ROLL:        {self.role:<53} |\n")
            f.write(f"|  OS:          {self.os_type:<53} |\n")
            f.write(f"|  GENEREERITUD: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):<56} |\n")
            f.write("=" * 79 + "\n\n")

            tase_levels = [
                ("kesk", "KESK (M) - Baastase - kohustuslikud põhimeetmed"),
                ("standard", "STANDARD (A) - Täiendav tase - soovituslikud meetmed"),
                ("korg", "KÕRG (S) - Kõrge tase - erinõuded")
            ]

            for tase_key, tase_name in tase_levels:
                f.write(f"\n--- {tase_name} ---\n")
                f.write("-" * 79 + "\n")
                tase_findings = [x for x in self.findings if x["eits_tase"] == tase_key]
                if tase_findings:
                    for finding in tase_findings:
                        f.write(f"[{finding['staatus']:<8}] [{finding['meede']:<30}] {finding['kirjeldus']}\n")
                        if finding['soovitus']:
                            f.write(f"          SOOVITUS: {finding['soovitus']}\n")
                else:
                    f.write("  (Kontrollimata - pole antud süsteemil kohaldatav)\n")

            f.write("\n" + "=" * 79 + "\n")
            f.write("  E-ITS 2024 VASTAVUSE KOKKUVÕTE\n")
            f.write("=" * 79 + "\n")
            for tase_key, tase_name in tase_levels:
                stats = self.summary[tase_key]
                f.write(f"\n  [{tase_name}]\n")
                f.write(f"    OK: {stats['OK']}  |  INFO: {stats['INFO']}  |  "
                       f"HIGH: {stats['HIGH']}  |  CRITICAL: {stats['CRITICAL']}\n")
                if stats.get("CRITICAL", 0) > 0:
                    f.write(f"    HINNANG: EBAKÕLAKOHANE - kriitilisi turvaprobleeme\n")
                elif stats.get("HIGH", 0) > 0:
                    f.write(f"    HINNANG: OSALISELT VASTAV - kõrge riskiga leidudega\n")
                else:
                    f.write(f"    HINNANG: VASTAB NÕUETELE\n")

            f.write(f"\n  SÜSTEEM: {self.hostname} ({self.role})\n")
            f.write(f"  OS: {self.os_type}\n")
            f.write(f"  AUDITI AEG: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"  KONTROLLE KOKKU: {len(self.findings)}\n")
            f.write("\n" + "=" * 79 + "\n")
            f.write("  NIST CSF 2.0 VASTAVUS\n")
            f.write("=" * 79 + "\n")
            f.write("  IDENTIFY: Varade kaardistus ja riskihinnang (E-ITS CON/NET/SYS)\n")
            f.write("  PROTECT: Turvakontrollid - tulemüür, autentimine, uuendused\n")
            f.write("  DETECT: Logimine ja monitooring (ORP.4.M22 - auditd/auditpol)\n")
            f.write("  RESPOND: Puuduste tuvastamine ja soovitused\n")
            f.write("  RECOVER: Varunduse staatus (INF.1.A1)\n")
            f.write("=" * 79 + "\n")
            f.write("  E-ITS 2024 - Eesti Infoturbestandard\n")
            f.write("  Vastavushinnang põhineb automaatsel skaneerimisel.\n")
            f.write("  Täpseks hindamiseks vajalik käsitsi ülevaatus.\n")
            f.write("=" * 79 + "\n")

        print(f"\n[+] Audit lõpetatud! Raport: {out_file}")
        logger.info(f"E-ITS vastavusraport salvestatud: {out_file}")

    def run_all(self):
        print(LOGO)
        print(f"[*] VALVUR E-ITS 2024 Baasturvalisuse Kontroll")
        print(f"[*] Süsteem: {self.hostname} | OS: {self.os_type} | Roll: {self.role}")
        print(f"[*] Aeg: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 79)

        if self.os_type == "Linux":
            self.audit_linux()
            ip_forward = self.run_cmd(["sysctl", "-n", "net.ipv4.ip_forward"]).strip()
            if ip_forward == "1":
                self.audit_router()
            if self.role in ("RUUTER", "RUUTER/TULEMÜÜR (NAT)"):
                self.audit_firewall()
                self.audit_router()
            elif any(x in self.role for x in ["SERVER", "DC"]):
                self.audit_server()
            else:
                self.audit_firewall()

        elif self.os_type == "Windows":
            self.audit_windows()
            if any(x in self.role for x in ["SERVER", "DC"]):
                self.audit_server()
                self.audit_firewall()
            else:
                self.audit_firewall()

        self.kokkuvotte_analyys()
        self.kirjuta_raport()


if __name__ == "__main__":
    auditor = EITSAuditor()
    auditor.run_all()
