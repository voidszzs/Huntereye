import re
import shutil
import socket
import subprocess


def crtsh(domain):
    if not shutil.which("curl"):
        return []
    try:
        r = subprocess.run(
            ["curl", "-sS", "--max-time", "20",
             f"https://crt.sh/?q=%25.{domain}&output=json"],
            capture_output=True, text=True, timeout=25, shell=False)
        subs = set()
        for m in re.findall(r'"name_value":"([^"]+)"', r.stdout):
            for line in m.split("\\n"):
                line = line.strip()
                if line and "*" not in line:
                    subs.add(line)
        return sorted(subs)
    except Exception:
        return []


def resolve_subs(subs):
    out = []
    for s in subs:
        try:
            out.append({"sub": s, "ip": socket.gethostbyname(s)})
        except Exception:
            continue
    return out


def hunt(d, args):
    domain = d["target"].get("host") or d["target"].get("name", "")
    if not domain:
        return None
    return resolve_subs(crtsh(domain))
