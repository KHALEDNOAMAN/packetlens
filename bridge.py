#!/usr/bin/env python3
"""PacketLens bridge: serves the UI and streams tcpdump output to it. Standard library only."""
import argparse
import os
import secrets
import shutil
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

UI_FILE = Path(__file__).resolve().with_name("index.html")


def default_interface():
    try:
        words = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=3).stdout.split()
        return words[words.index("dev") + 1]
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        return "any"


parser = argparse.ArgumentParser(description="PacketLens bridge: serves the UI and streams tcpdump to it")
parser.add_argument("-i", "--interface", default=None, help="interface to capture (default: the default-route interface)")
parser.add_argument("--host", default="127.0.0.1", help="bind address; use 0.0.0.0 to reach the bridge from a VM host")
parser.add_argument("-p", "--port", type=int, default=8787)
parser.add_argument("-s", "--snaplen", type=int, default=256, help="bytes kept per packet")
parser.add_argument("-f", "--bpf", default="", help="optional capture filter, e.g. 'not port 22'")
parser.add_argument("--list", action="store_true", help="list capture interfaces and exit")
options = parser.parse_args()

if not shutil.which("tcpdump"):
    sys.exit("tcpdump not found. Install it with: sudo apt install tcpdump")
if options.list:
    sys.exit(subprocess.run(["tcpdump", "-D"]).returncode)

interface = options.interface or default_interface()
token = secrets.token_urlsafe(24)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, body, content_type="text/plain; charset=utf-8"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in ("/", "/index.html"):
            if UI_FILE.exists():
                self.reply(200, UI_FILE.read_bytes(), "text/html; charset=utf-8")
            else:
                self.reply(404, "index.html must sit next to bridge.py")
        elif url.path == "/ping":
            self.reply(200, '{"bridge":"packetlens","interface":"%s"}' % interface, "application/json")
        elif url.path == "/stream":
            supplied = parse_qs(url.query).get("token", [""])[0]
            if secrets.compare_digest(supplied.encode(), token.encode()):
                self.stream()
            else:
                self.reply(403, "Bad token")
        else:
            self.reply(404, "Not found")

    def stream(self):
        command = ["tcpdump", "-i", interface, "-U", "-n", "-s", str(options.snaplen), "-w", "-"] + options.bpf.split()
        try:
            capture = subprocess.Popen(command, stdout=subprocess.PIPE)
        except OSError as error:
            self.reply(500, f"Could not start tcpdump: {error}")
            return
        time.sleep(0.5)
        if capture.poll() not in (None, 0):
            self.reply(500, f"tcpdump exited with code {capture.returncode}. Usually this means missing privileges (use sudo) or a wrong interface name (run with --list). Details are in the bridge terminal.")
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            while chunk := capture.stdout.read1(65536):
                self.wfile.write(chunk)
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            capture.terminate()


try:
    server = ThreadingHTTPServer((options.host, options.port), Handler)
except OSError as error:
    sys.exit(f"Cannot listen on {options.host}:{options.port}: {error}. Try another port with -p.")

if os.name == "posix" and os.geteuid() != 0:
    print("Warning: not running as root. If capture fails, use sudo or grant tcpdump capabilities (see README).")
shown_host = "127.0.0.1" if options.host in ("127.0.0.1", "localhost") else "<this-machine-ip>"
print(f"PacketLens bridge ready. Capturing interface: {interface}")
print(f"Open: http://{shown_host}:{options.port}/#token={token}")
if options.host not in ("127.0.0.1", "localhost"):
    print("Listening beyond localhost: the token protects the stream, but traffic is unencrypted HTTP. Use only on trusted networks.")
try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nStopped.")
