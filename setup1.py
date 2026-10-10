#!/usr/bin/env python3
# worm shadow — setup for the linux all-in-one logger
import os
import sys
import shutil
import subprocess
from pathlib import Path

REQUIRED_PY = ["pynput", "mss"]
REQUIRED_APT = ["xdotool"]
LOG_DIR = Path("logs")
SHOT_DIR = Path("screenshots")


def run(cmd, check=False):
    print(f"[setup] $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check)


def have(cmd):
    return shutil.which(cmd) is not None


def install_python_deps():
    print("[setup] installing python deps...")
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    run([sys.executable, "-m", "pip", "install"] + REQUIRED_PY, check=False)


def install_system_deps():
    if have("xdotool"):
        print("[setup] xdotool already installed.")
        return
    if not have("apt"):
        print("[setup] not a debian/ubuntu system — install xdotool manually.")
        return
    print("[setup] installing xdotool via apt...")
    run(["sudo", "apt", "update"])
    run(["sudo", "apt", "install", "-y", "xdotool"])


def make_dirs():
    LOG_DIR.mkdir(exist_ok=True)
    SHOT_DIR.mkdir(exist_ok=True)
    print(f"[setup] logs dir:        {LOG_DIR.resolve()}")
    print(f"[setup] screenshots dir: {SHOT_DIR.resolve()}")


def check_session():
    session = os.environ.get("XDG_SESSION_TYPE", "unknown").lower()
    print(f"[setup] session type: {session}")
    if session == "wayland":
        print("[setup] WARNING: wayland detected. global key capture and xdotool")
        print("[setup] will most likely fail. use an x11 session for full function.")


def verify():
    print("[setup] verifying imports...")
    ok = True
    for mod in REQUIRED_PY:
        try:
            __import__(mod)
            print(f"[setup]   {mod}: ok")
        except Exception as e:
            print(f"[setup]   {mod}: FAILED ({e})")
            ok = False
    if have("xdotool"):
        print("[setup]   xdotool: ok")
    else:
        print("[setup]   xdotool: MISSING")
        ok = False
    return ok


def main():
    print("=" * 50)
    print("  worm shadow — linux logger setup")
    print("=" * 50)
    check_session()
    install_system_deps()
    install_python_deps()
    make_dirs()
    print("-" * 50)
    if verify():
        print("[setup] all good. run: python3 logger.py")
    else:
        print("[setup] something is missing — fix the items above and re-run.")
    print("=" * 50)


if __name__ == "__main__":
    main()
