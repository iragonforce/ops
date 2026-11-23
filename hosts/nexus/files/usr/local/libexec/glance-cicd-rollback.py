#!/usr/bin/env python3
"""
Purpose:
    Recover an expired, unconfirmed Glance blue-green deployment.

Input:
    /var/lib/glance-cicd/pending.json
    NPM_EMAIL and NPM_PASSWORD from the protected environment.

Output:
    Restore NPM host 198 to glance:8080 when necessary.
    Record verified recovery under /var/lib/glance-cicd/history/.

Safety:
    Only handles the explicitly configured Glance deployment.
    Never modifies Compose files, images, volumes, or other NPM hosts.
    Failures leave pending state intact for the next timer invocation.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

STATE = Path("/var/lib/glance-cicd")
PENDING = STATE / "pending.json"

HOST_ID = 198
DOMAIN = "glance.blinkwired.com"
BLUE = "glance"
GREEN = "glance-green-cicd"

FIELDS = (
    "domain_names", "forward_scheme", "forward_host",
    "forward_port", "certificate_id", "ssl_forced",
    "hsts_enabled", "hsts_subdomains", "http2_support",
    "block_exploits", "caching_enabled",
    "allow_websocket_upgrade", "access_list_id",
    "advanced_config", "enabled", "locations",
    "trust_forwarded_proto"
)

NODE = r"""
(async () => {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    const req = JSON.parse(Buffer.concat(chunks).toString());

    const response = await fetch(
        "http://127.0.0.1:81/api" + req.path,
        {
            method: req.method,
            headers: {
                "Content-Type": "application/json",
                ...(req.token ? {
                    Authorization: "Bearer " + req.token
                } : {})
            },
            ...(req.body === null ? {} : {
                body: JSON.stringify(req.body)
            }),
            signal: AbortSignal.timeout(12000)
        }
    );

    const data = await response.json().catch(() => null);
    console.log(JSON.stringify({status: response.status, data}));
})().catch(() => {
    console.error("NPM API transport failed");
    process.exit(2);
});
"""


def docker(*args, input_data=None):
    result = subprocess.run(
        ["docker", *args],
        input=input_data,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError("Docker operation failed")
    return result.stdout


def api(method, path, token=None, body=None):
    request = {
        "method": method,
        "path": path,
        "token": token,
        "body": body,
    }

    result = docker(
        "exec", "-i", "nginx-proxy-manager",
        "node", "-e", NODE,
        input_data=json.dumps(request),
    )

    response = json.loads(result)

    if not 200 <= response["status"] < 300:
        raise RuntimeError(f"NPM API HTTP {response['status']}")

    return response["data"]


def authenticate():
    email = os.environ["NPM_EMAIL"]
    password = os.environ["NPM_PASSWORD"]

    response = api("POST", "/tokens", body={
        "identity": email,
        "secret": password,
    })

    return response["token"]


def get_host(token):
    return api("GET", f"/nginx/proxy-hosts/{HOST_ID}", token)


def verify_host(token):
    host = get_host(token)

    if host.get("forward_host") != BLUE:
        raise RuntimeError("API has not restored Blue")

    if int(host.get("forward_port", 0)) != 8080:
        raise RuntimeError("Unexpected forwarding port")

    config = docker(
        "exec", "nginx-proxy-manager",
        "cat", f"/data/nginx/proxy_host/{HOST_ID}.conf",
    )

    match = re.search(
        r'^\s*set \$server\s+"([^"]+)";',
        config,
        re.MULTILINE,
    )

    if not match or match.group(1) != BLUE:
        raise RuntimeError("Generated Nginx upstream mismatch")

    docker("exec", "nginx-proxy-manager", "nginx", "-t")


def verify_blue_health():
    for name in ("glance", "glance-router"):
        status = docker(
            "inspect", "-f",
            "{{.State.Health.Status}}", name,
        ).strip()

        if status != "healthy":
            raise RuntimeError(f"{name} is not healthy")


def restore(token, host):
    payload = {
        key: host[key]
        for key in FIELDS
        if key in host and host[key] is not None
    }
    payload["forward_host"] = BLUE

    api(
        "PUT",
        f"/nginx/proxy-hosts/{HOST_ID}",
        token,
        payload,
    )


def main():
    if not PENDING.exists():
        print("No pending Glance deployment")
        return

    pending = json.loads(PENDING.read_text())

    if (
        pending.get("host_id") != HOST_ID
        or pending.get("domain") != DOMAIN
        or pending.get("previous_upstream") != BLUE
        or pending.get("candidate_upstream") != GREEN
        or pending.get("status") != "pending"
    ):
        raise RuntimeError("Unexpected pending deployment state")

    deployment_id = pending.get("deployment_id", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", deployment_id):
        raise RuntimeError("Invalid deployment identifier")

    deadline = pending["deadline_epoch"]

    if not isinstance(deadline, (int, float)):
        raise RuntimeError("Invalid deadline")

    if time.time() < deadline:
        print("Deployment pending; deadline not reached")
        return

    print("Rollback deadline expired", flush=True)

    verify_blue_health()
    token = authenticate()
    host = get_host(token)

    if host.get("domain_names") != [DOMAIN]:
        raise RuntimeError("Unexpected proxy host domains")

    if int(host.get("forward_port", 0)) != 8080:
        raise RuntimeError("Unexpected forwarding port")

    current = host.get("forward_host")

    if current == GREEN:
        print("Restoring Blue", flush=True)
        restore(token, host)
    elif current != BLUE:
        raise RuntimeError("Unexpected upstream; refusing to overwrite")

    verify_host(token)
    print("Blue restored and verified", flush=True)

    history = STATE / "history"
    history.mkdir(mode=0o700, exist_ok=True)

    record = dict(pending)
    record["status"] = "rolled_back"
    record["completed_epoch"] = time.time()

    target = history / f"{deployment_id}.json"
    if target.exists():
        # A previous invocation may have committed history but
        # crashed before deleting pending.json. Resume safely.
        previous = json.loads(target.read_text())

        identity = (
            "deployment_id",
            "host_id",
            "domain",
            "previous_upstream",
            "candidate_upstream",
            "deadline_epoch",
        )

        if (
            previous.get("status") != "rolled_back"
            or any(
                previous.get(key) != pending.get(key)
                for key in identity
            )
        ):
            raise RuntimeError("Conflicting rollback history")

        PENDING.unlink()
        print("Previous rollback finalized")
        return

    temporary = history / f".{deployment_id}.tmp"
    try:
        with temporary.open("x") as output:
            json.dump(record, output, indent=2)
            output.flush()
            os.fsync(output.fileno())

        os.chmod(temporary, 0o600)
        os.replace(temporary, target)
        PENDING.unlink()
    finally:
        temporary.unlink(missing_ok=True)

    print("Recovery record saved")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ROLLBACK FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
