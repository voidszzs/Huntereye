# hunter3eye — ui. red/orange accents, melting banner, wipe animation, crosshair.

import os
import re
import shutil
import sys
import time

from _lib.platform import terminal_supports_unicode, is_windows

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def _fg(n):
    return f"\033[38;5;{n}m"


def red(t):        return _fg(196) + t + RESET
def red_bright(t): return _fg(203) + t + RESET
def orange(t):     return _fg(208) + t + RESET
def gold(t):       return _fg(220) + t + RESET
def green(t):      return _fg(114) + t + RESET
def grey(t):       return _fg(245) + t + RESET
def white(t):      return _fg(252) + t + RESET


def bold(t):  return f"{BOLD}{white(t)}{RESET}"
def dim(t):   return f"{DIM}{grey(t)}{RESET}"
def plain(t): print(t, flush=True)


_MELT_COLORS = [196, 202, 208, 214, 215, 220]
_BORDER_COLOR = 196
_SUB_COLOR = 220

_UNICODE = None
_BANNER_VISIBLE = True


def _u():
    global _UNICODE
    if _UNICODE is None:
        _UNICODE = terminal_supports_unicode()
    return _UNICODE


def set_banner_visible(v):
    global _BANNER_VISIBLE
    _BANNER_VISIBLE = bool(v)


def _term_width():
    try:
        w = shutil.get_terminal_size((140, 30)).columns
        return max(60, min(w, 240))
    except Exception:
        return 140


def _bchars():
    if _u():
        return {"tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│",
                "dtl": "╔", "dtr": "╗", "dbl": "╚", "dbr": "╝",
                "dh": "═", "dv": "║"}
    return {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|",
            "dtl": "+", "dtr": "+", "dbl": "+", "dbr": "+",
            "dh": "=", "dv": "|"}


def _platform_name():
    if is_windows():
        return "windows"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    return os.name


def _fit(s, w):
    if len(s) > w:
        s = s[:w]
    return s + " " * (w - len(s))


def _center(text, width):
    pad = width - len(text)
    if pad <= 0:
        return text[:width]
    left = pad // 2
    right = pad - left
    return " " * left + text + " " * right


def _strip_ansi(s):
    return re.sub(r"\033\[[0-9;]*m", "", s)


# ─── banner ────────────────────────────────────────────────────────────────
_LOGO = [
    "  ██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗ ██████╗ ███████╗██╗   ██╗███████╗",
    "  ██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗╚════██╗██╔════╝╚██╗ ██╔╝██╔════╝",
    "  ███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝ █████╔╝█████╗   ╚████╔╝ █████╗ ",
    "  ██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗ ╚═══██╗██╔══╝    ╚██╔╝  ██╔══╝ ",
    "  ██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║██████╔╝███████╗   ██║   ███████╗",
    "  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝   ╚═╝   ╚══════╝",
]


