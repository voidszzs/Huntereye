from _lib.debug import dbg


def _all():
    from _lib.ring1 import l3l4, l4state, tls, http, game, dns
    return [
        l3l4.UdpFlood, l3l4.IcmpFlood,
        l4state.HalfOpenFlood,
        tls.ClientHelloFlood,
        http.CacheBustFlood, http.Slowloris,
        game.McStatusFlood, game.McLoginStartFlood,
        game.RaknetPingFlood, game.SourceA2SFlood,
        dns.RandomSubdomainFlood,
    ]


GROUPS = {
    "l7":   ["http-cachebust", "http-slowloris"],
    "l4":   ["half-open-tcp"],
    "l3":   ["udp-flood", "icmp-flood"],
    "tls":  ["tls-clienthello"],
    "dns":  ["dns-random-sub"],
    "game": ["mc-status", "mc-login-start", "mc-bedrock-ping", "source-a2s"],
}


def select(d, args):
    by_name = {c.name: c for c in _all()}
    want = args.vectors
    if want == "auto":
        wanted = []
        if d.get("class") == "website":
            wanted += ["http-cachebust", "http-slowloris"]
        if d.get("class") == "game-server":
            wanted += ["mc-status", "mc-login-start"]
    elif want == "all":
        wanted = list(by_name.keys())
    elif want in GROUPS:
        wanted = GROUPS[want]
    else:
        wanted = [w.strip() for w in want.split(",")]

    out = []
    for name in wanted:
        cls = by_name.get(name)
        if not cls:
            continue
        v = cls()
        if not v.safe and not args.allow_reckless:
            dbg("vectors_selector", f"skip reckless {v.name}")
            continue
        if not v.can_run(d):
            dbg("vectors_selector", f"skip {v.name} needs {v.needs}")
            continue
        out.append(v)
    return out
