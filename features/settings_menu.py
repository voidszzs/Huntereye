from _lib import ui
from _lib.settings import all_values, set_value, reset
from _lib.debug import all_toggles, set_toggle, save as save_debug

SECTIONS = [
    ("01", "general",  "banner, confirm"),
    ("02", "debug",    "toggle debug lines"),
    ("03", "network",  "rate, duration"),
    ("04", "status",   "ping interval"),
    ("05", "reset",    "reset to defaults"),
    ("00", "back",     "return"),
]


def _edit(section):
    data = all_values().get(section, {})
    if not isinstance(data, dict):
        return
    keys = list(data.keys())
    lines = [""]
    for i, k in enumerate(keys, 1):
        lines.append(f"  [{i:>2}]  {k:<22} {data[k]}")
    lines += ["", "  [00] back", ""]
    ui.box(f"settings / {section}", lines)
    ch = ui.ask("edit key number")
    if ch in ("0", "00", ""):
        return
    if not ch.isdigit():
        return
    idx = int(ch) - 1
    if idx < 0 or idx >= len(keys):
        return
    key = keys[idx]
    new = ui.ask(f"new value for {key}", str(data[key]))
    set_value(f"{section}.{key}", _parse(new))
    ui.plain(f"  set.")


def _debug():
    while True:
        t = all_toggles()
        items = sorted(t.keys())
        lines = [""]
        for i, k in enumerate(items, 1):
            on = "ON " if t[k] else "off"
            lines.append(f"  [{i:>2}]  {on}   {k}")
        lines += ["", "  [s] save  [r] reload  [a] off  [A] on  [00] back", ""]
        ui.box("settings / debug", lines)
        ch = ui.ask("select")
        if ch in ("0", "00", ""):
            return
        if ch == "s":
            save_debug(); continue
        if ch == "r":
            from _lib.debug import reload
            reload(); continue
        if ch == "a":
            for k in items: set_toggle(k, False)
            save_debug(); continue
        if ch == "A":
            for k in items: set_toggle(k, True)
            save_debug(); continue
        if ch.isdigit():
            idx = int(ch) - 1
            if 0 <= idx < len(items):
                set_toggle(items[idx], not t[items[idx]])


def _parse(v):
    v = v.strip().lower()
    if v in ("true", "yes", "on", "1"):
        return True
    if v in ("false", "no", "off", "0"):
        return False
    try:
        return int(v)
    except ValueError:
        pass
    return v


def run():
    while True:
        ui.submenu("settings", SECTIONS)
        ch = ui.ask("select")
        if ch in ("0", "00", ""):
            return
        if ch == "01":
            _edit("general")
        elif ch == "02":
            _debug()
        elif ch == "03":
            _edit("network")
        elif ch == "04":
            _edit("status")
        elif ch == "05":
            if ui.ask("really reset? [y/N]").lower() == "y":
                reset(); ui.plain("  reset done.")
