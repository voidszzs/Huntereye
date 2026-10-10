# features/ask.py
# [99] ask — built-in help desk.
#
# type a question, get an answer. no api, no key, no internet.
# matches the question against a set of topics using simple keyword scoring.
# if nothing matches, it prints the list of topics you can ask about.
#
# this file is intentionally self-contained: it needs only _lib.ui and
# nothing else, so it works even if the rest of the tool is broken.

import re
import time

from _lib import ui


# ═══════════════════════════════════════════════════════════════════════════
# topics — (keywords, title, body)
# keep bodies short-ish. multiline is fine.
# ═══════════════════════════════════════════════════════════════════════════
TOPICS = [

    (["target", "set", "ip", "host", "url", "lab"],
     "target",
     "sets the ip / host / url / lab the tool works on.\n"
     "remembered for the whole session. cleared every launch.\n"
     "\n"
     "menu: [01] target\n"
     "\n"
     "accepts:\n"
     "  ipv4        1.2.3.4\n"
     "  host        example.com\n"
     "  url         https://example.com\n"
     "  host:port   192.168.1.1:8080\n"
     "  lab name    lab-nginx / lab-mc / lab-dns\n"
     "\n"
     "after setting, the status panel on the right of the main menu\n"
     "shows the target and a live state (up / down / flapping) with\n"
     "ping ms, updating every 3 seconds."),

    (["dossier", "recon", "scan", "profile"],
     "dossier",
     "profile a target WITHOUT firing anything. read-only.\n"
     "\n"
     "what it does:\n"
     "  - resolves the target to an ip\n"
     "  - port sweep (1-1024 quick, 1-65535 full)\n"
     "  - banner grab + service detect on open ports\n"
     "  - tls certificate info if 443 is open\n"
     "  - cdn / waf detection via headers\n"
     "  - costmap: times common endpoints, ranks the slowest\n"
     "\n"
     "menu: [02] dossier\n"
     "writes nothing to the target. no fire gate."),

    (["vector", "vectors", "stress", "flood"],
     "vectors",
     "stress groups. pick a family of packets and fire them.\n"
     "\n"
     "groups:\n"
     "  l7   http / slowloris\n"
     "  l4   tcp state / half-open / syn\n"
     "  l3   udp / icmp / gre / ip-in-ip\n"
     "  tls  client hello\n"
     "  dns  random subdomain\n"
     "  game minecraft / fivem / source\n"
     "  app  xml / json / graphql / regex / gzip\n"
     "  auth login / pwreset / mfa spam\n"
     "  ipv6 ndp / ra / icmpv6 / frag\n"
     "\n"
     "menu: [03] vectors. before firing you retype the target."),

    (["adaptive"],
     "adaptive",
     "same as vectors but with live measurement.\n"
     "\n"
     "while vectors run it pings the target every 2 seconds and keeps\n"
     "a rolling baseline. if the target degrades (latency up, or\n"
     "errors spike), it slows down or stacks another vector.\n"
     "\n"
     "menu: [04] adaptive"),

    (["multiplier", "origin", "cdn", "bypass"],
     "multipliers",
     "find the real ip behind a cdn. when a site is fronted by\n"
     "cloudflare / fastly / akamai, this looks up certificate\n"
     "transparency logs (crt.sh) and resolves subdomains to see\n"
     "which of them might point at the origin.\n"
     "\n"
     "read-only. no fire.\n"
     "menu: [05] multipliers"),

    (["lab", "lab-nginx", "local"],
     "lab",
     "spin up a local test target.\n"
     "\n"
     "menu: [06] lab\n"
     "  lab-nginx  http on 127.0.0.1:8080 with a slow /search endpoint\n"
     "\n"
     "after starting, set target to 'lab-nginx' with [01] target\n"
     "and everything else works against it. safe sandbox."),

    (["all", "everything"],
     "all",
     "fires every vector applicable to the current target at once.\n"
     "same retype gate as vectors.\n"
     "\n"
     "menu: [07] all"),

    (["monitor", "watch", "live"],
     "monitor",
     "live status view. refreshes every second.\n"
     "\n"
     "shows:\n"
     "  status        up / down / flapping\n"
     "  ping avg      with baseline comparison\n"
     "  ping min/max\n"
     "  samples\n"
     "  errors\n"
     "  ports open\n"
     "  last probe time\n"
     "\n"
     "menu: [08] monitor"),

    (["ping", "latency", "ms"],
     "ping",
     "continuous ping + bar graph.\n"
     "\n"
     "pings as fast as the network answers, one line per ping.\n"
     "summary line under it: min / avg / max / p95 / lost / rate.\n"
     "\n"
     "ctrl+c stops it.\n"
     "menu: [09] ping"),

    (["port", "ports", "scanner"],
     "ports",
     "port scanner.\n"
     "\n"
     "quick (1-1024) or full (1-65535).\n"
     "uses nmap if installed, else pure-python tcp-connect fallback.\n"
     "results are stored in the status panel.\n"
     "\n"
     "menu: [10] ports"),

    (["iplookup", "geo", "whois", "asn", "location", "isp"],
     "iplookup",
     "public info on the target's ip.\n"
     "\n"
     "sections:\n"
     "  local   classification + reverse dns\n"
     "  whois   asn / org / netname / country / abuse contact\n"
     "  geo     country / city / coords / timezone\n"
     "  isp     isp / org / as / as name\n"
     "  flags   hosting / proxy / mobile\n"
     "\n"
     "read-only. no api key. menu: [11] iplookup"),

    (["settings", "config", "configure"],
     "settings",
     "edit settings.yaml and debug/debug.yaml from inside the tool.\n"
     "\n"
     "menu: [12] settings\n"
     "  general   banner + confirm\n"
     "  debug     turn debug lines on/off per area\n"
     "  network   rate + duration\n"
     "  status    ping interval\n"
     "  reset     reset to defaults"),

    (["debug"],
     "debug",
     "every area of the tool has a debug toggle.\n"
     "\n"
     "when on, extra [debug] lines print for that area:\n"
     "timing, ports scanned, state samples, resolved targets, etc.\n"
     "\n"
     "menu: [12] settings -> [02] debug\n"
     "or edit debug/debug.yaml. set global: true for everything."),

    (["help", "usage"],
     "help",
     "plain text help screen.\n"
     "\n"
     "short list of menu, gate, safety.\n"
     "menu: [13] help\n"
     "\n"
     "for freeform questions, use [99] ask (this screen)."),

    (["gate", "retype", "confirm", "own"],
     "gate",
     "every fire feature (vectors, multipliers, all) asks you to\n"
     "retype the target to confirm you own it.\n"
     "\n"
     "if you can't retype it, you don't own it.\n"
     "\n"
     "read-only features (dossier, monitor, ping, ports, iplookup)\n"
     "run without the gate.\n"
     "\n"
     "it's the single line between curiosity and a federal charge.\n"
     "don't skip it."),

    (["safety", "legal", "law", "illegal"],
     "safety",
     "the tool fires real traffic at real targets.\n"
     "\n"
     "firing at anything you do not own is a crime in most\n"
     "countries. the safe path:\n"
     "\n"
     "  - your own home router\n"
     "  - your own laptop on the same lan\n"
     "  - a vm you own\n"
     "  - the built-in lab-nginx ([06] lab)\n"
     "\n"
     "the only hard wall: no csam, ever, in any form."),

    (["color", "colors", "theme", "red", "orange", "melt"],
     "colors",
     "black background. white text. red / orange accents.\n"
     "\n"
     "the banner melts from deep red at the top to golden yellow\n"
     "at the bottom.\n"
     "\n"
     "the state glyph in the status panel is:\n"
     "  green   up\n"
     "  red     down\n"
     "  orange  flapping\n"
     "\n"
     "to change the melt colors, edit _lib/ui.py line:\n"
     "  _MELT_COLORS = [196, 202, 208, 214, 215, 220]"),

    (["banner", "logo"],
     "banner",
     "the big HUNTER3EYE block text at the top of the menu.\n"
     "\n"
     "disable: settings.yaml -> general.show_banner: false\n"
     "edit:    _lib/ui.py, the _LOGO list"),

    (["wipe", "animation"],
     "wipe",
     "the fast red / orange sweep that plays top-to-bottom when you\n"
     "pick a menu item.\n"
     "\n"
     "slower:  run.py, ui.wipe(duration=0.18) -> 0.4\n"
     "faster:  0.08\n"
     "off:     delete the ui.wipe(...) line in run.py"),

    (["crosshair", "cross", "dot"],
     "crosshair",
     "the small round glyph next to 'target:' in the status panel.\n"
     "\n"
     "green when a target is set, grey when not.\n"
     "change the glyph in _lib/ui.py, crosshair()."),

    (["ask", "question", "help desk"],
     "ask",
     "this screen. type a question, get the closest topic.\n"
     "\n"
     "examples:\n"
     "  what does dossier do\n"
     "  tell me about vectors\n"
     "  how does the gate work\n"
     "  what is iplookup\n"
     "  ping\n"
     "  colors\n"
     "\n"
     "blank line goes back to the menu."),
]


