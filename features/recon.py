# [02] dossier — recon, no traffic. warns first, then runs.
from argparse import Namespace

from _lib import ui
from _lib.status import current_target, set_open_ports
from _lib.config import resolve_target
from _lib.ring0.host import full_recon


def run():
    target = current_target()
    if not target:
        ui.plain("  no target set. use [01] first.")
        return

    # warn + confirm
    ui.box("dossier", [
        "",
        f"  target      {target}",
        "",
        "  what this does:",
        "    - resolves the target ip",
        "    - port sweep (1-1024 or common)",
        "    - banner grab + service detect",
        "    - tls certificate info if 443 open",
        "    - cdn / waf detection",
        "    - costmap: times every endpoint, ranks slowest",
        "",
        "  this is read-only. no fire, no flood, no packets",
        "  beyond a normal port scan and a few http GETs.",
        "",
        "  press enter to start, or type 00 to cancel.",
        "",
    ])
    ch = ui.ask("confirm").strip().lower()
    if ch in ("0", "00", "q", "n", "no"):
        ui.plain("  cancelled.")
        return

    ui.plain("")
    ui.plain("  " + ui.fire_line(active=True, label="reconning"))
    ui.plain("")

    t = resolve_target(target)
    args = Namespace(mode="recon", vectors="auto", rate=50, duration=30,
                     allow_reckless=False)
    d = full_recon(t, args)
    try:
        set_open_ports([p for _, p in d.get("ports", [])])
    except Exception:
        pass

    lines = [
        "",
        f"  target      {target}",
        f"  ipv4        {d.get('ipv4')}",
        f"  ipv6        {d.get('ipv6')}",
        f"  class       {d.get('class')}",
        f"  ports       {d.get('ports')}",
        f"  deps        {d.get('deps')}",
        "",
    ]
    cm = d.get("costmap") or []
    if cm:
        lines.append("  costmap (slowest first):")
        for c in cm[:8]:
            lines.append(f"    {c['time']:>7.3f}s  {c['code']}  {c['url']}")
    ui.box("dossier results", lines)
    ui.plain(f"  {ui.sym_ok()} dossier complete.")
    ui.plain("  returning to menu.")