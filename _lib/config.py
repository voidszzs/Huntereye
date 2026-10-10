LAB = {
    "lab-nginx":  {"host": "127.0.0.1", "port": 8080,  "type": "http"},
    "lab-mc":     {"host": "127.0.0.1", "port": 25565, "type": "minecraft"},
    "lab-fivem":  {"host": "127.0.0.1", "port": 30120, "type": "fivem"},
    "lab-router": {"host": "192.168.99.1", "port": 80, "type": "router"},
    "lab-dns":    {"host": "127.0.0.1", "port": 5353,  "type": "dns"},
}


def resolve_target(arg):
    if arg in LAB:
        t = dict(LAB[arg])
        t["lab"] = True
        t["name"] = arg
        return t
    t = {"name": arg, "lab": False, "type": "unknown", "port": None}
    if arg.startswith(("http://", "https://")):
        t["type"] = "http"
        t["url"] = arg
    elif arg.count(":") == 1 and not arg.startswith("["):
        h, p = arg.rsplit(":", 1)
        t["host"] = h
        try:
            t["port"] = int(p)
        except ValueError:
            t["host"] = arg
    else:
        t["host"] = arg
    return t
