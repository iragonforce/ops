#!/usr/bin/env python3
"""Loopback-only TCP relays for the maintained NPM Tailscale app gateways."""
import asyncio
import json
import os
from pathlib import Path

async def handle(reader, writer, target):
    backend = None
    try:
        remote, backend = await asyncio.wait_for(asyncio.open_connection('172.16.11.4', target), 10)
        async def transfer(source, destination):
            while data := await asyncio.wait_for(source.read(65536), 300):
                destination.write(data)
                await destination.drain()
        jobs = [asyncio.create_task(transfer(reader, backend)), asyncio.create_task(transfer(remote, writer))]
        _, pending = await asyncio.wait(jobs, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
    except (OSError, asyncio.TimeoutError):
        pass
    finally:
        writer.close()
        if backend:
            backend.close()

async def main():
    path = Path(os.environ['CREDENTIALS_DIRECTORY']) / 'relay-ports.json' if 'CREDENTIALS_DIRECTORY' in os.environ else Path('/etc/nexus/dashboard/relay-ports.json')
    ports = json.loads(path.read_text())
    servers = []
    for port in ports:
        async def callback(reader, writer, target=port):
            await handle(reader, writer, target)
        servers.append(await asyncio.start_server(callback, '127.0.0.1', port))
    await asyncio.gather(*(s.serve_forever() for s in servers))

asyncio.run(main())
