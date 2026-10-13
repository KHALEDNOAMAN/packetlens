#!/usr/bin/env python3
"""Streams raw pcap bytes from tcpdump to a PacketLens browser tab. Standard library only."""
import argparse
import secrets
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

parser = argparse.ArgumentParser(description="Local tcpdump bridge for PacketLens")
parser.add_argument("-i", "--interface", required=True, help="the one interface this bridge may capture")
parser.add_argument("-p", "--port", type=int, default=8787)
parser.add_argument("-s", "--snaplen", type=int, default=256, help="bytes kept per packet")
parser.add_argument("-f", "--bpf", default="", help="optional capture filter, e.g. 'not port 22'")
options = parser.parse_args()
token = secrets.token_urlsafe(24)


class StreamHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        supplied = parse_qs(url.query).get("token", [""])[0]
        if url.path != "/stream" or not secrets.compare_digest(supplied, token):
            self.send_error(403)
            return
        command = ["tcpdump", "-i", options.interface, "-U", "-n", "-s", str(options.snaplen), "-w", "-"]
        command += options.bpf.split()
        capture = subprocess.Popen(command, stdout=subprocess.PIPE)
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


server = ThreadingHTTPServer(("127.0.0.1", options.port), StreamHandler)
print(f"Bridge listening on http://127.0.0.1:{options.port} for interface {options.interface}")
print(f"Token (paste into PacketLens): {token}")
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
