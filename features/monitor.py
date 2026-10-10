import time
from _lib import ui
from _lib.platform import clear
from _lib.status import (current_target, stats, status_line,
                         set_open_ports)
from _lib.config import resolve_target


def _scan(target):
    try:
        from _lib.ring0.host import port_sweep
        t = resolve_target(target)
        h = t.get("host") or t.get("url")
        if h and (h.startswith("http://") or h.startswith("https://")):
            h = h.split("//", 1)[1].split("/", 1)[0]
        if h and h.count(":") == 1:
            h = h.split(":", 1)[0]
        p = port_sweep(h, quick=True)
        set_open_ports([x for _, x in p])
        return p
    except Exception:
        return []


def run():
    target = current_target()
    if not target:
        ui.plain("  no target set. use [01] first.")
        return
    cached = None
    while True:
        clear()
        st = stats()
        ports_s = "-" if cached is None else (", ".join(str(p) for _, p in cached) or "-")
        lines = ["",
                 f"  target        {target}",
                 "",
                 f"  status        {status_line()}",
                 f"  ping avg      {st['avg']:.1f} ms" if st['avg'] is not None else "  ping avg      -",
                 f"  ping min/max  {st['min']:.1f} / {st['max']:.1f}" if st['min'] is not None else "  ping min/max  - / -",
                 f"  samples       {st['samples']}",
                 f"  errors        {st['errors']}",
                 f"  ports open    {ports_s}",
                 f"  last probe    {time.strftime('%H:%M:%S')}",
                 ""]
        ui.box("monitor", lines)
        ui.plain("  [R] refresh ports    [Q] back")
        try:
            k = input("  > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return
        if k == "q":
            return
        if k == "r":
            ui.plain("  scanning ...")
            cached = _scan(target)
        time.sleep(0.4)
