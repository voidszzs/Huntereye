# [09] ping — loops as fast as the network answers. ctrl+c to stop.
import statistics
import sys
import time

from _lib import ui
from _lib.status import current_target, ping_ms


def _summary_line(samples, lost, start):
    if not samples:
        return "  no replies yet   lost " + str(lost)
    elapsed = max(0.001, time.time() - start)
    sent = len(samples) + lost
    loss = (lost / sent * 100.0) if sent else 0.0
    try:
        p95 = statistics.quantiles(samples, n=20)[-1]
    except Exception:
        p95 = max(samples)
    return (f"  min {min(samples):.1f}   avg {sum(samples)/len(samples):.1f}   "
            f"max {max(samples):.1f}   p95 {p95:.1f}   "
            f"loss {loss:.1f}%   sent {sent}   rate {sent/elapsed:.1f}/s")


def run():
    target = current_target()
    if not target:
        ui.plain("  no target set. use [01] first.")
        return

    ui.plain("")
    ui.plain("  " + ui.red("PING") + "  " + ui.gold(target))
    ui.plain("  " + ui.grey("ctrl+c to stop"))
    ui.plain("")

    samples = []
    lost = 0
    start = time.time()
    last_summary = time.time()
    seq = 0

    try:
        while True:
            seq += 1
            ms = ping_ms(target)
            t = time.strftime("%H:%M:%S")

            if ms is None:
                lost += 1
                line = "  " + ui.grey(f"{t}  #{seq:<5}") + "  " + ui.red("timeout")
            else:
                samples.append(ms)
                bar_len = min(int(ms / 5) + 1, 40)
                bar_char = "█" if ui._u() else "#"
                bar = bar_char * bar_len
                line = ("  " + ui.grey(f"{t}  #{seq:<5}") + "  " +
                        ui.gold(f"{ms:>7.1f} ms") + "  " +
                        ui._fg(203) + bar + ui.RESET)

            # \r moves cursor to start of line, then rewrite. clean, no scroll.
            sys.stdout.write("\r" + line.ljust(120))
            sys.stdout.flush()

            # every ~1 second, print a newline and the summary line, then continue
            now = time.time()
            if now - last_summary >= 1.0:
                sys.stdout.write("\n")
                sys.stdout.write(_summary_line(samples, lost, start).ljust(120))
                sys.stdout.write("\r")
                # rebuild the ping line: print a fresh line above
                sys.stdout.write("\033[1A")     # up one line
                sys.stdout.write("\033[2K")     # clear that line
                sys.stdout.write("\n")
                sys.stdout.write(_summary_line(samples, lost, start).ljust(120))
                sys.stdout.flush()
                last_summary = now

    except KeyboardInterrupt:
        pass

    print()
    print()
    ui.plain("  " + ui.sym_ok() + " ping stopped.")
    ui.plain(_summary_line(samples, lost, start))
    print()