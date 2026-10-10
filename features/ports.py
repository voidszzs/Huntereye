import shutil
import socket
import subprocess
from _lib import ui
from _lib.status import current_target, set_open_ports


def _host(target):
    from _lib.config import resolve_target
    t = resolve_target(target)
    h = t.get("host") or t.get("url")
    if h and (h.startswith("http://") or h.startswith("https://")):
        h = h.split("//", 1)[1].split("/", 1)[0]
    if h and h.count(":") == 1:
        h = h.split(":", 1)[0]
    return h


def _nmap(host, full):
    ports = "-p-" if full else "-p1-1024"
    cmd = ["nmap", "-sS", "-Pn", "-T4", ports, host]
    ui.plain(f"  running: {' '.join(cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=1800, shell=False)
        found = []
        for line in r.stdout.splitlines():
            if "/tcp" in line and "open" in line:
                p = int(line.split("/")[0].strip())
                found.append(("tcp", p))
                ui.plain(f"  {ui.sym_ok()} open tcp/{p}")
        return found
    except Exception as e:
        ui.plain(f"  nmap error: {e}")
        return []


def _py(host, ports):
    found = []
    for i, p in enumerate(ports, 1):
        if i % 200 == 0:
            ui.plain(ui.dim(f"  progress {int(100*i/len(ports))}%"))
        try:
            with socket.create_connection((host, p), timeout=0.3):
                found.append(("tcp", p))
                ui.plain(f"  {ui.sym_ok()} open tcp/{p}")
        except Exception:
            pass
    return found


def run():
    target = current_target()
    if not target:
        ui.plain("  no target set. use [01] first.")
        return
    host = _host(target)
    if not host:
        ui.plain("  could not resolve host.")
        return
    ui.plain(f"  host: {host}")
    full = ui.ask("full scan 1-65535? [y/N]").lower() == "y"
    if shutil.which("nmap"):
        found = _nmap(host, full)
    else:
        ui.plain("  nmap not found — python fallback (slow).")
        common = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
                  587, 993, 995, 1433, 3306, 3389, 5432, 5900, 6379,
                  8080, 8443, 25565, 27015, 30120, 19132]
        if full:
            common = list(range(1, 1025)) + common
        found = _py(host, sorted(set(common)))
    set_open_ports([p for _, p in found])
    ui.plain("")
    ui.plain(f"  {ui.sym_ok()} done. {len(found)} open ports.")
    for proto, port in found:
        ui.plain(f"    {proto}/{port}")
