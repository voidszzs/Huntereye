# _lib/ring2/distribute.py
# ring 2.4 — multi-exit distribution for mullvad (and other vpn clis).
#
# hunter3eye's vectors run from whatever machine you launch them on.
# this module lets you spread the load across several mullvad exits
# (or any other vpn cli that supports `switch` or `set location`).
#
# no spoofing. no fake source. this only rotates the OUTBOUND identity
# between requests, using the vpn provider's own cli, which is legal
# and supported by mullvad.

import os
import random
import shutil
import subprocess
import time

from _lib.debug import dbg


# ═══════════════════════════════════════════════════════════════════════════
# detect available vpn clis
# ═══════════════════════════════════════════════════════════════════════════
def have_mullvad():
    return shutil.which("mullvad") is not None


def have_wg():
    return shutil.which("wg") is not None


def have_openvpn():
    return shutil.which("openvpn") is not None


def have_nmcli():
    return shutil.which("nmcli") is not None


# ═══════════════════════════════════════════════════════════════════════════
# mullvad — list exits
# ═══════════════════════════════════════════════════════════════════════════
def _run(args, timeout=10):
    try:
        r = subprocess.run(
            args,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout, shell=False,
        )
        return r.stdout, r.returncode
    except Exception as e:
        dbg("multipliers_distribute", f"{args[0]} failed: {e!r}")
        return "", 1


def mullvad_relays():
    if not have_mullvad():
        return []
    out, rc = _run(["mullvad", "relay", "list"], timeout=15)
    if rc != 0:
        return []
    relays = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # mullvad relay list output: "<country> <city> <hostname> (<ip>)"
        # we want the hostname (third token)
        parts = line.split()
        if len(parts) >= 3:
            relays.append(parts[2])
    return relays


def mullvad_locations():
    if not have_mullvad():
        return []
    out, rc = _run(["mullvad", "relay", "list"], timeout=15)
    if rc != 0:
        return []
    locs = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2:
            # country + city
            locs.add((parts[0], parts[1]))
    return sorted(locs)


def mullvad_status():
    if not have_mullvad():
        return {"connected": False, "raw": ""}
    out, rc = _run(["mullvad", "status"], timeout=5)
    if rc != 0:
        return {"connected": False, "raw": out}
    return {"connected": "Connected" in out, "raw": out}


def mullvad_set_location(country, city):
    if not have_mullvad():
        return False
    _, rc = _run(["mullvad", "relay", "set", "location", country, city], timeout=10)
    return rc == 0


def mullvad_reconnect():
    if not have_mullvad():
        return False
    _, rc = _run(["mullvad", "disconnect"], timeout=10)
    time.sleep(1)
    _, rc2 = _run(["mullvad", "connect"], timeout=20)
    return rc2 == 0


# ═══════════════════════════════════════════════════════════════════════════
# rotate the exit — pick a new random location and reconnect
# ═══════════════════════════════════════════════════════════════════════════
def rotate_mullvad(avoid=None):
    """
    picks a new random location, reconnects. returns the (country, city)
    tuple that we switched to, or None on failure.
    """
    locs = mullvad_locations()
    if not locs:
        return None
    avoid = avoid or set()
    choices = [l for l in locs if l not in avoid]
    if not choices:
        choices = locs
    pick = random.choice(choices)
    ok = mullvad_set_location(*pick)
    if not ok:
        return None
    ok = mullvad_reconnect()
    if not ok:
        return None
    return pick


# ═══════════════════════════════════════════════════════════════════════════
# wg-quick — bring up a config, bring down the previous
# ═══════════════════════════════════════════════════════════════════════════
def wg_up(interface, config_path):
    if not have_wg():
        return False
    _, rc = _run(["wg-quick", "up", config_path], timeout=20)
    return rc == 0


def wg_down(interface):
    if not have_wg():
        return False
    _, rc = _run(["wg-quick", "down", interface], timeout=15)
    return rc == 0


# ═══════════════════════════════════════════════════════════════════════════
# nmcli — networkmanager connection switching (for openvpn profiles)
# ═══════════════════════════════════════════════════════════════════════════
def nmcli_connections():
    if not have_nmcli():
        return []
    out, rc = _run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"], timeout=10)
    if rc != 0:
        return []
    conns = []
    for line in out.splitlines():
        if "vpn" in line or "wireguard" in line:
            conns.append(line.split(":", 1)[0])
    return conns


def nmcli_up(name):
    if not have_nmcli():
        return False
    _, rc = _run(["nmcli", "connection", "up", name], timeout=25)
    return rc == 0


def nmcli_down(name):
    if not have_nmcli():
        return False
    _, rc = _run(["nmcli", "connection", "down", name], timeout=15)
    return rc == 0


# ═══════════════════════════════════════════════════════════════════════════
# generic rotator — cycle through a list of callables that each
# disconnect and reconnect to a new exit
# ═══════════════════════════════════════════════════════════════════════════
class Rotator:
    def __init__(self, switch_fn=None, every=60.0):
        self.switch_fn = switch_fn
        self.every = every
        self.last = 0.0
        self.count = 0
        self.history = []

    def maybe_rotate(self):
        now = time.time()
        if now - self.last < self.every:
            return False
        if self.switch_fn is None:
            return False
        res = self.switch_fn()
        self.last = now
        self.count += 1
        self.history.append((now, res))
        dbg("multipliers_distribute", f"rotated to {res!r} (#{self.count})")
        return bool(res)

    def status(self):
        return {
            "rotations": self.count,
            "last": self.history[-1] if self.history else None,
            "every": self.every,
        }


# ═══════════════════════════════════════════════════════════════════════════
# network diagnostics — find local interface addresses for reference
# ═══════════════════════════════════════════════════════════════════════════
def local_ifaces():
    import socket
    out = {}
    try:
        for name in socket.if_nameindex():
            idx, ifname = name
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.2)
                # dummy connect to force ip assignment
                s.connect(("1.1.1.1", 80))
                ip = s.getsockname()[0]
                s.close()
                out[ifname] = ip
            except Exception:
                out[ifname] = None
    except Exception:
        pass
    return out


# ═══════════════════════════════════════════════════════════════════════════
# summary printer for the menu (used by menu.py if it wants to show status)
# ═══════════════════════════════════════════════════════════════════════════
def summary():
    lines = [""]
    lines.append(f"  mullvad cli   {'yes' if have_mullvad() else 'no'}")
    lines.append(f"  wireguard     {'yes' if have_wg() else 'no'}")
    lines.append(f"  openvpn       {'yes' if have_openvpn() else 'no'}")
    lines.append(f"  nmcli         {'yes' if have_nmcli() else 'no'}")
    if have_mullvad():
        st = mullvad_status()
        lines.append(f"  connected     {st['connected']}")
        locs = mullvad_locations()
        lines.append(f"  locations     {len(locs)}")
    ifaces = local_ifaces()
    if ifaces:
        lines.append("  interfaces:")
        for name, ip in ifaces.items():
            lines.append(f"    {name:<12} {ip or '(no ip)'}")
    lines.append("")
    return lines