# ring 0.3 — deps.
import shutil
import subprocess

SIGS = {"cf-ray": "cloudflare", "x-cache": "generic-cache",
        "x-amz-cf-id": "cloudfront", "x-akamai-": "akamai",
        "x-fastly-": "fastly", "x-served-by": "fastly",
        "x-azure-ref": "azure-frontdoor", "x-imperva-": "imperva"}


def detect_cdn(headers):
    found = []
    for k, v in headers.items():
        kl = k.lower()
        for sig, name in SIGS.items():
            if sig in kl or sig in (v or "").lower():
                if name not in found:
                    found.append(name)
    return found


def whois_asn(host):
    if not shutil.which("whois"):
        return None
    try:
        r = subprocess.run(["whois", host], capture_output=True,
                           text=True, timeout=15, shell=False)
        for line in r.stdout.splitlines():
            ll = line.lower()
            if "origin:" in ll or "originas:" in ll:
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return None


def map_deps(d):
    out = {"cdn": [], "asn": None}
    for svc in d.get("services", []):
        h = svc.get("http", {}).get("headers") if isinstance(svc.get("http"), dict) else None
        if h:
            for n in detect_cdn(h):
                if n not in out["cdn"]:
                    out["cdn"].append(n)
    host = d.get("ipv4") or d.get("ipv6")
    if host:
        out["asn"] = whois_asn(host)
    return out
