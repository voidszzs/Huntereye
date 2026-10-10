# ring 0.2 — services.
import shutil
import socket
import ssl
import subprocess
from _lib.debug import dbg

COMMON = {21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp", 53: "dns",
          80: "http", 110: "pop3", 143: "imap", 443: "https", 465: "smtps",
          587: "smtp-sub", 993: "imaps", 995: "pop3s", 1433: "mssql",
          3306: "mysql", 5432: "postgres", 6379: "redis", 8080: "http-alt",
          8443: "https-alt", 25565: "minecraft", 27015: "source",
          30120: "fivem", 19132: "mc-bedrock"}


def banner_grab(host, port, timeout=3):
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            if port in (80, 8080, 8000):
                s.sendall(b"HEAD / HTTP/1.0\r\nHost: %b\r\n\r\n" % host.encode())
            data = s.recv(1024)
            return data.decode("utf-8", "replace").strip()
    except Exception:
        return ""


def tls_info(host, port=443, timeout=5):
    out = {"cn": None, "san": [], "issuer": None, "version": None}
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=timeout) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                cert = ss.getpeercert()
                out["version"] = ss.version()
                if cert:
                    for tup in cert.get("subject", ()):
                        for k, v in tup:
                            if k == "commonName":
                                out["cn"] = v
                    out["san"] = [v for k, v in cert.get("subjectAltName", ()) if k == "DNS"]
    except Exception as e:
        dbg("recon_services", f"tls {host}:{port} {e!r}")
    return out


def http_probe(host, port=80, tls=False, timeout=5):
    out = {"status": None, "server": None, "headers": {}}
    if not shutil.which("curl"):
        return out
    scheme = "https" if tls else "http"
    url = f"{scheme}://{host}:{port}/"
    try:
        r = subprocess.run(
            ["curl", "-sSI", "-k", "--max-time", str(timeout), url],
            capture_output=True, text=True, timeout=timeout + 2, shell=False)
        for line in r.stdout.splitlines():
            if line.startswith("HTTP/"):
                out["status"] = line.split()[1]
            elif ":" in line:
                k, v = line.split(":", 1)
                k, v = k.strip().lower(), v.strip()
                out["headers"][k] = v
                if k == "server":
                    out["server"] = v
    except Exception as e:
        dbg("recon_services", f"http {host}:{port} {e!r}")
    return out


def detect_services(host, ports):
    out = []
    for proto, port in ports:
        if proto != "tcp":
            out.append({"proto": proto, "port": port,
                        "service": COMMON.get(port, "?")})
            continue
        banner = banner_grab(host, port)
        entry = {"proto": "tcp", "port": port,
                 "service": COMMON.get(port, "?"),
                 "banner": banner[:200]}
        if port in (443, 8443):
            entry["tls"] = tls_info(host, port)
        if port in (80, 8080, 443, 8443):
            entry["http"] = http_probe(host, port, tls=port in (443, 8443))
        out.append(entry)
    return out
