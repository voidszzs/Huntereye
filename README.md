# hunter3eye v8

terminal multitool — recon, live monitoring, port scanner, stress groups.
windows 11 + kali. python 3.11+. monochrome CLI.

## run

    py run.py                (windows)
    python3 run.py           (linux)

or double-click `hunter3eye.bat` on windows, or `./hunter3eye.sh` on linux.

## menu

- `[01]` target      — set ipv4 / host / url / lab
- `[02]` dossier     — recon, no traffic
- `[03]` vectors     — stress groups
- `[04]` adaptive    — vectors + live monitor
- `[05]` multipliers — origin hunt
- `[06]` lab         — local targets
- `[07]` all         — fire everything
- `[08]` monitor     — live status view
- `[09]` ping        — continuous ping
- `[10]` ports       — port scanner
- `[11]` settings
- `[12]` help
- `[00]` exit

## target

set once with `[01]`. the status panel on the right shows the target
and live up/down + ping ms, updating every 3 seconds.

## fire gate

read-only features (dossier, monitor, ping, ports) run with no gate.
fire features (vectors, multipliers, all) ask you to retype the target.
if you can't retype it, you don't own it.

## safety

no source-address spoofing. no csam, ever.
