from argparse import Namespace
from _lib import ui
from _lib.status import current_target
from _lib.config import resolve_target
from _lib.ring0.host import full_recon
from _lib.ring1.selector import select
from _lib.ring3.loop import adaptive_run
from _lib.security import retype_gate, contains_forbidden, refuse_forbidden

GROUPS = [
    ("01", "l7",   "http / slowloris"),
    ("02", "l4",   "tcp state / half-open"),
    ("03", "l3",   "udp / icmp"),
    ("04", "tls",  "client hello"),
    ("05", "dns",  "random subdomain"),
    ("06", "game", "minecraft / source"),
    ("09", "all",  "everything applicable"),
    ("00", "back", "return to main menu"),
]


def _pick():
    ui.submenu("vectors", [(k, n, d) for k, n, d in GROUPS])
    return ui.ask("select")


def run():
    target = current_target()
    if not target:
        ui.plain("  no target set. use [01] first.")
        return
    if contains_forbidden(target):
        refuse_forbidden()
        return
    choice = _pick()
    if choice in ("0", "00", ""):
        return
    if not any(k == choice for k, _, _ in GROUPS):
        return
    group = next(n for k, n, _ in GROUPS if k == choice)
    dur = ui.ask("duration seconds", "30")
    rate = ui.ask("rate", "50")
    try:
        dur_i, rate_i = int(dur), int(rate)
    except ValueError:
        ui.plain("  bad numbers.")
        return
    if not retype_gate(target):
        return
    t = resolve_target(target)
    args = Namespace(mode="stress", vectors=group, rate=rate_i, duration=dur_i,
                     allow_reckless=True)
    d = full_recon(t, args)
    plan = select(d, args)
    if not plan:
        ui.plain("  no vectors applicable.")
        return
    ui.plain(f"  firing {len(plan)}: {', '.join(v.name for v in plan)}")
    ui.ask("enter to start")
    adaptive_run(t, d, plan, args)


def run_all():
    target = current_target()
    if not target:
        ui.plain("  no target set. use [01] first.")
        return
    if contains_forbidden(target):
        refuse_forbidden()
        return
    if not retype_gate(target):
        return
    t = resolve_target(target)
    args = Namespace(mode="full", vectors="all", rate=50, duration=30,
                     allow_reckless=True)
    d = full_recon(t, args)
    plan = select(d, args)
    if not plan:
        ui.plain("  no vectors applicable.")
        return
    ui.plain(f"  firing {len(plan)}: {', '.join(v.name for v in plan)}")
    ui.ask("enter to start")
    adaptive_run(t, d, plan, args)
