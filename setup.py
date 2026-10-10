#!/usr/bin/env python3
# setup.py — hunter3eye installer for linux (and windows if you want).
#
# usage on kali / linux:
#   cd ~/hunter3eye
#   python3 setup.py install         # installs into ~/.local
#   python3 setup.py develop         # editable install (dev mode)
#   python3 setup.py user            # force user-local install
#   python3 setup.py clean           # remove build artifacts
#   python3 setup.py uninstall       # remove the installed command + package
#   python3 setup.py run             # just launch it (no install)
#
# after install, from anywhere:
#   hunter3eye
#
# the script installs:
#   ~/.local/bin/hunter3eye              <- launcher
#   ~/.local/lib/hunter3eye/             <- the app tree (or site-packages)
#
# no build backend needed. no pip wheel. pure python.

import os
import shutil
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
PACKAGE_NAME = "hunter3eye"
VERSION = "8.0.0"


# ═══════════════════════════════════════════════════════════════════════════
# small helpers
# ═══════════════════════════════════════════════════════════════════════════
def _say(msg, ok=True):
    tag = "\033[32m[+]\033[0m" if ok else "\033[31m[!]\033[0m"
    print(f"{tag} {msg}", flush=True)


def _die(msg):
    _say(msg, ok=False)
    sys.exit(1)


def _is_windows():
    return os.name == "nt"


def _user_base():
    # where pip --user installs. normally ~/.local on linux,
    # %APPDATA%\Python on windows.
    if _is_windows():
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Python"
        return Path.home() / "AppData" / "Roaming" / "Python"
    return Path.home() / ".local"


def _bin_dir():
    return _user_base() / "bin" if not _is_windows() else _user_base() / "Scripts"


def _lib_dir():
    return _user_base() / "lib" / PACKAGE_NAME


def _dist_info():
    return _user_base() / "lib" / f"{PACKAGE_NAME}-{VERSION}.dist-info"


def _python():
    return sys.executable or ("python" if _is_windows() else "python3")


# ═══════════════════════════════════════════════════════════════════════════
# what gets copied where
# ═══════════════════════════════════════════════════════════════════════════
COPY_DIRS = [
    "_lib",
    "features",
    "debug",
]
COPY_FILES = [
    "run.py",
    "settings.yaml",
    "requirements.txt",
    "README.md",
]


# ═══════════════════════════════════════════════════════════════════════════
# build a launcher script that points back at the installed package
# ═══════════════════════════════════════════════════════════════════════════
LAUNCHER_POSIX = """#!/usr/bin/env python3
import sys
from pathlib import Path
# the app was installed to ~/.local/lib/hunter3eye
pkg = Path.home() / ".local" / "lib" / "hunter3eye"
if not pkg.is_dir():
    print("hunter3eye not found in ~/.local/lib/hunter3eye")
    sys.exit(1)
sys.path.insert(0, str(pkg))
os.chdir(str(pkg))  # so out/, .target, debug/ live inside the package
import run
sys.exit(run.main())
"""

LAUNCHER_WIN = """# hunter3eye launcher (windows)
import os, sys
from pathlib import Path
appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
pkg = Path(appdata) / "Python" / "lib" / "hunter3eye"
if not pkg.is_dir():
    print("hunter3eye not found in", pkg)
    sys.exit(1)
sys.path.insert(0, str(pkg))
os.chdir(str(pkg))
import run
sys.exit(run.main())
"""

LAUNCHER_POSIX = LAUNCHER_POSIX.replace("os.chdir", "import os; os.chdir")  # guard


