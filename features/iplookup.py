# [11] iplookup — geolocation, isp, asn, reverse dns. read-only.

import ipaddress
import json
import socket
import subprocess
import shutil
import traceback
import urllib.request

from _lib import ui
from _lib.status import current_target
from _lib.config import resolve_target


# ── safe wrappers around ui functions ─────────────────────────────────────
def _p(t=""):
    ui.plain(t)


def _red(t):
    try:
        return ui.red(t)
    except Exception:
        return t


def _gold(t):
    try:
        return ui.gold(t)
    except Exception:
        return t


def _dim(t):
    try:
        return ui.dim(t)
    except Exception:
        return t


def _ok():
    try:
        return ui.sym_ok()
    except Exception:
        return "ok"


def _err():
    try:
        return ui.sym_err()
    except Exception:
        return "x"


def _box(title, lines):
    try:
        ui.box(title, lines)
    except Exception:
        _p("")
        _p("  " + title)
        for l in lines:
            _p(l)


# ── network lookups ────────────────────────────────────────────────────────
def _is_ip(s):
    try:
        ipaddress.ip_address(s)
        return True
    except ValueError:
        return False


def _resolve_host(target):
    t = resolve_target(target)
    h = t.get("host") or t.get("url")
    if not h:
        return None
    if h.startswith(("http://", "https://")):
        h = h.split("//", 1)[1]
    h = h.split("/", 1)[0]
    if h.count(":") == 1:
        h = h.split(":", 1)[0]
    if _is_ip(h):
        return h
    try:
        return socket.gethostbyname(h)
    except Exception:
        return None


def _reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None


def _whois(ip):
    if not shutil.which("whois"):
        return None
    try:
        r = subprocess.run(["whois", ip], capture_output=True, text=True,
                           timeout=15, shell=False,
                           encoding="utf-8", errors="replace")
        info = {}
        for line in (r.stdout or "").splitlines():
            ll = line.lower().strip()
            if not ll or ":" not in line:
                continue
            k, v = line.split(":", 1)
            k = k.strip().lower()
            v = v.strip()
            if not v:
                continue
            if k in ("orgname", "org-name", "organisation", "organization"):
                info.setdefault("org", v)
            elif k in ("origin", "originas"):
                info["asn"] = v
            elif k == "country":
                info.setdefault("country", v)
            elif k == "netname":
                info.setdefault("netname", v)
            elif k == "descr":
                info.setdefault("descr", v)
            elif "abuse" in k and "mail" in k:
                info.setdefault("abuse", v)
        return info or None
    except Exception:
        return None


def _ip_api(ip):
    url = ("http://ip-api.com/json/" + ip +
           "?fields=status,country,countryCode,regionName,city,zip,"
           "lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "hunter3eye/8.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
        if data.get("status") != "success":
            return None
        return data
    except Exception:
        return None


def _classify(ip):
    try:
        a = ipaddress.ip_address(ip)
    except ValueError:
        return "unknown"
    if a.is_private:
        return "private (rfc1918)"
    if a.is_loopback:
        return "loopback"
    if a.is_link_local:
        return "link-local"
    if a.is_multicast:
        return "multicast"
    if a.is_reserved:
        return "reserved"
    if a.is_global:
        return "public"
    return "other"


def _flag(val):
    if val is True:
        return _red("yes")
    if val is False:
        return _gold("no")
    return _dim("-")


# ── main ───────────────────────────────────────────────────────────────────
def run():
    try:
        _run_inner()
    except Exception:
        # NEVER silently return. print the traceback on screen.
        _p("")
        _p("  " + _err() + " iplookup crashed:")
        for line in traceback.format_exc().splitlines():
            _p("    " + line)
        _p("")
        try:
            ui.pause("enter to return")
        except Exception:
            pass


def _run_inner():
    target = current_target()
    if not target:
        _p("  no target set. use [01] first.")
        ui.pause("enter")
        return

    ip = _resolve_host(target)
    if not ip:
        _p("  could not resolve target to an ip.")
        ui.pause("enter")
        return

    _p("")
    _p("  " + _red("IP LOOKUP") + "  " + _gold(target) + "  ->  " + _gold(ip))
    _p("")

    # 1. local
    cls = _classify(ip)
    rdns = _reverse_dns(ip) or "(no reverse dns)"
    _p("  local")
    _p("    classification   " + str(cls))
    _p("    reverse dns      " + str(rdns))

    # 2. whois
    _p("")
    _p("  whois")
    w = _whois(ip)
    if not w:
        _p(_dim("    whois not available or empty (install whois for full info)."))
    else:
        for k in ("asn", "org", "netname", "descr", "country", "abuse"):
            if k in w:
                _p("    " + k.ljust(8) + "  " + str(w[k]))

    # 3. geo
    _p("")
    _p("  geo / isp")
    api = _ip_api(ip)
    if not api:
        _p(_dim("    geo lookup failed (offline, blocked, or api limit)."))
    else:
        cc = api.get("countryCode") or ""
        country = api.get("country") or ""
        _p("    country     " + str(country) + "  " + str(cc))
        _p("    region      " + str(api.get("regionName") or "-"))
        _p("    city        " + str(api.get("city") or "-"))
        _p("    zip         " + str(api.get("zip") or "-"))
        _p("    timezone    " + str(api.get("timezone") or "-"))
        lat = api.get("lat")
        lon = api.get("lon")
        if lat is not None and lon is not None:
            _p("    coords      %.4f, %.4f" % (lat, lon))
        _p("")
        _p("    isp         " + str(api.get("isp") or "-"))
        _p("    org         " + str(api.get("org") or "-"))
        _p("    as          " + str(api.get("as") or "-"))
        _p("    as name     " + str(api.get("asname") or "-"))
        _p("")
        _p("    hosting     " + _flag(api.get("hosting")) +
           _dim("   (datacenter / vps / cloud)"))
        _p("    proxy / vpn " + _flag(api.get("proxy")) +
           _dim("   (known proxy or vpn exit)"))
        _p("    mobile      " + _flag(api.get("mobile")) +
           _dim("   (mobile carrier)"))

    _p("")
    _p("  " + _ok() + " lookup done.")
    _p("")
    ui.pause("enter to return to menu")