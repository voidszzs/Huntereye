from _lib import ui

_FORBIDDEN = [
    "child porn", "csam", "underage sex", "underage porn",
    "minor sex", "minor porn", "loli sex", "lolicon porn",
    "shota sex", "shotacon porn", "preteen sex", "preteen porn",
]


def contains_forbidden(text):
    if not text:
        return False
    low = text.lower()
    return any(t in low for t in _FORBIDDEN)


def refuse_forbidden():
    ui.plain(f"  {ui.sym_err()} that request is against the one wall this tool respects.")
    ui.plain(ui.dim("  no further action taken."))


def retype_gate(target):
    ui.plain("")
    ui.plain(f"  about to fire at: {target}")
    ui.plain(ui.dim("  retype the target to confirm you own it:"))
    confirm = ui.ask("confirm")
    if confirm != target:
        ui.plain("  mismatch. cancelled.")
        return False
    return True
