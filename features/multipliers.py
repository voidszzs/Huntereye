from argparse import Namespace
from _lib import ui
from _lib.status import current_target
from _lib.config import resolve_target
from _lib.ring0.host import full_recon
from _lib.ring2.origin_hunt import hunt
from _lib.security import retype_gate, contains_forbidden, refuse_forbidden


def run():
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
    args = Namespace(mode="bypass", vectors="auto", rate=50, duration=30,
                     allow_reckless=False)
    d = full_recon(t, args)
    cands = hunt(d, args) or []
    if not cands:
        ui.plain("  no candidates.")
        return
    lines = [""]
    for c in cands[:30]:
        lines.append(f"  {c['sub']:<45} -> {c['ip']}")
    lines.append("")
    ui.box("candidates", lines)
