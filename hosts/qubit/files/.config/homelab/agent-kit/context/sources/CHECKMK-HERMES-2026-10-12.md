# Nexus Checkmk and Hermes configuration — 2026-10-12

## Access

- Checkmk: https://checkmk.blinkwired.com/cmk/ (homelab clients only), or http://192.168.5.56:5000/cmk/ on the LAN.
- Username: `cmkadmin`. Qubit stores the generated login privately at `/Users/iragonforce/.config/homelab/checkmk-login.json`, mode 600. Nexus's bootstrap secret is `/etc/nexus/secrets/checkmk/checkmk.env`, mode 600. Never paste either file's contents into chat or a report.
- Grafana: https://grafana.blinkwired.com/d/homelab-checkmk — **Homelab - Checkmk**, under the **Homelab** folder. Existing Grafana login and the TrueNAS/ArchCore dashboards were retained.
- Hermes: from Qubit, run `ssh -t nexus hermes-login`. Select ChatGPT login or an OpenAI API key. The credential prompt is handled by Hermes, never by shell arguments. After authentication, run `ssh -t nexus hermes`.
- On Nexus, `hermes-login chatgpt`, `hermes-login api`, and `hermes` are available. Hermes inference was deliberately left for the user's authentication; no billable inference was attempted.

## What existed versus what changed

Already present: Grafana 13.2.3, Prometheus, cAdvisor, node-exporter, healthy Docker/storage, and a healthy Hermes v0.21.6 container restored from migration. Codex CLI existed on Qubit and Tensor. No standalone Codex CLI was found on Nexus.

Installed/configured:

1. Checkmk Community 2.5.0p15, with persistent site `cmk` on fast and new service IP **192.168.5.56**, VLAN 5. Docker/network inventory and three ARP probes found no conflict. Image is pinned to `checkmk/check-mk-community:2.5.0-latest@sha256:9eb222d05fe03d751f70ac7d8022cc655637679ba1d38922ee408e4e25058c26`. Resources: two CPUs, 4 GiB memory limit, bounded Docker logs, HTTP healthcheck and unless-stopped restart policy.
2. Four hosts: Nexus, Tensor, Qubit, UDR7. Version-matched Linux/macOS agents are collected over forced-command SSH. No new public agent port or SNMP community was opened. Qubit's collector runs as the existing user, without macOS administrator changes; Nexus, Tensor and UDR7 use root-owned read-only collectors.
3. Two dedicated Ed25519 identities: site-to-Nexus and Nexus-to-collectors. Existing human SSH credentials were preserved. Authorized keys limit origins and disable forwarding/TTY features. Host keys were verified through existing trusted SSH access and Qubit's local SSH host public key, with strict verification retained. Both private keys are mode 600.
4. An exception in Nexus's existing access-guard renderer permits **only Checkmk's current private bridge address to reach 172.16.11.1:22**. The existing 30-second refresh follows container-address changes. Other SSH and bridge isolation rules are retained. Collectors can invoke only the whitelisted host names. Qubit/Tensor collection uses their Tailscale addresses through Nexus's relay.
5. UDR7 monitoring covers CPU/memory/storage/thermal/interface state, UniFi Network service, Bell gateway reachability, VLAN/WAN byte counters, Switzerland tunnel presence, and the independent IPv4/IPv6 Media VPN guard. Router API configuration and VPN routing were preserved.
6. Nexus local checks cover every Docker container's running/health/restart state and CPU usage, Docker engine access, ZFS health/capacity, failed systemd units, Codex activity and Hermes OpenAI credential readiness. Existing Checkmk discovery detects additional host metrics and datasets.
7. Codex activity checks expose installation presence, process counts and age of session-file writes. They do not read prompts, tokens, session contents or process arguments. Idle Codex is OK. This measures runtime activity, not the correctness of AI responses or provider authentication. Hermes credentials similarly indicate material present, not a successful inference.
8. Grafana Checkmk plug-in **4.1.1**, persistent read-only data-source provisioning, a separate guest-based automation role with read access to user information/all hosts, and a thirteen-panel dashboard. Existing Grafana credentials were untouched; generated Checkmk automation credentials remain private. Grafana 13 stores dashboards in its unified resource table, which was checked rather than relying on the obsolete dashboard table.
9. Added a local HTTPS NPM route for Checkmk, with a homelab source allowlist and existing wildcard certificate. Proxy/DNS access works from Qubit. No Cloudflare public tunnel configuration was changed.
10. Reused the existing pinned Hermes image `nousresearch/hermes-agent:v0.21.6@sha256:55e192fba0cd4fde61142abbff5adeacff40efdb482ccd0ff877924bd274f909`. Installed host CLI/login wrappers. Removed the legacy main-model OpenRouter base URL, selected OpenAI Codex authentication by default, prepared a separate direct OpenAI Responses API provider, disabled provider fallbacks, and aligned auxiliary model routes with the selected OpenAI mode. Preserved model identity as `gpt-5.5`, removing its old routing prefix. `hermes model` can select another account-supported model after login.
11. Hermes's persistent working directory is `/opt/data/workspace`, mapped under `/srv/containers/data/hermes/data/workspace`. Its existing integrations, mounts, histories, skills, other credentials and Docker socket configuration were retained. Auth/config files are mode 600. The gateway restarts after successful login.

## Verified addresses

| Host/service | LAN / service address | Tailscale |
|---|---|---|
| Nexus | 192.168.1.2 | **100.96.255.81** (current verified address; older instructions had a different one) |
| Tensor | 192.168.1.3 | 100.114.178.50 |
| Qubit | 192.168.1.4 | 100.103.67.56 |
| UDR7 | 192.168.1.1 | No Tailscale dependency for its collector |
| Checkmk | 192.168.5.56:5000 | Use existing Nexus HTTPS ingress |
| Hermes | 192.168.5.55:8642 | Existing placement retained |