def banner(version="8.0.0"):
    if not _BANNER_VISIBLE:
        return
    b = _bchars()
    logo_w = max(len(r) for r in _LOGO)
    inner = logo_w + 4
    screen = _term_width()
    sp = " " * max(0, (screen - (inner + 2)) // 2)
    print(sp + _fg(_BORDER_COLOR) + b["dtl"] + b["dh"] * inner + b["dtr"] + RESET)
    print(sp + _fg(_BORDER_COLOR) + b["dv"] + RESET + " " * inner + _fg(_BORDER_COLOR) + b["dv"] + RESET)
    for i, row in enumerate(_LOGO):
        color = _MELT_COLORS[min(i, len(_MELT_COLORS) - 1)]
        body = " " * ((inner - len(row)) // 2) + row
        body = _fit(body, inner)
        print(sp + _fg(color) + b["dv"] + RESET + _fg(color) + body + RESET + _fg(color) + b["dv"] + RESET)
    print(sp + _fg(_SUB_COLOR) + b["dv"] + RESET + " " * inner + _fg(_SUB_COLOR) + b["dv"] + RESET)
    sub1 = _center("terminal multitool  •  lab / research only", inner)
    sub2 = _center(f"version {version}  •  {_platform_name()}", inner)
    print(sp + _fg(_SUB_COLOR) + b["dv"] + RESET + sub1 + _fg(_SUB_COLOR) + b["dv"] + RESET)
    print(sp + _fg(_SUB_COLOR) + b["dv"] + RESET + sub2 + _fg(_SUB_COLOR) + b["dv"] + RESET)
    print(sp + _fg(_SUB_COLOR) + b["dbl"] + b["dh"] * inner + b["dbr"] + RESET)
    print()


# ─── generic box ───────────────────────────────────────────────────────────
def _title_bar(title, inner, ch, color=196):
    head = ch["h"] * 2 + " " + title.upper() + " "
    if len(head) > inner:
        head = head[:inner]
    return _fg(color) + head + ch["h"] * (inner - len(head)) + RESET


def box(title, body_lines, width=82):
    b = _bchars()
    inner = width - 2
    pad = " " * max(0, (_term_width() - width) // 2)
    print(pad + _fg(_BORDER_COLOR) + b["tl"] + RESET + _title_bar(title, inner, b, 196) + _fg(_BORDER_COLOR) + b["tr"] + RESET)
    for line in body_lines:
        print(pad + _fg(_BORDER_COLOR) + b["v"] + RESET + _fit(line, inner) + _fg(_BORDER_COLOR) + b["v"] + RESET)
    print(pad + _fg(_BORDER_COLOR) + b["bl"] + b["h"] * inner + b["br"] + RESET)


def submenu(title, items):
    b = _bchars()
    width = 82
    inner = width - 2
    pad = " " * max(0, (_term_width() - width) // 2)
    print(pad + _fg(_BORDER_COLOR) + b["tl"] + RESET + _title_bar(title, inner, b, 196) + _fg(_BORDER_COLOR) + b["tr"] + RESET)
    print(pad + _fg(_BORDER_COLOR) + b["v"] + RESET + " " * inner + _fg(_BORDER_COLOR) + b["v"] + RESET)
    for key, label, desc in items:
        visible = f"  [{key}]  {label:<11} {desc}"
        colored = "  " + _fg(220) + f"[{key}]" + RESET + "  " + _fg(252) + f"{label:<11}" + RESET + " " + _fg(245) + desc + RESET
        pad_to = inner - len(visible)
        print(pad + _fg(_BORDER_COLOR) + b["v"] + RESET + colored + " " * max(0, pad_to) + _fg(_BORDER_COLOR) + b["v"] + RESET)
    print(pad + _fg(_BORDER_COLOR) + b["v"] + RESET + " " * inner + _fg(_BORDER_COLOR) + b["v"] + RESET)
    print(pad + _fg(_BORDER_COLOR) + b["bl"] + b["h"] * inner + b["br"] + RESET)
    print()


# ─── crosshair glyph ───────────────────────────────────────────────────────
def crosshair(active=False):
    if _u():
        icon = "◉"
    else:
        icon = "(*)"
    if active:
        return green(icon)
    return grey(icon)


# ─── main menu ─────────────────────────────────────────────────────────────
def _grid_layout(items):
    longest = max(len(label) for _, label, _, _ in items)
    cell_w = longest + 10
    screen = _term_width()
    available = screen - 34 - 4
    max_cols = max(1, available // cell_w)
    columns = min(4, max_cols) if max_cols >= 1 else 1
    if columns < 1:
        columns = 1
    n = len(items)
    per_col = (n + columns - 1) // columns
    cols = []
    for c in range(columns):
        col = []
        for r in range(per_col):
            idx = c * per_col + r
            col.append(items[idx] if idx < n else None)
        cols.append(col)
    height = max(len(c) for c in cols)
    rows = []
    for r in range(height):
        cells = []
        for c in range(columns):
            it = cols[c][r] if r < len(cols[c]) else None
            if it is None:
                cells.append(" " * cell_w)
            else:
                key, label, _d, _p = it
                visible = f"  [{key}] {label}"
                pad = " " * (cell_w - len(visible))
                colored = "  " + _fg(220) + f"[{key}]" + RESET + " " + _fg(252) + label + RESET + pad
                cells.append(colored)
        rows.append((cells, cell_w))
    return rows, columns, cell_w


def main_menu(items):
    b = _bchars()
    from _lib.status import status_line, stats, current_target, get_open_ports
    tgt = current_target() or "(not set)"
    if len(tgt) > 18:
        tgt = tgt[:17] + "…"
    st = status_line()
    sn = stats()
    avg = sn.get("avg")
    ports = get_open_ports()
    ports_s = "-"
    if ports:
        ports_s = ",".join(str(p) for p in ports[:8])
        if len(ports) > 8:
            ports_s = ports_s[:20] + ".."

    active = bool(current_target())
    cross = crosshair(active)

    status_lines = [
        "",
        f"  {cross} target   {tgt}",
        f"     state    {st}",
        f"     ping     {avg:.1f} ms" if avg is not None else "     ping     -",
        f"     samples  {sn.get('samples', 0)}",
        f"     errors   {sn.get('errors', 0)}",
        f"     ports    {ports_s}",
        f"     last     {time.strftime('%H:%M:%S')}",
        "",
    ]
    rw = 28
    ri = rw - 2

    grid_rows, columns, cell_w = _grid_layout(items)
    left_w = cell_w * columns + 2
    li = left_w - 2

    lt = _fg(_BORDER_COLOR) + b["tl"] + RESET + _title_bar("main menu", li, b, 196) + _fg(_BORDER_COLOR) + b["tr"] + RESET
    rt = _fg(_BORDER_COLOR) + b["tl"] + RESET + _title_bar("status", ri, b, 220) + _fg(_BORDER_COLOR) + b["tr"] + RESET
    lb = _fg(_BORDER_COLOR) + b["bl"] + b["h"] * li + b["br"] + RESET
    rb = _fg(_BORDER_COLOR) + b["bl"] + b["h"] * ri + b["br"] + RESET

    gap = 2
    total = left_w + gap + rw
    pad = " " * max(0, (_term_width() - total) // 2)

    left_rows = [("", 0)]
    for cells, cw in grid_rows:
        visible_len = sum(len(_strip_ansi(cell)) for cell in cells)
        line = "".join(cells)
        left_rows.append((line, visible_len))
    left_rows.append(("", 0))

    print(pad + lt + " " * gap + rt)
    rows = max(len(left_rows), len(status_lines))
    for i in range(rows):
        l_line, l_len = left_rows[i] if i < len(left_rows) else ("", 0)
        r_line = status_lines[i] if i < len(status_lines) else ""
        l_pad = " " * max(0, li - l_len)
        print(pad + _fg(_BORDER_COLOR) + b["v"] + RESET + l_line + l_pad +
              _fg(_BORDER_COLOR) + b["v"] + RESET + " " * gap +
              _fg(_BORDER_COLOR) + b["v"] + RESET + _fit(r_line, ri) +
              _fg(_BORDER_COLOR) + b["v"] + RESET)
    print(pad + lb + " " * gap + rb)
    print()


def footer(next_screen=True, back=True, quit_=True, select=True):
    parts = []
    if next_screen: parts.append("[N] next")
    if back:        parts.append("[B] back")
    if quit_:       parts.append("[Q] quit")
    if select:      parts.append("enter = select")
    msg = "  " + "    ".join(parts)
    pad = " " * max(0, (_term_width() - len(msg)) // 2)
    print(pad + grey(msg))
    print()


def ask(prompt, default=""):
    p = f"  {prompt} > "
    pad = " " * max(0, (_term_width() - len(p) - 20) // 2)
    try:
        v = input(pad + _fg(196) + p + RESET).strip()
        return v or default
    except (EOFError, KeyboardInterrupt):
        return default


def pause(msg="enter"):
    try:
        input(f"\n  [{msg}] ")
    except (EOFError, KeyboardInterrupt):
        print()


# ─── wipe animation — plays on menu select ─────────────────────────────────
def wipe(duration=0.22, cols=None):
    # fast top→bottom sweep. hard-clears on every frame so nothing stacks.
    width = cols or min(_term_width() - 4, 100)
    pad = " " * max(0, (_term_width() - width) // 2)
    frames = 7
    delay = max(0.012, duration / frames)
    total_rows = 18
    for i in range(frames):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
        top_blank = (i * total_rows) // frames
        for _ in range(top_blank):
            print()
        color = 196 if i % 2 == 0 else 203
        bar = "─" * width
        print(pad + _fg(color) + bar + RESET)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


# ─── fire line for long operations ─────────────────────────────────────────
_FIRE_FRAMES = [
    "  [=       ] firing ...",
    "  [==      ] firing ...",
    "  [===     ] firing ...",
    "  [====    ] firing ...",
    "  [=====   ] firing ...",
    "  [======  ] firing ...",
    "  [======= ] firing ...",
    "  [========] firing ...",
    "  [ =======] firing ...",
    "  [  ======] firing ...",
    "  [   =====] firing ...",
    "  [    ====] firing ...",
    "  [     ===] firing ...",
    "  [      ==] firing ...",
    "  [       =] firing ...",
]
_fire_idx = [0]


def fire_line(active=True, label="firing"):
    if not active:
        return grey("  [ idle ]")
    frame = _FIRE_FRAMES[_fire_idx[0] % len(_FIRE_FRAMES)]
    _fire_idx[0] += 1
    text = frame.replace("firing", label)
    return _fg(203) + text + RESET


def sym_up():      return _fg(114) + "● up" + RESET       if _u() else "o up"
def sym_down():    return _fg(196) + "○ down" + RESET     if _u() else ". down"
def sym_flap():    return _fg(208) + "◐ flapping" + RESET if _u() else "~ flapping"
def sym_unknown(): return _fg(245) + "○ unknown" + RESET  if _u() else ". unknown"
def sym_ok():      return _fg(114) + "✓" + RESET          if _u() else "ok"
def sym_err():     return _fg(196) + "✗" + RESET          if _u() else "x"


def panel(title, lines, width=82):
    box(title, lines, width=width)
    print()