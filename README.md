
markdown
# hunter3eye

terminal multitool for recon, live monitoring, port scanning and stress testing.

runs on **windows 11** and **kali linux** (and most debian/ubuntu variants).
100% python. monochrome terminal UI. no browser. no daemon.

---

## what it does

| menu | feature     | what it does                                                    |
|------|-------------|-----------------------------------------------------------------|
| 01   | target      | set the ip / host / url / lab the tool works on                 |
| 02   | dossier     | recon: ports, services, tls, deps, costmap                      |
| 03   | vectors     | stress groups (l3 / l4 / tls / http / dns / game / app / auth / ipv6) |
| 04   | adaptive    | vectors + live latency monitor + retune                         |
| 05   | multipliers | origin hunt, rate-limit bypass, waf bypass helpers              |
| 06   | lab         | spin up local test targets (nginx, http2, ws, dns, mc)          |
| 07   | all         | fire every applicable vector at once                            |
| 08   | monitor     | live up/down panel with ping stats                              |
| 09   | ping        | continuous ping with bar graph                                  |
| 10   | ports       | port scanner (quick 1-1024 or full 1-65535)                     |
| 11   | iplookup    | geo / isp / asn / reverse dns of the target's ip                |
| 12   | settings    | edit settings.yaml + debug toggles from inside                  |
| 13   | help        | usage + safety                                                  |
| 99   | ask         | built-in help desk (type a question)                            |
| 00   | exit        | leave                                                           |

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
- **this tool is for research and lab use.**

---

## install

### 1. get python ready

**windows 11**

1. download python 3.11 or newer: https://www.python.org/downloads/windows/
2. on the first screen of the installer, **check both boxes**:
   - ☑ Add python.exe to PATH
   - ☑ Install py launcher for all users
