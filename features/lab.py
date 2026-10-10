import subprocess
import sys
from _lib import ui

ITEMS = [
    ("01", "lab-nginx", "http on 127.0.0.1:8080, slow /search"),
    ("00", "back",      "return"),
]


def _nginx():
    ui.plain("  starting lab-nginx on 127.0.0.1:8080 ...")
    code = (
        "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
        "import time\n"
        "class H(BaseHTTPRequestHandler):\n"
        "    def log_message(self, *a): pass\n"
        "    def do_GET(self):\n"
        "        if self.path.startswith('/search'):\n"
        "            time.sleep(1.2)\n"
        "        self.send_response(200)\n"
        "        self.send_header('Content-Type','text/html')\n"
        "        self.end_headers()\n"
        "        self.wfile.write(b'ok')\n"
        "HTTPServer(('127.0.0.1', 8080), H).serve_forever()\n"
    )
    subprocess.Popen([sys.executable, "-c", code])
    ui.plain(f"  {ui.sym_ok()} lab-nginx up. set target to lab-nginx.")


def run():
    ui.submenu("lab", ITEMS)
    c = ui.ask("select")
    if c == "01":
        _nginx()
