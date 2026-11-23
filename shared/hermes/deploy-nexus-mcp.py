#!/usr/bin/env python3
"""Deploy Git-managed Nexus Hermes MCP definitions.

Requires Python 3 and PyYAML. Only the top-level mcp_servers
section is replaced; unrelated configuration is preserved.
"""

import argparse
import os
from pathlib import Path
import re
import stat
import sys
import tempfile

import yaml


DEFAULT_SOURCE = Path(__file__).resolve().with_name("nexus-mcp.yaml")
DEFAULT_LIVE = Path("/srv/containers/data/hermes/data/config.yaml")


def load(text, label):
    obj = yaml.safe_load(text)
    if not isinstance(obj, dict):
        raise ValueError(f"{label}: expected YAML mapping")
    return obj


def section(text, label):
    lines = text.splitlines(keepends=True)

    starts = [
        i for i, line in enumerate(lines)
        if re.fullmatch(
            r"mcp_servers:\s*(?:#.*)?",
            line.rstrip("\r\n"),
        )
    ]

    if len(starts) != 1:
        raise ValueError(f"{label}: expected one MCP section")

    start = starts[0]
    end = next(
        (
            i for i in range(start + 1, len(lines))
            if re.match(r"^[A-Za-z_][\w-]*:\s*", lines[i])
        ),
        len(lines),
    )

    return lines, start, end


def atomic_write(path, text, original, metadata):
    temporary = None

    try:
        fd, temporary = tempfile.mkstemp(
            prefix=".hermes-mcp-",
            dir=path.parent,
        )

        with os.fdopen(fd, "w") as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())

        os.chown(temporary, metadata.st_uid, metadata.st_gid)
        os.chmod(temporary, stat.S_IMODE(metadata.st_mode))

        if (
            path.read_text() != original
            or path.stat().st_mtime_ns != metadata.st_mtime_ns
        ):
            raise RuntimeError("Live configuration changed during deployment")

        os.replace(temporary, path)
        temporary = None

    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(
        description="Check or deploy Git-managed Nexus Hermes MCP definitions."
    )
    parser.add_argument("mode", choices=("check", "apply"))
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--live", type=Path, default=DEFAULT_LIVE)
    args = parser.parse_args()

    source_text = args.source.read_text()
    live_text = args.live.read_text()

    source = load(source_text, "Git source")
    live = load(live_text, "Live configuration")

    if set(source) != {"mcp_servers"}:
        raise ValueError("Git source must contain only mcp_servers")

    definitions = source["mcp_servers"]

    if not isinstance(definitions, dict) or not definitions:
        raise ValueError("Empty or invalid MCP definitions")

    source_lines, source_start, source_end = section(
        source_text, "Git source"
    )
    live_lines, live_start, live_end = section(
        live_text, "Live configuration"
    )

    print(f"Git MCP definitions: {len(definitions)}")
    print(f"Live MCP definitions: {len(live['mcp_servers'])}")

    if definitions == live["mcp_servers"]:
        print("Status: IN SYNC")
        print("Live file modified: NO")
        return 0

    if args.mode == "check":
        print("Status: DRIFT DETECTED")
        print("Live file modified: NO")
        return 2

    replacement = "".join(
        source_lines[source_start:source_end]
    )

    if not replacement.endswith("\n"):
        replacement += "\n"

    candidate = (
        "".join(live_lines[:live_start])
        + replacement
        + "".join(live_lines[live_end:])
    )

    parsed = load(candidate, "Deployment candidate")
    expected = dict(live)
    expected["mcp_servers"] = definitions

    if parsed != expected:
        raise ValueError("Deployment would alter unrelated settings")

    metadata = args.live.stat()

    atomic_write(
        args.live,
        candidate,
        live_text,
        metadata,
    )

    verified = load(args.live.read_text(), "Deployed configuration")

    if verified != expected:
        raise RuntimeError("Post-deployment verification failed")

    print("Status: APPLIED")
    print("Unrelated configuration: PRESERVED")
    print("Ownership and permissions: PRESERVED")
    print("Gateway restart: NOT PERFORMED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, yaml.YAMLError) as exc:
        print(f"Deployment failed: {type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
