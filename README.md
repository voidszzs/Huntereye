# hunter3eye

terminal multitool for recon, live monitoring, port scanning and stress testing.

runs on **windows 11** and **kali linux** (and most debian/ubuntu variants).  
100% python. monochrome terminal UI. no browser. no daemon.

---

## what it does

| menu | feature | what it does |
|------|---------|--------------|
| 01 | target      | set the ip / host / url / lab the tool works on |
| 02 | dossier     | recon: ports, services, tls, deps, costmap |
| 03 | vectors     | stress groups (l3 / l4 / tls / http / dns / game / app / auth / ipv6) |
| 04 | adaptive    | vectors + live latency monitor + retune |
| 05 | multipliers | origin hunt, rate-limit bypass, waf bypass helpers |
| 06 | lab         | spin up local test targets (nginx, http2, ws, dns, mc) |
| 07 | all         | fire every applicable vector at once |
| 08 | monitor     | live up/down panel with ping stats |
| 09 | ping        | continuous ping with bar graph |
| 10 | ports       | port scanner (quick 1-1024 or full 1-65535) |
| 11 | iplookup    | geo / isp / asn / reverse dns of the target's ip |
| 12 | settings    | edit settings.yaml + debug toggles from inside |
| 13 | help        | usage + safety |
| 99 | ask         | built-in help desk (type a question) |
| 00 | exit        | leave |

---

## safety

read this before anything else.

- **no spoofing anywhere in this tool.** every packet uses the real
  outbound address of the machine you're on. the classic amplification
  vectors (memcached, ntp, dns reflector) are not implemented because
  they need spoofed source, which vpns and isps drop anyway.
- **no csam, ever, in any form.**
- **fire features (03, 05, 07) require you to retype the target** before
  they run. if you can't retype it, you don't own it.
- **read-only features (02, 08, 09, 10, 11) run without the gate.**
- **run against targets you own.** home router, your own laptop, a vm,
  the built-in lab. firing at anything else is a crime in most countries.
- **this tool is for research and lab use.** don't be the reason it gets
  taken down.

---

## install — windows 11

### 1. install python

download **python 3.11 or newer** from https://www.python.org/downloads/windows/

during install, on the first screen, **check both boxes**:
- ☑ Add python.exe to PATH
- ☑ Install py launcher for all users (recommended)

then reboot (windows needs a full logout/login for PATH to update).

verify in cmd:

```cmd
py --version
