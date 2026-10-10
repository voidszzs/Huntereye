# debug toggles.
from pathlib import Path

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_ROOT = Path(__file__).resolve().parent.parent
_FILE = _ROOT / "debug" / "debug.yaml"

_T = {}


def _load():
    global _T
    _T = {"global": False}
    if not _HAS_YAML or not _FILE.is_file():
        return
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        for k, v in data.items():
            _T[str(k)] = bool(v)
    except Exception:
        pass


def reload():
    _load()


def dbg(area, msg):
    if not _T:
        _load()
    if not (_T.get("global") or _T.get(area, False)):
        return
    from _lib import ui
    ui.plain(ui.dim(f"  [debug] {area} — {msg}"))


def all_toggles():
    if not _T:
        _load()
    return dict(_T)


def set_toggle(area, value):
    if not _T:
        _load()
    _T[area] = bool(value)
    save()


def save():
    if not _HAS_YAML:
        return False
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_FILE, "w", encoding="utf-8", newline="\n") as f:
            f.write("# hunter3eye debug toggles\n\n")
            for k in sorted(_T.keys()):
                f.write(f"{k}: {str(_T[k]).lower()}\n")
        return True
    except Exception:
        return False


_load()
