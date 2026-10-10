#!/usr/bin/env python3
# hunter3eye v8 — terminal multitool. research / lab only.
# this is the top-level entry point. every menu item maps to a feature.

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

VERSION = "8.0.0"

from _lib import ui
from _lib.platform import enable_ansi, hard_clear, center_window
from _lib.settings import s
from _lib.debug import dbg
from _lib.status import start_background, stop_background, current_target


# ═══════════════════════════════════════════════════════════════════════════
# menu — every entry
# needs_target: if True and no target set, the row is dimmed and selecting
# it redirects to the target menu instead of running the feature.
# ═══════════════════════════════════════════════════════════════════════════
MENU = [
    ("01", "target",      "set the ip / host / url / lab",  "features.target",          False),
    ("02", "dossier",     "recon, no traffic",              "features.recon",           True),
    ("03", "vectors",     "stress groups",                  "features.vectors",         True),
    ("04", "adaptive",    "vectors + live monitor",         "features.adaptive",        True),
    ("05", "multipliers", "origin hunt, bypass helpers",    "features.multipliers",     True),
    ("06", "lab",         "spin up local test targets",     "features.lab",             False),
    ("07", "all",         "fire every vector at once",      "features.vectors:run_all", True),
    ("08", "monitor",     "live up/down + ping panel",      "features.monitor",         True),
    ("09", "ping",        "continuous ping graph",          "features.ping",            True),
    ("10", "ports",       "port scanner",                   "features.ports",           True),
    ("11", "iplookup",    "geo / isp / asn of the target",  "features.iplookup",        True),
    ("12", "settings",    "edit config",                    "features.settings_menu",   False),
    ("13", "help",        "usage and safety",               "features.help",            False),
    ("99", "ask",         "ask about the tool",             "features.ask",             False),
    ("00", "exit",        "leave",                          None,                       False),
]


# ═══════════════════════════════════════════════════════════════════════════
# input normalization
# ═══════════════════════════════════════════════════════════════════════════
def _norm(choice):
    if choice is None:
        return "00"
    c = choice.strip().lower()
    if c in ("", "q", "e", "exit", "0", "00"):
        return "00"
    if c.isdigit():
        n = int(c)
        if 0 < n < 100:
            return f"{n:02d}"
    return c


def _resolve(path):
    if ":" in path:
        return path.split(":", 1)
    return path, "run"


# ═══════════════════════════════════════════════════════════════════════════
# dispatch
# ═══════════════════════════════════════════════════════════════════════════
def _no_target_redirect():
    hard_clear()
    ui.plain("")
    ui.plain("  " + ui.sym_err() + " " + ui.red("please select a target first."))
    ui.plain("  " + ui.grey("opening [01] target now..."))
    ui.plain("")
    time.sleep(0.9)
    try:
        __import__("features.target")
        getattr(sys.modules["features.target"], "run")()
    except Exception as e:
        ui.plain("  " + ui.sym_err() + " could not open target menu: " + str(e))
        ui.pause("enter")


def dispatch(choice):
    have_target = bool(current_target())
    for key, _lbl, _desc, path, needs_target in MENU:
        if choice == key:
            if path is None:
                return "exit"
            if needs_target and not have_target:
                _no_target_redirect()
                return "ok"
            mod, attr = _resolve(path)
            __import__(mod)
            getattr(sys.modules[mod], attr)()
            return "ok"
    return None


# ═══════════════════════════════════════════════════════════════════════════
# drawing
# ═══════════════════════════════════════════════════════════════════════════
def draw_menu():
    hard_clear()
    ui.banner(VERSION)
    ui.main_menu([(k, l, d, p) for k, l, d, p, _n in MENU])
    ui.footer(False, False, True, True)


# ═══════════════════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════════════════
def main():
    enable_ansi()
    center_window(120, 40)
    ui.set_banner_visible(bool(s("general.show_banner", True)))
    start_background()

    try:
        while True:
            draw_menu()
            choice = _norm(ui.ask("select"))
            if choice == "00":
                hard_clear()
                ui.plain("bye.")
                return 0

            ui.wipe(duration=0.18)
            hard_clear()

            ui.plain(ui.fire_line("executing"))
            ui.plain("")

            result = None
            try:
                result = dispatch(choice)
            except KeyboardInterrupt:
                result = "ok"
            except Exception as e:
                hard_clear()
                ui.plain("")
                ui.plain(f"error: {type(e).__name__}: {e}")
                dbg("run", f"dispatch error: {e!r}")
                ui.pause()
                continue

            if result is None:
                time.sleep(0.4)
                continue
            if result == "exit":
                return 0

            hard_clear()
    finally:
        try:
            stop_background()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# entry
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        ui.plain("")
        ui.plain("interrupted.")
        try:
            stop_background()
        except Exception:
            pass
        sys.exit(130)