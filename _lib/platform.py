# cross-platform helpers.
import os
import shutil
import subprocess
import sys

IS_WINDOWS = os.name == "nt"


def is_windows():
    return IS_WINDOWS


def is_linux():
    return sys.platform.startswith("linux")


def enable_ansi():
    if IS_WINDOWS:
        try:
            os.system("")
        except Exception:
            pass


def binary_exists(name):
    return shutil.which(name) is not None


def hard_clear():
    # full-screen ansi clear + cursor home. works on win11 terminal,
    # powershell 7, windows conhost with vt enabled, and every modern linux.
    try:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    except Exception:
        os.system("cls" if IS_WINDOWS else "clear")


def clear():
    hard_clear()


def center_window(width=120, height=40):
    if not IS_WINDOWS:
        return
    try:
        import ctypes
        from ctypes import wintypes
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        hwnd = kernel32.GetConsoleWindow()
        if not hwnd:
            return
        user32.ShowWindow(hwnd, 9)
        try:
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0001 | 0x0002)
        except Exception:
            pass
        cell_w, cell_h = 8, 16
        px_w = width * cell_w
        px_h = height * cell_h
        screen_w = user32.GetSystemMetrics(0)
        screen_h = user32.GetSystemMetrics(1)
        x = max(0, (screen_w - px_w) // 2)
        y = max(0, (screen_h - px_h) // 2)
        user32.MoveWindow(hwnd, x, y, px_w, px_h, True)
        try:
            kernel32.SetConsoleScreenBufferSize(
                kernel32.GetStdHandle(-11),
                wintypes._COORD(width, height))
        except Exception:
            pass
    except Exception:
        pass


def _safe_run(args, timeout=5):
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
    except Exception:
        return None


def ping_args_1(host):
    if IS_WINDOWS:
        return ["ping", "-n", "1", "-w", "2000", host]
    return ["ping", "-c", "1", "-W", "2", host]


def ping_once(host, timeout=3):
    import re
    r = _safe_run(ping_args_1(host), timeout=timeout)
    if r is None:
        return None
    out = r.stdout or ""
    m = re.search(r"time[=<]\s*([\d.]+)", out, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def terminal_supports_unicode():
    try:
        enc = (sys.stdout.encoding or "").lower()
        return "utf" in enc
    except Exception:
        return False