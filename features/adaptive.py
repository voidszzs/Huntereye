from _lib import ui


def run():
    ui.plain("  adaptive = recon + vectors + live monitoring.")
    ui.plain("  forwarding to vectors.")
    from features.vectors import run as v
    v()
