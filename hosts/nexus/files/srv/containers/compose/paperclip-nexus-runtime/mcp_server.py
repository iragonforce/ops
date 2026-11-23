#!/usr/bin/env python3
"""Bounded, read-only Nexus runtime facts for Paperclip."""
import collections
import datetime
import hmac
import json
import pathlib
import re
import socket
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOKEN = pathlib.Path("/run/secrets/mcp-token").read_text().strip()
PROXY = "http://127.0.0.1:2375"
CONF_DIR = pathlib.Path("/npm/proxy_host")
LOG_DIR = pathlib.Path("/npm/logs")
CONTAINERS = ("nginx-proxy-manager", "glance", "glance-router")
NETWORKS = ("docker-vlan", "proxy-backend", "nexus-egress")


def tool(name, description, properties, required=()):
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": properties,
                            "required": list(required), "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False,
                            "openWorldHint": False}}


TOOLS = [
    tool("compose_service", "Inspect current maintained Compose source metadata and selected service settings; excludes environment, secrets and commands.",
         {"name": {"type": "string", "enum": ["glance", "glance-router"]}}, ["name"]),
    tool("mount_inspection", "Inspect bind source paths, container targets and read-only flags for approved containers; no file contents.",
         {"name": {"type": "string", "enum": list(CONTAINERS)}}, ["name"]),
    tool("container_state", "Read selected Docker container state, ports and network attachments; no environment, mounts, exec or raw inspect.",
         {"name": {"type": "string", "enum": list(CONTAINERS)}}, ["name"]),
    tool("network_state", "Read selected Docker network driver, subnet and scoped container membership.",
         {"name": {"type": "string", "enum": list(NETWORKS)}}, ["name"]),
    tool("npm_upstream", "Read parsed Nginx Proxy Manager upstream scheme, host and port for a matching domain; no raw config.",
         {"match": {"type": "string", "pattern": "^[a-zA-Z0-9.-]{1,80}$"}}, ["match"]),
    tool("proxy_errors", "Read bounded Nginx Proxy Manager error categories and recent metadata for a matching domain; no raw access log.",
         {"match": {"type": "string", "pattern": "^[a-zA-Z0-9.-]{1,80}$"}}, ["match"]),
    tool("listener_probe", "Probe a fixed Nexus proxy-backend listener with a two-second TCP timeout.",
         {"target": {"type": "string", "enum": ["glance", "nginx-proxy-manager"]},
          "port": {"type": "integer", "minimum": 1, "maximum": 65535}}, ["target", "port"]),
]
TOOLS.append({"name": "restore_glance", "description": "Start existing Glance and optional router containers after checking maintained Compose and bind sources. Does not recreate containers, change settings or pull images. Inspect first; report outcome before retrying.",
              "inputSchema": {"type": "object", "properties": {"include_router": {"type": "boolean", "default": True}}, "additionalProperties": False},
              "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}})


def compose_service(args):
    name = args.get("name")
    if name not in ("glance", "glance-router"):
        raise ValueError("Service outside approved scope")
    return docker_get("/compose/" + name)


def mount_inspection(args):
    name = args.get("name")
    if name not in CONTAINERS:
        raise ValueError("Container outside approved scope")
    data = docker_get("/containers/" + name + "/json")
    if not data:
        return {"name": name, "exists": False}
    labels = data.get("Config", {}).get("Labels", {})
    return {"name": name, "composeSource": labels.get("com.docker.compose.project.config_files"),
            "composeService": labels.get("com.docker.compose.service"),
            "mounts": [{"type": m.get("Type"), "source": m.get("Source"), "target": m.get("Destination"), "writable": m.get("RW")} for m in data.get("Mounts", [])]}


def restore_glance(args):
    names = ["glance", "glance-router"] if args.get("include_router", True) else ["glance"]
    expected = {"/srv/containers/data/glance/config": pathlib.Path("/bind-check/glance-config"),
                "/srv/containers/builds/glance-router": pathlib.Path("/bind-check/glance-router")}
    # Preflight the whole requested stack before dispatching the first start.
    for name in names:
        service = compose_service({"name": name})["service"]
        data = docker_get("/containers/" + name + "/json")
        if not data or data.get("Config", {}).get("Image") != service.get("image"):
            raise ValueError("Existing image differs from maintained Compose; inspect before restoration")
        labels = data.get("Config", {}).get("Labels", {})
        if labels.get("com.docker.compose.service") != name:
            raise ValueError("Compose identity mismatch")
        for mount in data.get("Mounts", []):
            if mount.get("Type") == "bind":
                source = expected.get(mount.get("Source"))
                if source is None or not source.is_dir():
                    raise ValueError("Approved bind source missing or outside scope")
    results = []
    for name in names:
        data = docker_get("/containers/" + name + "/json")
        if data.get("State", {}).get("Running"):
            results.append({"name": name, "action": "already_running"})
            continue
        req = urllib.request.Request(PROXY + "/containers/" + name + "/start", data=b"", method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                results.append({"name": name, "action": "start_requested", "httpStatus": response.status})
        except (OSError, urllib.error.HTTPError):
            return {"results": results, "stoppedAt": name, "outcome": "inspect_current_state_before_retry"}
    return {"results": results, "states": [container_state({"name": name}) for name in names]}


def docker_get(path):
    try:
        with urllib.request.urlopen(PROXY + path, timeout=7) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise RuntimeError("Docker read proxy unavailable") from None


def clean_error(value):
    text = str(value or "")[:300]
    text = re.sub(r"(?i)(token|password|secret|authorization)\s*[=:]\s*\S+", r"\1=[redacted]", text)
    return text


def container_state(args):
    name = args.get("name")
    if name not in CONTAINERS:
        raise ValueError("Container outside approved scope")
    data = docker_get("/containers/" + name + "/json")
    if data is None:
        return {"name": name, "exists": False}
    state = data.get("State") or {}
    config = data.get("Config") or {}
    network = data.get("NetworkSettings") or {}
    host = data.get("HostConfig") or {}
    attachments = {}
    for key, value in (network.get("Networks") or {}).items():
        if key in NETWORKS:
            attachments[key] = {"currentIp": value.get("IPAddress"),
                                "configuredIp": (value.get("IPAMConfig") or {}).get("IPv4Address")}
    return {"name": name, "exists": True, "image": config.get("Image"),
            "status": state.get("Status"), "running": state.get("Running"),
            "health": (state.get("Health") or {}).get("Status"),
            "exitCode": state.get("ExitCode"), "oomKilled": state.get("OOMKilled"),
            "stateError": clean_error(state.get("Error")),
            "startedAt": state.get("StartedAt"), "finishedAt": state.get("FinishedAt"),
            "restartCount": data.get("RestartCount"),
            "exposedPorts": sorted((config.get("ExposedPorts") or {}).keys()),
            "publishedPorts": network.get("Ports") or {},
            "networkMode": host.get("NetworkMode"), "networks": attachments}


def network_state(args):
    name = args.get("name")
    if name not in NETWORKS:
        raise ValueError("Network outside approved scope")
    data = docker_get("/networks/" + name)
    if data is None:
        return {"name": name, "exists": False}
    members = []
    for item in (data.get("Containers") or {}).values():
        if item.get("Name") in CONTAINERS:
            members.append({"name": item.get("Name"), "ipv4": item.get("IPv4Address")})
    ipam = data.get("IPAM") or {}
    ranges = [{"subnet": x.get("Subnet"), "gateway": x.get("Gateway")}
              for x in (ipam.get("Config") or [])[:4]]
    return {"name": name, "exists": True, "driver": data.get("Driver"),
            "internal": data.get("Internal"), "ranges": ranges,
            "approvedMembers": sorted(members, key=lambda x: x["name"] or "")}


def proxy_hosts(match):
    if not isinstance(match, str) or not re.fullmatch(r"[a-zA-Z0-9.-]{1,80}", match):
        raise ValueError("Use a short domain or service match")
    found = []
    for path in sorted(CONF_DIR.glob("[0-9]*.conf")):
        text = path.read_text(errors="replace")
        server = re.search(r"^\s*server_name\s+([^;]+);", text, re.M)
        names = server.group(1).split() if server else []
        if not any(match.lower() in name.lower() for name in names):
            continue
        def setting(key):
            m = re.search(r"^\s*set\s+\$" + key + r"\s+\"?([^\";]+)\"?;", text, re.M)
            return m.group(1).strip() if m else None
        found.append({"proxyHostId": path.stem, "domains": names[:8],
                      "scheme": setting("forward_scheme"), "upstreamHost": setting("server"),
                      "upstreamPort": setting("port"),
                      "configModifiedAt": datetime.datetime.fromtimestamp(path.stat().st_mtime,
                          datetime.timezone.utc).isoformat()})
    return found[:10]


def npm_upstream(args):
    return {"matches": proxy_hosts(args.get("match"))}


def proxy_errors(args):
    hosts = proxy_hosts(args.get("match"))
    counts = collections.Counter()
    recent = []
    patterns = (("connect_refused", "connect() failed"),
                ("upstream_timeout", "upstream timed out"),
                ("no_live_upstream", "no live upstreams"),
                ("tls_handshake", "SSL_do_handshake"),
                ("host_unresolved", "host not found in upstream"))
    for host in hosts:
        path = LOG_DIR / ("proxy-host-" + host["proxyHostId"] + "_error.log")
        if not path.is_file():
            continue
        # Only the current log, last 512 KiB. Never return raw request lines.
        with path.open("rb") as stream:
            stream.seek(max(0, path.stat().st_size - 524288))
            lines = stream.read().decode(errors="replace").splitlines()[-1500:]
        for line in lines:
            category = next((key for key, marker in patterns if marker in line), None)
            if not category:
                continue
            counts[category] += 1
            stamp = re.match(r"^(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", line)
            recent.append({"proxyHostId": host["proxyHostId"],
                           "timestamp": stamp.group(1) if stamp else None,
                           "category": category})
    return {"matches": len(hosts), "categories": dict(counts), "recent": recent[-12:]}


def listener_probe(args):
    target, port = args.get("target"), args.get("port")
    allowed = {"glance": {8080}, "nginx-proxy-manager": {80, 443}}
    if target not in allowed or port not in allowed[target]:
        raise ValueError("Listener outside approved scope")
    try:
        with socket.create_connection((target, port), timeout=2):
            return {"target": target, "port": port, "tcpConnect": "ok"}
    except socket.gaierror:
        return {"target": target, "port": port, "tcpConnect": "name_unresolved"}
    except (OSError, TimeoutError):
        return {"target": target, "port": port, "tcpConnect": "failed"}


CALLS = {"container_state": container_state, "network_state": network_state,
         "npm_upstream": npm_upstream, "proxy_errors": proxy_errors,
         "listener_probe": listener_probe, "compose_service": compose_service,
         "mount_inspection": mount_inspection, "restore_glance": restore_glance}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(self.command, self.path, fmt % args, flush=True)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_error(405)

    def do_POST(self):
        if self.path != "/mcp":
            self.send_error(404)
            return
        if not hmac.compare_digest(self.headers.get("Authorization", ""), "Bearer " + TOKEN):
            self.send_error(401)
            return
        request = {}
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size < 1 or size > 32768:
                raise ValueError("Request size outside bounds")
            request = json.loads(self.rfile.read(size))
            method = request.get("method")
            params = request.get("params") or {}
            if "id" not in request:
                self.send_response(202)
                self.end_headers()
                return
            if method == "initialize":
                result = {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                          "capabilities": {"tools": {}},
                          "serverInfo": {"name": "nexus-runtime-readonly", "version": "2026-10-27"}}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": TOOLS}
            elif method == "tools/call":
                name = params.get("name")
                if name not in CALLS:
                    raise ValueError("Unknown tool")
                value = CALLS[name](params.get("arguments") or {})
                result = {"content": [{"type": "text", "text": json.dumps(value)}],
                          "isError": False}
            else:
                raise ValueError("Unsupported method")
            response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
        except ValueError as error:
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                        "result": {"content": [{"type": "text", "text": json.dumps({"error": str(error)[:120]})}],
                                   "isError": True}}
        except Exception:
            response = {"jsonrpc": "2.0", "id": request.get("id") if isinstance(request, dict) else None,
                        "error": {"code": -32603, "message": "Nexus runtime read failed"}}
        body = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


ThreadingHTTPServer(("0.0.0.0", 8769), Handler).serve_forever()
