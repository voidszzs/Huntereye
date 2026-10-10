from _lib import ui


def run():
    lines = ["",
             "  terminal multitool for recon, live monitoring, ports, stress.",
             "  windows 11 + kali. python 3.11+. monochrome CLI.",
             "",
             "  [01]  set target       ipv4 / host / url / lab",
             "  [02]  dossier          recon, no traffic",
             "  [03]  vectors          stress groups",
             "  [04]  adaptive         vectors + live monitor",
             "  [05]  multipliers      origin hunt",
             "  [06]  lab              local targets",
             "  [07]  all              fire everything",
             "  [08]  monitor          live view",
             "  [09]  ping             continuous ping",
             "  [10]  ports            port scanner",
             "  [11]  settings",
             "  [12]  help",
             "  [00]  exit",
             "",
             "  the gate",
             "    dossier/monitor/ping/ports run without asking.",
             "    vectors/multipliers/all require you to retype the target.",
             "",
             "  safety",
             "    no source-address spoofing anywhere.",
             "    no csam, ever.",
             ""]
    ui.box("help", lines)
