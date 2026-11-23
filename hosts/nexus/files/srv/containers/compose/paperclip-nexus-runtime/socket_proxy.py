#!/usr/bin/env python3
"""Docker API proxy with exact read and existing Glance start allowlists."""
import http.client
import hashlib
import json
import pathlib
import re
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
sys.path.insert(0, "/app/vendor")
import yaml

SOCKET = "/var/run/docker.sock"
CONTAINERS = {"glance", "glance-router", "nginx-proxy-manager"}
NETWORKS = {"docker-vlan", "proxy-backend", "nexus-egress"}


class UnixConnection(http.client.HTTPConnection):
    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(5)
        self.sock.connect(SOCKET)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_GET(self):
        if self.path in {"/compose/glance", "/compose/glance-router"}:
            name = self.path.rsplit("/", 1)[1]
            try:
                raw = pathlib.Path("/compose/monitoring.yaml").read_bytes()
                service = yaml.safe_load(raw)["services"][name]
                keys = ("image", "container_name", "restart", "depends_on", "volumes", "networks", "ports")
                body = json.dumps({"name": name, "source": "/srv/containers/compose/monitoring/compose.yaml",
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "service": {k: service[k] for k in keys if k in service}}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_error(502)
            return
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        container = re.fullmatch(r"/containers/([a-zA-Z0-9_.-]+)/json", self.path)
        network = re.fullmatch(r"/networks/([a-zA-Z0-9_.-]+)", self.path)
        allowed = bool(container and container.group(1) in CONTAINERS)
        allowed |= bool(network and network.group(1) in NETWORKS)
        if not allowed:
            self.send_error(404)
            return
        try:
            upstream = UnixConnection("localhost", timeout=5)
            upstream.request("GET", self.path)
            response = upstream.getresponse()
            body = response.read(1_000_001)
            upstream.close()
            if len(body) > 1_000_000:
                self.send_error(502)
                return
            self.send_response(response.status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (OSError, http.client.HTTPException):
            self.send_error(502)

    def do_POST(self):
        if self.path not in {"/containers/glance/start", "/containers/glance-router/start"}:
            self.send_error(405)
            return
        try:
            upstream = UnixConnection("localhost", timeout=5)
            upstream.request("POST", self.path, body=b"", headers={"Content-Length": "0"})
            response = upstream.getresponse()
            body = response.read(4096)
            upstream.close()
            self.send_response(response.status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (OSError, http.client.HTTPException):
            self.send_error(502)

    def do_PUT(self):
        self.send_error(405)

    do_PATCH = do_PUT
    do_DELETE = do_PUT


ThreadingHTTPServer(("127.0.0.1", 2375), Handler).serve_forever()