# ═══════════════════════════════════════════════════════════════════════════
# copy the tree into ~/.local/lib/hunter3eye/
# ═══════════════════════════════════════════════════════════════════════════
def _copy_tree(dest):
    if dest.exists():
        _say(f"removing old {dest}")
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    # directories
    for d in COPY_DIRS:
        src = HERE / d
        if src.is_dir():
            shutil.copytree(src, dest / d,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            _say(f"copied {d}/")

    # files
    for f in COPY_FILES:
        src = HERE / f
        if src.is_file():
            shutil.copy2(src, dest / f)
            _say(f"copied {f}")

    # setup.py itself, for reference
    if (HERE / "setup.py").is_file():
        shutil.copy2(HERE / "setup.py", dest / "setup.py")

    # also copy the .bat / .sh launchers, if present
    for extra in ("hunter3eye.sh", "hunter3eye.bat"):
        if (HERE / extra).is_file():
            shutil.copy2(HERE / extra, dest / extra)

    # make sure out/ exists
    (dest / "out").mkdir(exist_ok=True)
    _say(f"created {dest / 'out'}")


# ═══════════════════════════════════════════════════════════════════════════
# write the launcher
# ═══════════════════════════════════════════════════════════════════════════
def _write_launcher():
    bindir = _bin_dir()
    bindir.mkdir(parents=True, exist_ok=True)
    if _is_windows():
        launcher = bindir / f"{PACKAGE_NAME}.py"
        launcher.write_text(LAUNCHER_WIN, encoding="utf-8")
        _say(f"wrote {launcher}")
        # also write a .bat wrapper so windows finds it on PATH
        bat = bindir / f"{PACKAGE_NAME}.bat"
        bat.write_text(
            f'@echo off\r\n"{_python()}" "{launcher}" %*\r\n',
            encoding="utf-8",
        )
        _say(f"wrote {bat}")
    else:
        launcher = bindir / PACKAGE_NAME
        launcher.write_text(LAUNCHER_POSIX, encoding="utf-8")
        os.chmod(launcher, 0o755)
        _say(f"wrote {launcher}")


# ═══════════════════════════════════════════════════════════════════════════
# write a minimal .dist-info so pip and importlib can find it
# ═══════════════════════════════════════════════════════════════════════════
def _write_metadata():
    meta = _dist_info()
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "METADATA").write_text(
        f"Metadata-Version: 2.1\n"
        f"Name: {PACKAGE_NAME}\n"
        f"Version: {VERSION}\n"
        f"Summary: terminal multitool\n"
        f"Requires-Python: >=3.11\n",
        encoding="utf-8",
    )
    (meta / "INSTALLER").write_text("setup.py\n", encoding="utf-8")
    (meta / "RECORD").write_text("", encoding="utf-8")
    _say(f"wrote {meta}")


# ═══════════════════════════════════════════════════════════════════════════
# commands
# ═══════════════════════════════════════════════════════════════════════════
def cmd_install(develop=False):
    _say(f"installing hunter3eye {VERSION} to {_user_base()}")
    dest = _lib_dir()
    _copy_tree(dest)
    _write_launcher()
    _write_metadata()

    # make sure pip deps are installed too
    _say("installing python deps ...")
    req = HERE / "requirements.txt"
    if req.is_file():
        py = _python()
        r = subprocess.run(
            [py, "-m", "pip", "install", "--user", "-q", "-r", str(req)],
            shell=False,
        )
        if r.returncode != 0:
            _say("pip install had a warning — you may need sudo or --break-system-packages")
            _say("try: pip3 install --user --break-system-packages -r requirements.txt", ok=False)

    # warn if ~/.local/bin not on path
    bindir = _bin_dir()
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    if str(bindir) not in path_dirs and not _is_windows():
        _say("add this to your ~/.bashrc / ~/.zshrc so 'hunter3eye' works from anywhere:", ok=False)
        _say(f'  export PATH="$HOME/.local/bin:$PATH"')

    _say("")
    _say("done.")
    _say("run it with:  hunter3eye")
    _say(f"or:           {_python()} {dest / 'run.py'}")


def cmd_uninstall():
    _say("uninstalling ...")
    for p in (_lib_dir(), _dist_info()):
        if p.exists():
            shutil.rmtree(p)
            _say(f"removed {p}")
        else:
            _say(f"not found: {p}")
    launcher = _bin_dir() / (f"{PACKAGE_NAME}.bat" if _is_windows() else PACKAGE_NAME)
    if launcher.exists():
        launcher.unlink()
        _say(f"removed {launcher}")
    launcher_py = _bin_dir() / f"{PACKAGE_NAME}.py"
    if launcher_py.exists():
        launcher_py.unlink()
        _say(f"removed {launcher_py}")
    _say("done.")


def cmd_clean():
    for junk in ("build", "dist", f"{PACKAGE_NAME}.egg-info", "__pycache__"):
        p = HERE / junk
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            _say(f"removed {junk}")
    _say("clean.")


def cmd_run():
    sys.path.insert(0, str(HERE))
    import run as runner
    sys.exit(runner.main())


def cmd_user():
    # convenience alias for install
    cmd_install(develop=False)


# ═══════════════════════════════════════════════════════════════════════════
# entry
# ═══════════════════════════════════════════════════════════════════════════
USAGE = f"""hunter3eye setup.py {VERSION}

commands:
  install      copy the app into ~/.local/lib/hunter3eye and add the
               'hunter3eye' command to ~/.local/bin
  user         same as install
  develop      same as install (kept for muscle memory)
  uninstall    remove the launcher and the installed package
  clean        remove build artifacts from this folder
  run          just run the tool from this folder (no install)

example:
  python3 setup.py install
  hunter3eye
"""


def main():
    if len(sys.argv) < 2:
        print(USAGE)
        return 0
    cmd = sys.argv[1].lower()

    if cmd in ("install", "user"):
        cmd_install()
    elif cmd in ("develop", "dev"):
        cmd_install(develop=True)
    elif cmd == "uninstall":
        cmd_uninstall()
    elif cmd == "clean":
        cmd_clean()
    elif cmd == "run":
        cmd_run()
    elif cmd in ("-h", "--help", "help"):
        print(USAGE)
    else:
        print(f"unknown command: {cmd}")
        print(USAGE)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
