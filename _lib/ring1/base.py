class Vector:
    name = "unnamed"
    safe = False
    needs = []

    def can_run(self, d):
        for need in self.needs:
            if need == "ipv4" and not d.get("ipv4"):
                return False
            if need == "http" and not (d.get("target", {}).get("url") or
                                       any(s.get("port") in (80, 443, 8080, 8443)
                                           for s in d.get("services", []))):
                return False
            if need.startswith("game-"):
                pm = {"game-mc": 25565, "game-mcbe": 19132,
                      "game-fivem": 30120, "game-source": 27015}
                if not any(s.get("port") == pm.get(need)
                           for s in d.get("services", [])):
                    return False
        return True

    def run(self, d, args):
        raise NotImplementedError
