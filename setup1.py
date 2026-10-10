#!/usr/bin/env python3
# worm shadow — kali setup for the linux all-in-one logger
import os
import sys
import shutil
import subprocess
from pathlib import Path

VENV_DIR = Path(".venv")
LOG_DIR = Path("logs")
SHOT_DIR = Path("screenshots")
REQUIRED_APT = ["xdotool", "python3-venv", "python3-full", "python3-dev", "libx11-dev"]
REQUIRED_PY = ["pynput", "mss", "evdev"]


def run(cmd, check=False):
    print(f"[setup] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def have(cmd):
    return shutil.which(cmd) is not None


def pkg_installed(pkg):
    r = subprocess.run(["dpkg", "-s", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def install_system_deps():
    to_install = [p for p in REQUIRED_APT if not pkg_installed(p)]
    if not to_install:
        print("[setup] system deps already installed.")
        return
    print(f"[setup] installing: {', '.join(to_install)}")
    run(["sudo", "apt", "update"], check=False)
    run(["sudo", "apt", "install", "-y"] + to_install, check=False)


def make_venv():
    if VENV_DIR.exists():
        print(f"[setup] venv exists: {VENV_DIR.resolve()}")
        return
    print("[setup] creating venv...")
    run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)


def venv_python():
    return VENV_DIR / "bin" / "python"


def venv_pip():
    return VENV_DIR / "bin" / "pip"


def install_python_deps():
    print("[setup] installing python deps into venv...")
    run([str(venv_pip()), "install", "--upgrade", "pip"], check=False)
    run([str(venv_pip()), "install"] + REQUIRED_PY, check=True)


def make_dirs():
    LOG_DIR.mkdir(exist_ok=True)
    SHOT_DIR.mkdir(exist_ok=True)
    print(f"[setup] logs:        {LOG_DIR.resolve()}")
    print(f"[setup] screenshots: {SHOT_DIR.resolve()}")


def check_session():
    session = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "unknown")
    print(f"[setup] session: {session} | desktop: {desktop}")
    if session == "wayland":
        print("[setup] WARNING: wayland session detected.")
        print("[setup]   - pynput key capture will NOT work (x11-only).")
        print("[setup]   - falling back to /dev/input reader needs sudo.")
        print("[setup]   - xdotool window titles may be empty under wayland.")
        print("[setup]   - for cleanest operation: log out → pick 'Xorg' session.")
    return session


def check_dev_input():
    try:
        from glob import glob
        devs = glob("/dev/input/event*")
        readable = [d for d in devs if os.access(d, os.R_OK)]
        print(f"[setup] /dev/input devices: {len(devs)} total, {len(readable)} readable as user")
        if not readable:
            print("[setup]   → run keylogger with sudo for /dev/input mode")
    except Exception as e:
        print(f"[setup] /dev/input check failed: {e}")


def verify():
    print("[setup] verifying venv imports...")
    ok = True
    for mod in REQUIRED_PY:
        r = subprocess.run(
            [str(venv_python()), "-c", f"import {mod}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        if r.returncode == 0:
            print(f"[setup]   {mod}: ok")
        else:
            print(f"[setup]   {mod}: FAILED — {r.stderr.decode(errors='ignore').strip()}")
            ok = False
    if have("xdotool"):
        print("[setup]   xdotool: ok")
    else:
        print("[setup]   xdotool: MISSING")
        ok = False
    return ok


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
    print("-" * 55)
    if verify():
        print("[setup] all good.")
        if session == "wayland":
            print("[setup] run (needs sudo for key capture):")
            print(f"[setup]   sudo {venv_python().resolve()} keylogger.py")
        else:
            print("[setup] run:")
            print(f"[setup]   {venv_python().resolve()} keylogger.py")
            print(f"[setup] or with sudo for /dev/input mode:")
            print(f"[setup]   sudo {venv_python().resolve()} keylogger.py")
    else:
        print("[setup] something failed — fix above and re-run.")
    print("=" * 55)


if __name__ == "__main__":
    main()
