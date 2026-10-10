# live status daemon. utf-8 safe ping + tcp fallback. no background subprocess threads.
import socket
import threading
import time
from pathlib import Path

from _lib.settings import s
from _lib.platform import ping_once
from _lib.debug import dbg

_ROOT = Path(__file__).resolve().parent.parent
_TARGET = _ROOT / ".target"
_LOG = _ROOT / "out" / "session.log"

_HISTORY = []
_MAX = 60
_LOCK = threading.Lock()
_STOP = threading.Event()
_THREAD = None
_LAST = None
_OPEN = []


def current_target():
    try:
        if _TARGET.is_file():
            t = _TARGET.read_text(encoding="utf-8").strip()
            return t or None
    except Exception:
        pass
    return None


def set_target(value):
    try:
        _TARGET.parent.mkdir(parents=True, exist_ok=True)
        _TARGET.write_text(value.strip(), encoding="utf-8", newline="\n")
        _reset()
        return True
    except Exception:
        return False


def clear_target():
    try:
        if _TARGET.is_file():
            _TARGET.unlink()
        _reset()
        return True
    except Exception:
        return False


def _log_line(line):
    if not s("status.log_changes", True):
        return
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(_LOG, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    except Exception:
        pass


def _clean(host):
    if not host:
        return host
    if host.startswith(("http://", "https://")):
        host = host.split("//", 1)[1]
    host = host.split("/", 1)[0]
    if host.count(":") == 1:
        host = host.split(":", 1)[0]
    return host


def _tcp_check(host, timeout=3):
    # try 443, then 80. returns ms or None. this is the "site is up but
    # blocks icmp" fallback used by every real monitoring tool.
    for port in (443, 80):
        try:
            t0 = time.time()
            with socket.create_connection((host, port), timeout=timeout):
                return (time.time() - t0) * 1000.0
        except Exception:
            continue
    return None


def probe(host, timeout=3):
    # returns (ms, method) where method is "icmp" or "tcp" or None.
    host = _clean(host)
    if not host:
        return None, None
    try:
        socket.getaddrinfo(host, None)
    except Exception:
        return None, None

    ms = ping_once(host, timeout=timeout)
    if ms is not None:
        return ms, "icmp"

    ms = _tcp_check(host, timeout=timeout)
    if ms is not None:
        return ms, "tcp"

    return None, None


def ping_ms(host, timeout=3):
    ms, _ = probe(host, timeout=timeout)
    return ms


def _sample():
    host = current_target()
    if not host:
        return
    ms, method = probe(host)
    with _LOCK:
        _HISTORY.append({"t": time.time(), "ms": ms, "method": method})
        if len(_HISTORY) > _MAX:
            del _HISTORY[: len(_HISTORY) - _MAX]
    state = "up" if ms is not None else "down"
    global _LAST
    if _LAST is not None and state != _LAST:
        _log_line(f"state change: {_LAST} -> {state}   target={host}   via {method or '-'}")
    _LAST = state


def _loop():
    interval = float(s("status.interval", 3) or 3)
    while not _STOP.is_set():
        try:
            _sample()
        except Exception as e:
            dbg("status", f"{e!r}")
        _STOP.wait(interval)


def start_background():
    if not s("status.enabled", True):
        return
    global _THREAD
    if _THREAD and _THREAD.is_alive():
        return
    _STOP.clear()
    _THREAD = threading.Thread(target=_loop, daemon=True)
    _THREAD.start()


def stop_background():
    _STOP.set()


def _reset():
    global _LAST, _OPEN
    with _LOCK:
        _HISTORY.clear()
    _LAST = None
    _OPEN = []


def history():
    with _LOCK:
        return list(_HISTORY)


def stats():
    with _LOCK:
        vals = [x["ms"] for x in _HISTORY if x["ms"] is not None]
        total = len(_HISTORY)
    if not vals:
        return {"min": None, "avg": None, "max": None,
                "samples": total, "errors": total,
                "method": None}
    # last method wins for the panel
    last_method = None
    for x in reversed(_HISTORY):
        if x.get("ms") is not None:
            last_method = x.get("method")
            break
    return {"min": min(vals), "avg": sum(vals) / len(vals),
            "max": max(vals), "samples": total, "errors": total - len(vals),
            "method": last_method}


def set_open_ports(ports):
    global _OPEN
    _OPEN = list(ports or [])


def get_open_ports():
    return _OPEN


def status_line():
    from _lib import ui
    h = history()
    if not h:
        return ui.dim(ui.sym_unknown())
    last = h[-1]
    if last["ms"] is None:
        recent = [x["ms"] for x in h[-3:]]
        if all(r is None for r in recent):
            return ui.sym_down()
        return ui.sym_flap()
    method = last.get("method") or "icmp"
    tag = ui.dim(f"({method})") if method == "tcp" else ""
    return ui.sym_up() + "  " + ui.gold(f"{last['ms']:.0f} ms") + " " + tag