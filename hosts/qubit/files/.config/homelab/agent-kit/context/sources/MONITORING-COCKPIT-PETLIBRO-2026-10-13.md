# Monitoring, Cockpit, PETLIBRO and Tensor standby — 2026-10-13

## Access

Tailscale must be connected. These endpoints are private; Funnel is not enabled.

| Function | URL |
|---|---|
| Nexus Cockpit | https://nexus.tail4e4f0f.ts.net |
| Tensor Cockpit | https://tensor.tail4e4f0f.ts.net |
| Home Assistant | https://nexus.tail4e4f0f.ts.net:8443 |
| HA monitoring dashboard | https://nexus.tail4e4f0f.ts.net:8443/homelab-monitoring/hosts |
| Grafana reports | https://nexus.tail4e4f0f.ts.net:8444/d/homelab-hardware-energy |

Use existing operating-system credentials for Cockpit and existing Grafana/HA credentials. None were changed.

## Completed changes

### Cockpit

- Nexus: Debian Cockpit 337-1+deb13u2. Tensor: Arch Cockpit 369-1.
- Both socket units enabled at boot. Tensor listens on loopback port 9090, proxied by persistent Tailscale Serve HTTPS 443.
- Nexus retains existing Nginx Proxy Manager LAN/Tailscale listeners and application routes. A dedicated TLS virtual host proxies the Nexus hostname to Cockpit at 172.16.11.1:9090. Tailnet source ranges only are allowed.
- Nexus Cockpit also listens on loopback. `/etc/nexus/cockpit-guard.nft` permits the NPM backend and loopback, rejecting other direct access to port 9090. `homelab-cockpit-guard.service` is enabled.
- Managed Tailscale certificate stored privately under NPM `data/custom_tls`; `nexus-cockpit-cert.timer` renews it daily. HTTP host 190 redirects to HTTPS.
- HTTPS login pages return 200 with valid TLS on both machines. Nexus HTTP redirects to HTTPS. HA 8443 and Grafana 8444 return 200.
- Authentication with an actual browser login was not exercised; login credentials remain unchanged.

Rollback: backups are under `/var/lib/homelab-cockpit-20261013`. Restore previous Cockpit configuration/socket drop-ins, remove the Nexus custom virtual host and restore host 190's prior advanced configuration, validate/reload NPM, then disable the certificate timer and guard if no longer needed. On Tensor, remove only Serve's HTTPS 443 handler. Do not reset all Serve configuration: Nexus HA and Grafana have independent handlers.

### Read-only power and Docker telemetry

- Both machines run `/usr/local/libexec/homelab-telemetry.py` under enabled `homelab-telemetry.service`.
- Added Python Paho MQTT: Nexus 2.1.0; Tensor 1.6.1. Existing MQTT broker and HA integration retained.
- CPU package energy comes from hardware RAPL counters. GPU power comes from AMD hwmon on Nexus and NVIDIA tools on Tensor. GPU energy is integrated from samples. Sample intervals use a monotonic clock.
- Persistent cumulative counters: `/var/lib/homelab-telemetry/energy.json`. Latest numeric state: `latest.json`. No credentials are stored in these files.
- HA discovery publishes CPU/GPU watts, cumulative component kWh, CPU/memory utilization, availability, Docker counts and each running container's running/problem/CPU/memory reports. Expected containers persist after discovery so a later stopped or missing container is flagged.
- Nexus publishes both hosts into existing node-exporter textfiles. Prometheus has six CPU/GPU/combined power series across the two hosts.
- Nexus had 52 running containers and zero problems during validation. Tensor had no Docker containers running; its Docker count was zero.
- New HA sidebar dashboard: **Homelab Monitoring**, with Hosts and Containers views and a Grafana report link.
- Four daily/monthly component-energy utility meters created through HA configuration flows. Their entity IDs have the `nexus_monitoring_` / `tensor_monitoring_` device prefixes; the dashboard uses the registered IDs.
- Added two component consumers to HA's Energy dashboard. Hardware energy statistics are recorded. No grid/whole-home source or electricity tariff was invented.
- Grafana dashboard **Homelab - Hardware Energy and Containers**, UID `homelab-hardware-energy`, contains 11 panels using the existing Prometheus datasource. Provisioning completed and the dashboard exists in Grafana's resource database. An authenticated dashboard API request was not available with the existing credentials; credentials were preserved.
- Grafana private HTTPS 8444 uses enabled `nexus-grafana-tailscale-relay.service`, loopback 13037, and persistent Tailscale Serve. Existing Grafana routes remain available.