# ═══════════════════════════════════════════════════════════════════════════
# matching — score every topic against the question
# ═══════════════════════════════════════════════════════════════════════════
_WORD_RE = re.compile(r"[a-zA-Z0-9_]+")


def _tokens(q):
    return set(m.group(0).lower() for m in _WORD_RE.finditer(q or ""))


def _score(question_lower, tokens, keys):
    score = 0
    for k in keys:
        k = k.lower()
        if " " in k:
            if k in question_lower:
                score += 3
        else:
            if k in tokens:
                score += 3
            elif k in question_lower:
                score += 1
    return score


def _match(q):
    q = (q or "").lower().strip()
    if not q:
        return None
    toks = _tokens(q)
    best = None
    best_score = 0
    for keys, title, body in TOPICS:
        s = _score(q, toks, keys)
        if s > best_score:
            best_score = s
            best = (title, body)
    return best


def _list_topics():
    return [t for _k, t, _b in TOPICS]


# ═══════════════════════════════════════════════════════════════════════════
# rendering
# ═══════════════════════════════════════════════════════════════════════════
def _render(title, body):
    lines = [""]
    for line in body.split("\n"):
        lines.append("  " + line)
    lines.append("")
    ui.box(title, lines)


def _render_unmatched(q):
    ui.plain("")
    ui.plain("  " + ui.sym_err() + f" no topic matched \"{q[:40]}\".")
    ui.plain("")
    ui.plain("  try one of these topics:")
    for t in _list_topics():
        ui.plain("    - " + t)
    ui.plain("")
    ui.plain("  blank line goes back to the menu.")
    ui.plain("")


# ═══════════════════════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════════════════════
def run():
    ui.plain("")
    ui.plain("  " + ui.red("ASK") + "  " + ui.dim("built-in help desk"))
    ui.plain("  " + ui.dim("type a question like 'what does dossier do'"))
    ui.plain("  " + ui.dim("or just a keyword. blank line to go back."))
    ui.plain("")

    while True:
        q = ui.ask("ask").strip()

        # back signals
        if q == "" or q.lower() in ("00", "0", "q", "back", "exit"):
            return

        m = _match(q)
        if not m:
            _render_unmatched(q)
            continue

        title, body = m
        _render(title, body)
        ui.plain("")


# ═══════════════════════════════════════════════════════════════════════════
# introspection (used by other modules in future)
# ═══════════════════════════════════════════════════════════════════════════
def topics():
    return list(_list_topics())


def has_topic(name):
    return name.lower() in (t.lower() for t in _list_topics())