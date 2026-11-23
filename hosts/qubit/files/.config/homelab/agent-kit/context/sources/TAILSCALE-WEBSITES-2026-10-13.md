# Tensor private websites and A1 Mini controls — 2026-10-13

## Access

Connect Tailscale on the client. Bookmark the service index:

https://tensor.tail4e4f0f.ts.net/services/

| Service | Private address | Backend | Authentication |
|---|---|---|---|
| Cockpit | https://tensor.tail4e4f0f.ts.net | 127.0.0.1:9090 | Existing Linux login |
| Syncthing | https://tensor.tail4e4f0f.ts.net:8443 | 127.0.0.1:8384 | Existing Syncthing login |
| OpenLinkHub | https://tensor.tail4e4f0f.ts.net:8444 | 127.0.0.1:27003 | Private tailnet access |
| Ollama API | https://tensor.tail4e4f0f.ts.net:8445 | 127.0.0.1:11434 | Private tailnet access; API, not a chat UI |
| Desktop notifications API | https://tensor.tail4e4f0f.ts.net:8446 | 127.0.0.1:8787 | Existing API authentication; requires desktop session |
| Tensor RGB/fans/monitors API | https://tensor.tail4e4f0f.ts.net:8447 | 127.0.0.1:18769 relay to 192.168.1.3:8769 | Existing bearer token |

## Configuration

- Added persistent Tailscale Serve HTTPS ports 8443–8447; retained Cockpit at the root of HTTPS 443.
- Added `/services/` static service index from `/srv/tensor-services/index.html`.
- No public Funnel is enabled. Access follows the tailnet's existing access policy.
- Existing application logins and secrets were preserved.
- Syncthing, Ollama and notification user units were already enabled; `Linger=yes` was already configured. OpenLinkHub was already enabled as a system unit.
- Added `/usr/local/libexec/tensor-control-relay.py` and enabled `tensor-control-tailscale-relay.service`. The relay listens only on loopback and uses a loopback source to retain the existing authenticated control service's allowlist. It does not log request headers or bodies.
- The relay uses Python's standard library. No package installation completed; an existing pacman transaction held the package database lock and was left intact.
- Non-HTTP listeners (OpenRGB SDK, NFS/RPC, SSH, Steam transport and synchronization data ports) are not browser websites. Ephemeral Codex/Electron internal listeners were not published.

## Verification

- Valid HTTPS, status 200: Cockpit, service index, Syncthing UI and OpenLinkHub UI.
- Syncthing CSS and OpenLinkHub JavaScript assets returned 200 through their HTTPS endpoints.
- OpenLinkHub's read-only devices API returned 200 with three controllers.
- Ollama `/api/tags` returned 200 and two model entries. No inference/download was requested.
- Syncthing's unauthenticated REST request was rejected (403).
- Notifications and Tensor controls rejected unauthenticated requests (401).
- An authenticated read-only Tensor RGB state request returned 200. No lighting, fan, display or power action was executed.
- Actual Syncthing GUI login/sync and notification delivery were not exercised. Desktop-only endpoints require the relevant desktop session to be active.

## A1 Mini Pause / Resume / Stop

- User confirmed the reported failure occurred while the printer was idle.
- The integration's v2.2.26 button implementation intentionally exposes Pause only for RUNNING, Resume only for PAUSE, and Stop only for RUNNING or PAUSE.
- A fresh, read-only MQTT status request confirmed the retained job status FAILED. Printer online was ON; HMS errors and print error flags were OFF.
- Local MQTT configuration remains enabled. No Bambu errors were found in the inspected recent HA log interval.
- Checked HomeKit's button-to-momentary-switch mapping; it calls HA `button.press`. Original controls and pairings were preserved.
- No stop/pause/resume command or new print was sent. Actual operation can only be verified during an appropriate running/paused print. Idle/failed jobs cannot be paused or resumed by these controls.

Source: https://github.com/greghesp/ha-bambulab/blob/v2.2.26/custom_components/bambu_lab/button.py

## Rollback

Previous Serve configuration: `/var/lib/tensor-tailscale-web-20261013/serve-before.json`.

Remove only this change's handlers: ports 8443–8447 and the HTTPS 443 `/services` handler. Retain HTTPS 443 `/` (Cockpit) and any handlers added afterward. Do not run a global Serve reset.

Disable `tensor-control-tailscale-relay.service`, then remove its unit, relay executable and static index if retiring these endpoints. Reload systemd. Existing application services, data, users, logins, network bindings and HomeKit configuration need no rollback because they were not modified.

Implementation artifact: `publish-tailscale-services.py` in this directory.
