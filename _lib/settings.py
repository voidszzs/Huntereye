# settings loader.
from pathlib import Path

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

_ROOT = Path(__file__).resolve().parent.parent
_FILE = _ROOT / "settings.yaml"

DEFAULTS = {
    "general": {"version": "8.0.0", "show_banner": True},
    "paths": {"output_dir": "out"},
    "network": {"default_rate": 50, "default_duration": 30, "default_timeout": 5},
    "status": {"enabled": True, "interval": 3, "log_changes": True},
    "recon": {"services": True, "deps": True, "costmap": True},
    "vectors": {"allow_reckless": False},
    "safety": {"require_retype_on_fire": True},
    "ui": {"box_width": 82},
}

_DATA = {}


def _deep(d):
    out = {}
    for k, v in d.items():
        out[k] = _deep(v) if isinstance(v, dict) else v
    return out


def _load():
    global _DATA
    _DATA = _deep(DEFAULTS)
    if not _HAS_YAML or not _FILE.is_file():
        return
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
        for section, vals in loaded.items():
            if isinstance(vals, dict) and section in _DATA:
                for k, v in vals.items():
                    _DATA[section][k] = v
            else:
                _DATA[section] = vals
    except Exception:
        pass


def s(path, default=None):
    node = _DATA
    for p in path.split("."):
        if isinstance(node, dict) and p in node:
            node = node[p]
        else:
            return default
    return node


def set_value(path, value):
    parts = path.split(".")
    node = _DATA
    for p in parts[:-1]:
        if p not in node or not isinstance(node[p], dict):
            node[p] = {}
        node = node[p]
    node[parts[-1]] = value
    save()


def all_values():
    return _deep(_DATA)


def save():
    if not _HAS_YAML:
        return False
    try:
        with open(_FILE, "w", encoding="utf-8", newline="\n") as f:
            yaml.safe_dump(_DATA, f, default_flow_style=False, sort_keys=False)
        return True
    except Exception:
        return False


def reset():
    global _DATA
    _DATA = _deep(DEFAULTS)
    save()


_load()
