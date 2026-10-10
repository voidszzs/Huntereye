# [01] target — set / show / clear with a dedicated clear option.
from _lib import ui
from _lib.status import current_target, set_target, clear_target
from _lib.security import contains_forbidden, refuse_forbidden

ITEMS = [
    ("01", "set target",   "type ipv4 / host / url / lab"),
    ("02", "clear target", "remove the remembered target"),
    ("03", "show target",  "print the current target"),
    ("00", "back",         "return to main menu"),
]


def _show():
    cur = current_target()
    ui.plain("")
    ui.plain(f"  current target: {cur if cur else '(not set)'}")
    ui.plain("")


def _set():
    ui.plain("")
    ui.plain("  examples:")
    ui.plain("    ipv4        1.2.3.4")
    ui.plain("    host        example.com")
    ui.plain("    url         https://example.com")
    ui.plain("    host:port   192.168.1.1:8080")
    ui.plain("    lab name    lab-nginx / lab-mc / lab-dns")
    ui.plain("")
    value = ui.ask("new target (blank to cancel)")
    if value == "":
        ui.plain("  cancelled.")
        return
    if contains_forbidden(value):
        refuse_forbidden()
        return
    if set_target(value):
        ui.plain(f"  {ui.sym_ok()} target set: {value}")
    else:
        ui.plain(f"  {ui.sym_err()} could not save target.")


def _clear():
    if not current_target():
        ui.plain("  no target to clear.")
        return
    confirm = ui.ask("really clear the target? [y/N]").lower()
    if confirm != "y":
        ui.plain("  cancelled.")
        return
    if clear_target():
        ui.plain(f"  {ui.sym_ok()} target cleared.")
    else:
        ui.plain(f"  {ui.sym_err()} could not clear target.")


def run():
    while True:
        ui.plain("")
        ui.plain(f"  current: {current_target() or '(not set)'}")
        ui.submenu("target", ITEMS)
        ch = ui.ask("select")
        if ch in ("0", "00", ""):
            return
        if ch == "01" or ch == "1":
            _set()
        elif ch == "02" or ch == "2":
            _clear()
        elif ch == "03" or ch == "3":
            _show()