## Validation

- **364 services** discovered across the four hosts. All four Check_MK agent checks have run successfully in the live monitoring core. Hermes activity includes active turn leases and aggregate session/API/token counters, read from SQLite without message or prompt content.
- Checkmk, Hermes and Grafana containers were running and healthy. All **52** Docker containers were running, with no unhealthy containers at final inspection. bulk and fast remained ONLINE.
- Checkmk HTTPS and direct LAN login endpoints returned HTTP 200 from Qubit.
- Checkmk API authentication and user-information access succeeded with the separate Grafana account. Representative graph requests for Nexus load, Qubit Codex processes and UDR7 VPN state returned HTTP 200 with metric series. The installed Grafana data-source and thirteen-panel dashboard were confirmed in Grafana's actual storage. Authenticated browser rendering was not inspected. Hermes's configuration check completed without validation errors.
- Checkmk's monitoring-core configuration passed validation and was activated. The stock bundled SSL library conflicted with the system SSH binary; data-source commands explicitly remove `LD_LIBRARY_PATH` for SSH. Strict SSH verification remains enabled.
- `nexus-stack@checkmk.service`, `nexus-stack@hermes.service` and `nexus-stack@monitoring.service` are enabled. The existing stack preflight still requires correct pools/mounts and valid Compose configurations. The new configuration has not been tested by rebooting hosts or the router.
- Private validation report: `/var/lib/nexus-checkmk-20261012/validation.json`. Operational recheck: `sudo python3 /home/iragonforce/checkmk-artifacts-20261012/verify-monitoring.py`.

### Existing conditions now visible

- Tensor: `ollama.service` and `systemd-vconsole-setup.service` were already failed before this work. Both the native systemd check and the local summary report them.
- Qubit: Time Machine reports a failed mount of its backup destination. This was detected, not changed.
- Nexus: roughly 2,400 threads trigger Checkmk's default 2,000-thread warning; its default critical level is 4,000. Thresholds were retained.
- Hermes: OpenAI credentials are intentionally pending. A warning remains until the user authenticates; actual inference still needs an authenticated run.

Alerts are visible in Checkmk. No new mail/Telegram notification recipients or automated AI workloads were configured.

## Files and persistence

- Compose: `/srv/containers/compose/checkmk/compose.yaml`; existing monitoring Compose gained only Grafana's provisioning mount.
- Site/data: `/srv/containers/data/checkmk/sites/cmk/`; own hosts/rules under `etc/check_mk/conf.d/wato/`, own users/role under `etc/check_mk/multisite.d/zz-homelab-*.mk`.
- Site key: `/srv/containers/data/checkmk/sites/cmk/.ssh/id_ed25519`; Nexus relay key and pinned peer keys: `/etc/nexus/secrets/checkmk/`.
- Nexus: `/usr/local/libexec/checkmk/{agent-linux,local-checks.py,relay.py}`.
- Tensor: `/usr/local/libexec/checkmk/{agent-linux,local-checks.py,run-host.sh}`.
- Qubit: `/Users/iragonforce/.local/libexec/checkmk/`.
- UDR7: `/data/checkmk-agent/`. The monitoring key is a root authorized key restricted to Nexus's LAN source and the fixed collector command. Firmware or SSH-setting changes can remove custom router files or keys; check collector health afterward.
- Grafana provisioning: `/srv/containers/data/grafana/provisioning/`; plug-in under `/srv/containers/data/grafana/plugins/checkmk-cloud-datasource/`.
- Hermes wrappers: `/usr/local/bin/{hermes,hermes-login}` and `/usr/local/libexec/hermes-auth-mode.py`.
- Change scripts: Qubit `outputs/checkmk-hermes/`; Nexus `/home/iragonforce/checkmk-artifacts-20261012/`.
- Private backups: `/var/lib/nexus-checkmk-20261012/`, including original Compose/Hermes configuration, access-guard renderer and NPM database. Host authorized-key backups have the suffix `checkmk-before-20261012`; UDR7's original file was absent and its backup is empty.
- Snapshot: `fast/debian-live@checkmk-hermes-20261012`. No pools were formatted, recreated or upgraded. Migration references were preserved.

## Rollback

1. Stop only the new Checkmk stack and disable `nexus-stack@checkmk.service`. Preserve its site/data and private credentials until cleanup is explicitly requested.
2. Remove only the keys marked `nexus-checkmk-relay`/`checkmk-site` from the affected authorized-key files. Preserve any keys added since preparation. Remove the Checkmk exception from the access-guard renderer and refresh its own rules; do not flush the firewall.
3. Disable/delete only the newly recorded Checkmk NPM proxy, regenerate its configuration and validate/reload nginx. The new proxy ID is in `/var/lib/nexus-checkmk-20261012/checkmk-proxy-id.json`; do not restore the entire database over subsequent changes.
4. Remove Checkmk's Grafana data-source/dashboard provisioning files and mount, and recreate only Grafana through the maintained monitoring project. Retain its original dashboards/database. Remove the new plug-in only if no other data sources use it.
5. Restore only Hermes's saved configuration if reverting provider changes. Retain any newly supplied credentials unless the user asks to remove them; remove the new host wrappers if desired. Restart the existing Hermes gateway.
6. Never roll back the entire fast dataset to undo these application changes. Use individual backed-up files, accounting for later edits.

## Sources

[Checkmk Docker installation](https://docs.checkmk.com/latest/en/introduction_docker.html), [SSH data-source programs](https://docs.checkmk.com/latest/en/datasource_programs.html), [Checkmk Grafana integration](https://docs.checkmk.com/latest/en/grafana.html), [Hermes configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration).