3. finish install. **reboot** (windows needs a full logout/login for PATH to update).
4. verify in cmd:

   ```cmd
   py --version
must print Python 3.11.x or newer.

kali linux

bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
                    nmap curl whois tcpdump dnsmasq git
verify:

bash
python3 --version
must print Python 3.11.x or newer.

what each system package gives you:

package	used for
nmap	fast port scans (dossier, ports)
curl	http probes, costmap timing
whois	asn / org lookups in iplookup
tcpdump	ipv6 ra sniff in dossier
dnsmasq	lab-dns target
git	cloning the repo
2. get the tool
pick one way.

a. clone from github — works on windows and linux

bash
git clone https://github.com/YOURNAME/hunter3eye.git
cd hunter3eye
on windows, run the same command in cmd. put it somewhere simple like C:\hunter3eye.

b. download the zip from github releases → extract.

windows: right-click → extract all → C:\hunter3eye\

linux: unzip hunter3eye.zip -d ~/ → cd ~/hunter3eye

c. copy the folder from a usb stick or another machine.

3. install python dependencies
windows

cmd
cd C:\hunter3eye
py -m pip install -r requirements.txt
kali linux

kali 2024+ blocks plain pip install outside a venv. two options:

option a — user install with the guard bypassed:

bash
cd ~/hunter3eye
pip3 install --user --break-system-packages -r requirements.txt
option b — use a venv (cleaner, keeps deps separate):

bash
cd ~/hunter3eye
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
if you choose the venv, run source .venv/bin/activate every time before python3 run.py.

4. run it
windows

cmd
cd C:\hunter3eye
py run.py
or double-click hunter3eye.bat.

kali linux

bash
cd ~/hunter3eye
python3 run.py
or:

bash
chmod +x hunter3eye.sh
./hunter3eye.sh
raw-packet vectors on linux need root. if you want icmp-flood, frag-udp, ipv6 ndp/ra, or anything using scapy's send() to work:

bash
sudo python3 run.py
the http / tcp / tls / dns / game vectors work fine as normal user.

5. optional — install as a system command
windows — make it available from any cmd

copy:

text
C:\hunter3eye\hunter3eye.bat
to:

text
C:\Windows\System32\hunter3eye.bat
now hunter3eye works from any folder.

(if you can't write to System32, put the bat in any folder already on your PATH. run echo %PATH% to see the folders.)

kali — install with setup.py

the repo ships a setup.py. run:

bash
cd ~/hunter3eye
python3 setup.py install
this copies the app to ~/.local/lib/hunter3eye/, writes a launcher at ~/.local/bin/hunter3eye, and installs pip deps. no sudo needed.

then add ~/.local/bin to your PATH (one time):

bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
from now on, hunter3eye works from any folder.

updates
if you cloned with git
windows

cmd
cd C:\hunter3eye
git pull
py -m pip install -r requirements.txt
kali linux

bash
cd ~/hunter3eye
git pull
pip3 install --user --break-system-packages -r requirements.txt
if you installed with setup.py install on linux, also:

bash
python3 setup.py install
to refresh the installed copy.

if you downloaded a zip
extract the new zip somewhere else (don't overwrite the old one yet).

copy your personal files from the old folder into the new one:

settings.yaml

debug/debug.yaml

.target (if you want to keep your saved target)

run from the new folder. delete the old one when you're sure it works.

check your version
the version is on the banner when the tool starts:

text
version 8.0.0  •  windows
or in settings.yaml, under general.version.

if you cloned with git, also:

bash
git log --oneline -5
shows the last five commits.

uninstall
windows
delete the folder C:\hunter3eye\

if you created C:\Windows\System32\hunter3eye.bat, delete it too

if you made a venv, delete .venv inside the folder (already gone if you deleted the folder)

kali linux
if you installed with setup.py install:

bash
cd ~/hunter3eye
python3 setup.py uninstall
that removes:

~/.local/bin/hunter3eye (launcher)

~/.local/lib/hunter3eye/ (app)

~/.local/lib/hunter3eye-8.0.0.dist-info/ (metadata)

then remove the source:

bash
cd ~
rm -rf hunter3eye
if you used a venv, rm -rf ~/hunter3eye/.venv removes it.

removing the pip deps — don't do this blindly. pyyaml and httpx are used by a lot of things on a normal kali system. only uninstall if you know nothing else needs them:

bash
pip3 uninstall --user -y pyyaml scapy aiohttp httpx dnspython h2
troubleshooting
"python is not recognized as a command" (windows)
python isn't on PATH. reinstall python and check "Add python.exe to PATH" on the first screen. reboot.

"ModuleNotFoundError: No module named 'yaml'"
dependencies weren't installed. run:

windows: py -m pip install -r requirements.txt

linux: pip3 install --user --break-system-packages -r requirements.txt

"externally-managed-environment" on kali
kali 2024+ blocks pip install outside a venv. use:

bash
pip3 install --user --break-system-packages -r requirements.txt
or use a venv:

bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
"ImportError: cannot import name 'clear' from '_lib.ui'"
you have an old copy of _lib/ui.py. pull the latest:

bash
git pull
or re-extract the zip.

unicode box characters look like ? or garbage
your terminal isn't in utf-8.

windows:

cmd
chcp 65001
or use windows terminal (default on win11) instead of plain cmd — always utf-8.

linux:

bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
python3 run.py
if box characters still look wrong, the tool auto-falls-back to ascii boxes (+---+).

"Permission denied" on icmp / frag / ipv6 vectors
those need raw socket access. on linux:

bash
sudo python3 run.py
on windows, run cmd as administrator.

nmap hangs or takes forever
full scan -p- on a slow target can take 20+ minutes. use quick scan (1-1024) first.

"nmap: command not found"
linux: sudo apt install nmap
windows: download from https://nmap.org/download.html and check "add nmap to PATH" during install.

"whois: command not found"
linux: sudo apt install whois

target shows ○ down but the site is obviously up
that site blocks icmp. the tool falls back to tcp connect on port 443 automatically. if it still shows down, either the site is down or it blocks both icmp and tcp from your location.

try ping from a normal terminal to confirm.

hunter3eye command not found after setup.py install (linux)
~/.local/bin isn't on PATH. fix:

bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
or run it directly once: ~/.local/bin/hunter3eye.

reports aren't being written
reports go to out/ inside the tool folder. if you ran setup.py install, that's ~/.local/lib/hunter3eye/out/.

if the folder doesn't exist, the tool creates it on first run.

reset everything to defaults
delete these files — they'll be recreated on next start:

.target — clears the saved target

out/ — clears reports + session log

debug/debug.yaml — resets debug toggles

settings.yaml — regenerated with defaults if you delete it

folder layout
text
hunter3eye/
├── run.py                ← entry point
├── setup.py              ← installer for linux (setup.py install)
├── settings.yaml         ← user settings
├── requirements.txt      ← python deps
├── hunter3eye.bat        ← windows launcher
├── hunter3eye.sh         ← linux launcher
├── README.md             ← this file
├── _lib/
│   ├── ui.py             ← every screen draws through here
│   ├── platform.py       ← cross-platform helpers
│   ├── settings.py       ← settings loader
│   ├── debug.py          ← debug toggles
│   ├── config.py         ← lab targets
│   ├── status.py         ← live ping daemon
│   ├── security.py       ← the one wall + retype gate
│   ├── ring0/            ← recon: host, services, deps, costmap, ipv6
│   ├── ring1/            ← vectors: l3l4, l4state, tls, http, dns, game, app, auth, ipv6, selector
│   ├── ring2/            ← multipliers: origin_hunt, ratelimit, amplify, waf_bypass, distribute
│   └── ring3/            ← adaptive: measure, retune, report, loop
├── features/
│   ├── target.py         ← [01]
│   ├── recon.py          ← [02] dossier
│   ├── vectors.py        ← [03]
│   ├── adaptive.py       ← [04]
│   ├── multipliers.py    ← [05]
│   ├── lab.py            ← [06]
│   ├── monitor.py        ← [08]
│   ├── ping.py           ← [09]
│   ├── ports.py          ← [10]
│   ├── iplookup.py       ← [11]
│   ├── settings_menu.py  ← [12]
│   ├── help.py           ← [13]
│   └── ask.py            ← [99]
├── debug/
│   ├── debug.yaml        ← per-area debug toggles
│   └── README.md
└── out/                  ← reports + session.log + lab logs
how to change things
I want to...	edit this file	change this
ping every 1 second	settings.yaml	status.interval: 1
hide the banner	settings.yaml	general.show_banner: false
rename a menu item	run.py	the MENU list
add a new menu item	run.py + new file in features/	add row + write run()
change the melt colors	_lib/ui.py	_MELT_COLORS = [...]
widen the boxes	_lib/ui.py	every width = 82
see debug output	debug/debug.yaml	flip an area to true
add a new vector	_lib/ring1/ new file	subclass Vector, add to selector.py
change what a feature does	features/<feature>.py	the run() function
rule of thumb: numbers and on/off → settings.yaml. debug → debug/debug.yaml. look and feel → _lib/ui.py. menu → run.py. feature behavior → the features/ file for that feature.

dependencies
required (tool won't start without them):

pyyaml — settings + debug config

optional (they degrade gracefully if missing):

scapy — raw-packet vectors (icmp, frag, ipv6, syn flood, etc.)

aiohttp — http vectors (cachebust, slowloris, rps, xml bomb)

httpx — some http helper paths

dnspython — dns vectors and dns lookup

h2 — http/2 vectors (rapid reset)

system tools (optional):

nmap — fast port scans

curl — http timing + probes

whois — asn / org lookups

tcpdump — ipv6 ra sniff

dnsmasq — lab-dns

docker — lab-mc

install all on kali in one line:

bash
sudo apt install nmap curl whois tcpdump dnsmasq
pip3 install --user --break-system-packages pyyaml scapy aiohttp httpx dnspython h2
on windows:

cmd
py -m pip install pyyaml scapy aiohttp httpx dnspython h2
license
MIT. see LICENSE if present.

changelog
8.0.0
full ring0 / ring1 / ring2 / ring3 engine

adaptive loop with retune

live status panel on the main menu

iplookup ([11]) with geo, isp, asn, reverse dns

ask ([99]) built-in help desk

lab with nginx, http2, ws, dns, mc

cross-platform utf-8 safe ping

no spoofing anywhere

one wall: no csam

text

---

## was du jetzt machst

**1.** öffne dein notepad mit der readme (oder neue datei).

**2.** **ctrl+a** → **delete** → paste **das ganze markdown oben**.

**3.** speichern:

- speicherort: `C:\hunter3eye_build\hunter3eye\`
- dateiname: `README.md`
- dateityp: **Alle Dateien (\*.\*)**
- encoding: **UTF-8**

**4.** push auf github:

```cmd
cd /d C:\hunter3eye_build\hunter3eye
git add README.md
git commit -m "docs: full readme for windows + linux"
git push
oder GitHub Desktop: readme update → Commit to main → Push origin.