These values cover CPU/GPU components only. They exclude PSU losses, motherboard, drives, fans and other devices. They are not wall electricity measurements. Container CPU/memory percentages do not measure per-container electrical consumption.

Rollback: stop/disable the telemetry service before removing its executable. Preserve energy counters for recovery. Remove its MQTT discovery records only if retiring the entities. Remove only the added HA meters, dashboard and Energy device consumers; the previous Energy preferences are saved in `/var/lib/homelab-monitoring-20261013`. Remove Grafana's energy provider/files and reload provisioning. Remove only the Serve 8444 handler and Grafana relay if retiring this URL.

### HomeKit

- Extended existing **Tensor Home** bridge, port 21065. It now includes 69 entities: the 12 existing Tensor/printer entities plus 57 host/Grafana/container status indicators.
- The two stored paired clients, pairing key and all 12 prior accessory ID assignments were compared against the pre-change archive and preserved.
- Watts/kWh cannot be represented by the HA HomeKit Bridge. Actual readings and reports are available in HA/Grafana. Apple Home receives availability/problem indicators.
- Physical display of the added indicators on the iPhone has not been checked.

Rollback: restore only the previous `homekit` block from `/var/lib/homelab-monitoring-20261013/tensor-control-before-monitoring.yaml`, then call HA `homekit.reload`. Preserve unrelated package edits and existing HomeKit pairing storage.

### PETLIBRO PLAF301

- Installed community integration `jjjonesjr33/petlibro` stable **v1.2.32**, commit `e307919794b01173294939e7b9772fa04a1710d4`.
- Version/commit/archive SHA recorded privately under `/var/lib/nexus-petlibro-ha-20261013`.
- Configured account through the supported HA user flow. Integration title **PETLIBRO Feeder**, state **loaded**; device model confirmed **PLAF301**.
- Region normalized to API value **US** in the private credential file. This does not change the feeder's Toronto timezone or feeding schedule.
- 79 entities registered; 77 had states and 59 were known/available during inspection. Unsupported or unpopulated features may remain unknown/unavailable.
- No feed, schedule, portion-size or physical control commands were executed. Feeder controls were not added to HomeKit.
- Credentials remain only in private local/Nexus files and HA integration storage. Account values are excluded from this report.
- This is a cloud integration. The project documents that reusing the phone-app account may log the app out; a separately shared account can be substituted later.

Rollback: remove the PETLIBRO integration entry through HA, then remove `custom_components/petlibro` and restart HA if desired. Do not replace the whole `.storage` directory with its historical backup, since that would discard unrelated later configuration and pairing changes.

### Tensor stays awake during visual standby

- User rebooted Tensor after it became unreachable. Prior boot logs showed no system suspend entry; the original outage cause remains unconfirmed.
- Found Tensor's clock nearly four hours behind and time synchronization disabled. Enabled `systemd-timesyncd` with Cloudflare/Google NTP and Arch fallback servers. `NTPSynchronized=yes` verified; Tailscale health list is empty.
- Added `/etc/systemd/sleep.conf.d/90-visual-standby.conf` to disable actual suspend, hibernation, hybrid sleep and suspend-then-hibernate.
- Added logind drop-in with idle action and suspend/hibernate keys set to ignore; logind configuration reloaded without restarting the desktop.
- Retained Hypridle's 1800-second visual standby and input-triggered resume, existing RGB state restoration, fan profiles, display configuration and btop behavior.
- Executed `hibernate`, waited 10 seconds, then `hibernate resume`: both exited successfully. Independent SSH remained reachable during standby; final state was awake.
- The complete 30-minute idle interval and physical keyboard wake were not repeated during this session. Visual artifacts require physical observation.
- Existing unrelated failed units seen: `ollama.service`, `systemd-vconsole-setup.service`; these were not changed.

Rollback: remove the two `90-visual-standby.conf` drop-ins (or restore prior versions from `/var/lib/tensor-awake-20261013`) and reload logind. Remove/restore the NTP drop-in and prior timesync enablement only if required; keeping accurate time is recommended. The visual `hibernate` wrapper was not replaced.

## Implementation artifacts on Qubit

Directory: `outputs/udr7-network` in this chat's workspace.

- `install-cockpit-private.py`, `publish-nexus-cockpit.py`
- `homelab-telemetry.py`, `install-homelab-telemetry.py`
- `configure-energy-grafana.py`, `configure-homelab-monitoring-ha.py`
- `install-petlibro-ha.py`, `configure-petlibro-ha.py`
- Tensor guard: `outputs/tensor-control/keep-host-awake.py`

Apply scripts only after reading the current state and private rollback copies. Never dump HA storage, rendered secrets, passwords or private keys into logs or chat.
