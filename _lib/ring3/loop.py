import threading
import time
from _lib.status import ping_ms


def adaptive_run(target, dossier, plan, args):
    if not plan:
        return 0
    host = dossier.get("ipv4") or dossier.get("ipv6") or target.get("host")
    stop = threading.Event()
    samples = []
    errors = [0]

    def sampler():
        while not stop.is_set():
            ms = ping_ms(host)
            if ms is None:
                errors[0] += 1
            else:
                samples.append(ms)
            time.sleep(2)

    threading.Thread(target=sampler, daemon=True).start()

    threads = []
    for v in plan:
        th = threading.Thread(target=_safe, args=(v, dossier, args), daemon=True)
        th.start()
        threads.append(th)

    last = time.time()
    while time.time() < last + args.duration:
        time.sleep(1)

    stop.set()
    for th in threads:
        th.join(timeout=2)
    return 0


def _safe(v, d, args):
    try:
        v.run(d, args)
    except Exception:
        pass
