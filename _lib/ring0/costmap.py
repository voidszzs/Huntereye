# ring 0.4 — costmap.
import shutil
import subprocess
from urllib.parse import urljoin
from _lib.debug import dbg

PATHS = ["/", "/about", "/contact", "/search", "/api", "/api/login",
         "/api/search", "/login", "/register", "/export", "/report",
         "/download", "/image", "/render", "/graphql", "/admin"]


def _time_url(url, timeout=10):
    if not shutil.which("curl"):
        return None
    null_dev = "NUL" if __import__("os").name == "nt" else "/dev/null"
    try:
        r = subprocess.run(
            ["curl", "-sS", "-o", null_dev, "-w", "%{http_code} %{time_total}",
             "--max-time", str(timeout), "-k", url],
            capture_output=True, text=True, timeout=timeout + 2, shell=False)
        parts = r.stdout.strip().split()
        if len(parts) == 2:
            return {"code": parts[0], "time": float(parts[1])}
    except Exception:
        pass
    return None


def build_costmap(base_url):
    results = []
    for p in PATHS:
        url = urljoin(base_url.rstrip("/") + "/", p.lstrip("/"))
        r = _time_url(url)
        if r and r["code"] not in ("404", "000"):
            results.append({"url": url, "code": r["code"], "time": r["time"]})
            dbg("recon_costmap", f"{url} {r['time']:.3f}s {r['code']}")
    results.sort(key=lambda x: x["time"], reverse=True)
    return results[:10]
