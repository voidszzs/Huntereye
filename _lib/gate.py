# target check helper. one place, one message, all features call it.

from _lib import ui
from _lib.status import current_target, set_target


def require_target(prompt_if_missing=True):
    # returns the target string, or None if user cancelled.
    t = current_target()
    if t:
        return t

    ui.plain("")
    ui.plain("  " + ui.sym_err() + " no target set.")
    if not prompt_if_missing:
        ui.plain("  use menu [01] to set one first.")
        return None

    ui.plain("  enter an ip / host / url now, or blank to cancel.")
    v = ui.ask("target").strip()
    if not v:
        return None
    if v.lower() in ("0", "00", "q", "exit"):
        return None
    set_target(v)
    ui.plain("  " + ui.sym_ok() + " target set: " + v)
    return v