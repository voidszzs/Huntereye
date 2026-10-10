# ring 0.1 — host recon.
import ipaddress
import shutil
import socket
import subprocess
from _lib.debug import dbg
from _lib.status import set_open_ports

COMMON = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 587,
          993, 995, 1433, 3306, 3389, 5432, 5900, 6379, 8080, 8443,
          25565, 27015, 30120, 19132]


def _ip(s):
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def resolve(name):
    out = {"ipv4": None, "ipv6": None}
    try:
        for fam, _, _, _, sa in socket.getaddrinfo(name, None):
            if fam == socket.AF_INET and not out["ipv4"]:
                out["ipv4"] = sa[0]
            elif fam == socket.AF_INET6 and not out["ipv6"]:
                out["ipv6"] = sa[0]
    except socket.gaierror:
        pass
    return out


def _py_scan(host, ports):
    found = []
    for p in ports:
        try:
            with socket.create_connection((host, p), timeout=0.4):
                found.append(("tcp", p))
        except Exception:
            pass
    return found


def port_sweep(host, quick=True):
    if shutil.which("nmap"):
        flags = ["-sS", "-Pn", "-T4", "-p", "1-1024" if quick else "1-65535"]
        cmd = ["nmap"] + flags + [host]
        dbg("recon_host", "nmap: " + " ".join(cmd))
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=600, shell=False).stdout
        except subprocess.TimeoutExpired:
            return []
        ports = []
        for line in out.splitlines():
            if "/tcp" in line and "open" in line:
                ports.append(("tcp", int(line.split("/")[0].strip())))
            elif "/udp" in line and "open" in line:
                ports.append(("udp", int(line.split("/")[0].strip())))
        return ports
    dbg("recon_host", "nmap missing — python fallback")
    return _py_scan(host, COMMON)


def recon_target(target, args):
    d = {"target": target, "ipv4": None, "ipv6": None, "ports": [],
         "class": "unknown", "notes": []}
    host = target.get("host") or target.get("url")
    if not host:
        return d
    if _ip(host):
        if ":" in host:
            d["ipv6"] = host
        else:
            d["ipv4"] = host
    else:
        a = resolve(host)
        d["ipv4"] = a["ipv4"]
        d["ipv6"] = a["ipv6"]
    probe = d["ipv4"] or d["ipv6"] or host
    d["ports"] = port_sweep(probe, quick=(getattr(args, "mode", "recon") == "recon"))
    declared = target.get("port")
    if declared and ("tcp", declared) not in d["ports"]:
        d["ports"].append(("tcp", declared))
    try:
        set_open_ports([p for _, p in d["ports"]])
    except Exception:
        pass
    t = target.get("type", "unknown")
    if t == "minecraft" or any(p == 25565 for _, p in d["ports"]):
        d["class"] = "game-server"
    elif t == "http" or any(p in (80, 443, 8080) for _, p in d["ports"]):
        d["class"] = "website"
    elif t == "router" or (any(p in (80, 443) for _, p in d["ports"]) and d["ipv4"]):
        d["class"] = "router-or-web"
    return d


def full_recon(target, args):
    from _lib.ring0.services import detect_services
    from _lib.ring0.deps import map_deps
    from _lib.ring0.costmap import build_costmap
    d = recon_target(target, args)
    host = d.get("ipv4") or d.get("ipv6") or target.get("host")
    if not host:
        return d
    d["services"] = detect_services(host, d.get("ports", []))
    d["deps"] = map_deps(d)
    if target.get("type") == "http" or d.get("class") == "website":
        base = target.get("url") or f"http://{host}"
        d["costmap"] = build_costmap(base)
    return d
