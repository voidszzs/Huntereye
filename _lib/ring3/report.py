# _lib/ring3/report.py
# ring 3.3 — end-of-run report writer.
#
# collects everything the run produced: dossier, vectors fired, monitor
# timeline, retune decisions, timings, target state flips, and writes a
# plain-text report next to the session log.
#
# pure python, no external deps. cross-platform (windows + kali).

import json
import os
import statistics
import time
from pathlib import Path

from _lib.debug import dbg


# ═══════════════════════════════════════════════════════════════════════════
# where reports go
# ═══════════════════════════════════════════════════════════════════════════
_ROOT = Path(__file__).resolve().parent.parent.parent
_OUT = _ROOT / "out"


def _ensure_out():
    try:
        _OUT.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


def _safe_name(s):
    keep = []
    for ch in s or "target":
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        else:
            keep.append("_")
    out = "".join(keep).strip("_")
    return out[:60] or "target"


# ═══════════════════════════════════════════════════════════════════════════
# a small accumulator callers can use
# ═══════════════════════════════════════════════════════════════════════════
class ReportData:
    def __init__(self, target_name, mode, vectors, rate, duration):
        self.target_name = target_name
        self.mode = mode
        self.vectors = vectors
        self.rate = rate
        self.duration = duration
        self.started = time.time()
        self.ended = None
        self.dossier = {}
        self.plan_names = []
        self.vector_results = []      # list of dicts {name, sent, errors, seconds}
        self.monitor_summary = {}
        self.monitor_history = []
        self.retune_timeline = []
        self.state_changes = []       # list of (ts, from, to)
        self.extra = {}
        self.errors = []              # list of (ts, where, message)

    def finish(self):
        self.ended = time.time()

    def add_vector_result(self, name, sent, errors, seconds):
        self.vector_results.append({
            "name": name, "sent": sent, "errors": errors, "seconds": seconds,
        })

    def add_state_change(self, frm, to):
        self.state_changes.append((time.time(), frm, to))

    def add_error(self, where, message):
        self.errors.append((time.time(), where, message))

    def elapsed(self):
        return (self.ended or time.time()) - self.started

    def to_dict(self):
        return {
            "target": self.target_name,
            "mode": self.mode,
            "vectors_arg": self.vectors,
            "rate": self.rate,
            "duration": self.duration,
            "started": self.started,
            "ended": self.ended,
            "elapsed": self.elapsed(),
            "dossier": self.dossier,
            "plan": self.plan_names,
            "vector_results": self.vector_results,
            "monitor": self.monitor_summary,
            "retune": self.retune_timeline,
            "state_changes": [
                {"t": t, "from": f, "to": x} for t, f, x in self.state_changes
            ],
            "extra": self.extra,
            "errors": [
                {"t": t, "where": w, "message": m} for t, w, m in self.errors
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════
# write the human-readable report
# ═══════════════════════════════════════════════════════════════════════════
def save_report(dossier, monitor, args, out_dir=None):
    """
    legacy entry point used by features/vectors.py and features/adaptive.py.
    builds a ReportData from whatever it's given and writes it.
    """
    out_dir = out_dir or _OUT
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    tname = dossier["target"].get("name") or dossier["target"].get("host") or "target"
    name = _safe_name(tname)
    ts = int(time.time())
    path = Path(out_dir) / f"{name}-{int(time.time())}.txt"

    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write("hunter3eye report\n")
            f.write("=" * 72 + "\n")
            f.write(f"generated : {time.ctime()}\n")
            f.write(f"target    : {tname}\n")
            f.write(f"mode      : {getattr(args, 'mode', '?')}\n")
            f.write(f"vectors   : {getattr(args, 'vectors', '?')}\n")
            f.write(f"rate      : {getattr(args, 'rate', '?')}\n")
            f.write(f"duration  : {getattr(args, 'duration', '?')}\n")
            f.write("\n")

            f.write("target:\n")
            for k, v in dossier.get("target", {}).items():
                f.write(f"  {k:<10} {v}\n")
            f.write("\n")

            f.write("recon:\n")
            for k in ("ipv4", "ipv6", "class", "ports", "deps"):
                f.write(f"  {k:<10} {dossier.get(k)}\n")
            cm = dossier.get("costmap") or []
            if cm:
                f.write("  costmap (slowest first):\n")
                for c in cm[:10]:
                    f.write(f"    {c['time']:>7.3f}s  {c['code']}  {c['url']}\n")
            f.write("\n")

            if monitor is not None:
                try:
                    s = monitor.summary()
                except Exception:
                    s = {}
                f.write("monitor:\n")
                for k in ("baseline", "baseline_method", "avg", "min", "max",
                          "p95", "samples", "errors", "degraded"):
                    f.write(f"  {k:<16} {s.get(k)}\n")
                f.write("\n")

            f.write("end of report.\n")
    except Exception as e:
        dbg("adaptive_report", f"write failed: {e!r}")
        return None

    dbg("adaptive_report", f"wrote {path}")
    return str(path)


# ═══════════════════════════════════════════════════════════════════════════
# json companion (for the report reader in another tool)
# ═══════════════════════════════════════════════════════════════════════════
def save_report_json(data, out_dir=None):
    out_dir = out_dir or _OUT
    try:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    name = _safe_name(data.target_name)
    path = Path(out_dir) / f"{name}-{int(time.time())}.json"
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data.to_dict(), f, indent=2, default=str)
    except Exception as e:
        dbg("adaptive_report", f"json write failed: {e!r}")
        return None
    return str(path)


# ═══════════════════════════════════════════════════════════════════════════
# verdict — one-line summary of what the run actually did
# ═══════════════════════════════════════════════════════════════════════════
def verdict_text(monitor, data=None):
    if monitor is None:
        return "no monitor data"
    try:
        s = monitor.summary()
    except Exception:
        return "no monitor data"
    baseline = s.get("baseline")
    avg = s.get("avg")
    errors = s.get("errors", 0)
    total = s.get("samples", 0)
    degraded = s.get("degraded")

    if not baseline or not avg:
        return "no baseline — target unreachable during run"

    ratio = avg / baseline if baseline else 1.0
    delta_pct = (ratio - 1.0) * 100.0

    if degraded:
        return f"target degraded: latency +{delta_pct:.0f}% vs baseline, {errors}/{total} failed probes"
    if delta_pct > 30:
        return f"target slowing: latency +{delta_pct:.0f}% vs baseline"
    if delta_pct > 10:
        return f"target slightly elevated: latency +{delta_pct:.0f}% vs baseline"
    return f"target stable: latency {delta_pct:+.0f}% vs baseline"


# ═══════════════════════════════════════════════════════════════════════════
# timing helpers used by the loop
# ═══════════════════════════════════════════════════════════════════════════
def now_str():
    return time.strftime("%H:%M:%S")


def short_ts(t):
    return time.strftime("%H:%M:%S", time.localtime(t))


# ═══════════════════════════════════════════════════════════════════════════
# optional: list past reports
# ═══════════════════════════════════════════════════════════════════════════
def list_reports(limit=20, out_dir=None):
    out_dir = Path(out_dir or _OUT)
    if not out_dir.is_dir():
        return []
    files = sorted(
        [p for p in out_dir.iterdir() if p.suffix in (".txt", ".json")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return [str(p) for p in files[:limit]]


# ═══════════════════════════════════════════════════════════════════════════
# extra: write a "session" line, so out/session.log stays useful
# ═══════════════════════════════════════════════════════════════════════════
def append_session(line, out_dir=None):
    out_dir = Path(out_dir or _OUT)
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "session.log", "a", encoding="utf-8", newline="\n") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}  {line}\n")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
# helper: compact dump for the terminal right after a run ends
# ═══════════════════════════════════════════════════════════════════════════
def print_run_summary(ui, monitor, data=None):
    lines = [""]
    if data is not None:
        lines.append(f"  mode       {data.mode}")
        lines.append(f"  elapsed    {data.elapsed():.1f}s")
        lines.append(f"  vectors    {len(data.vector_results)}")
        sent = sum(v["sent"] for v in data.vector_results)
        errs = sum(v["errors"] for v in data.vector_results)
        lines.append(f"  sent       {sent}")
        lines.append(f"  errors     {errs}")
    if monitor is not None:
        try:
            s = monitor.summary()
        except Exception:
            s = {}
        lines.append(f"  baseline   {s.get('baseline') and round(s.get('baseline'), 1)} ms")
        lines.append(f"  avg        {s.get('avg') and round(s.get('avg'), 1)} ms")
        lines.append(f"  p95        {s.get('p95') and round(s.get('p95'), 1)} ms")
        lines.append(f"  samples    {s.get('samples')}")
        lines.append(f"  failed     {s.get('errors')}")
        lines.append("")
        lines.append("  " + verdict_text(monitor, data))
    lines.append("")
    ui.box("run summary", lines)