# Host power commands and Telegram startup — 2026-10-11

## Commands on Qubit, Nexus and Tensor

```sh
nexus on
nexus off
tensor on
tensor off
qubit on
qubit off
```

| Target | `on` | `off` |
|---|---|---|
| Nexus | Send wired LAN magic packets | Graceful systemd shutdown |
| Tensor | Send wired LAN magic packets | Graceful systemd shutdown |
| Qubit | Attempt wired network wake from sleep | Sleep, as requested |

No typed sudo or password prompt is required. Internally the fixed receiver action uses a narrow, password-free sudo rule. Qubit’s rule was installed through the completed macOS administrator dialog. The helper accepts only the literal `off` argument; it provides no arbitrary root-command interface. Existing broader Linux administrator permissions were preserved.

`<host> status` checks SSH reachability and prints the remote hostname. A bare remote host command, such as `nexus`, opens the existing SSH connection. A bare local host command reports that it is the current machine.

For remote wake through an awake LAN host over Tailscale:

```sh
nexus on --via tensor
tensor on --via nexus
qubit on --via nexus
```

An awake relay must be reachable using the existing SSH credentials. Strict host-key checks remain enabled. Both Linux machines being off requires Qubit to be on the home LAN, or another awake LAN relay. No router broadcast forwarding or Internet UDP exposure was added.

## Current identities

| Host | LAN | Tailscale | Wired MAC |
|---|---|---|---|
| Nexus | 192.168.1.2 | 100.96.255.81 | 98:03:8e:a7:b7:43 |
| Tensor | 192.168.1.3 | 100.114.178.50 | bc:fc:e7:6f:95:42 |
| Qubit | 192.168.1.4 | 100.103.67.56 | 6c:1f:f7:70:5f:6f |

Qubit’s wired MAC is from `networksetup` for the USB 2.5 Gb/s adapter en4. Do not substitute the generic 02:00:00:00:00:00 address reported by the shell’s ifconfig output. Its Wi-Fi adapter is a different interface/MAC and is not the target of the wired wake command.

## Telegram startup notifications

- Installed `homelab-boot-notify.service` and enabled its timer on **Nexus and Tensor**.
- On each boot the timer triggers around 60 seconds after boot, after network-online ordering. Delivery retries every minute on failure. The service remains active after success, avoiding repeated successful runs.
- Each host sends directly through Telegram HTTPS using the existing bot and its single configured authorized recipient. Tensor does not depend on Nexus being awake. No second polling bot or Docker Telegram instance was created.
- Messages include hostname, boot time in America/Toronto, LAN and Tailscale addresses. “Up” means the host is online; it does not assert that all applications have completed startup.
- Persistent boot-ID state prevents another notification for the same boot if the service is manually restarted. A new boot ID permits the next notification.
- **Initial notifications for both currently running hosts were accepted by Telegram.** Both services reported success and recorded their current boot IDs. The initial messages were produced by enabling the startup timers on the existing boot; they were not a reboot test.
- The bot token and recipient configuration are root-only under `/etc/homelab/secrets/telegram-boot.json`, delivered to the service through systemd credentials. Contents were transferred in memory over authenticated SSH and were not printed or stored in the public records. Error logs exclude token URLs and recipient values.

## Already configured and preserved

- Linux Wake-on-LAN and PCIe wake-path persistence from `WAKE-ON-LAN-2026-10-11.md`.
- Qubit’s wake-for-network setting was already enabled. Its Remote Login and peer SSH keys were already working.
- Nexus → Qubit/Tensor and Tensor → Qubit/Nexus SSH authentication worked before these commands were installed. No SSH keys or credentials were rotated.
- Existing Telegram bot, application data, Docker, storage, VLANs, NFS and SMB remained intact.

## Changes made

- Added host-named commands and `homelab-power` under Qubit `~/.local/bin` and Linux `/usr/local/bin`.
- Added `/usr/local/sbin/homelab-power-action` and `/etc/sudoers.d/homelab-power` on all three machines. Qubit’s fixed action is pmset sleep; Linux’s is systemctl poweroff without force.
- Added power-host configuration under Qubit `~/.config/homelab` and Linux `/etc/homelab`.
- Extended the existing wake sender/inventory to Qubit’s wired adapter. The existing `homelab-wake both` command continues to target only Nexus and Tensor.
- Added independent Linux Telegram startup service/timer, credential files and protected per-boot delivery state.

## Power-cycle tests — 2026-10-11

At the user's request, the actual commands were tested from Qubit, sequentially: Tensor first, then Nexus. Each `off` command requested a graceful shutdown; SSH was confirmed offline before sending `on`. Each machine returned with a different boot ID and delivered a Telegram notification matching that new boot. Both tests passed. No force-shutdown or disk recovery action was used.

Nexus returned with both pools healthy, all 50 containers running with no unhealthy status, and no failed systemd units. Tensor's power and startup-notification checks passed; it already had failed Nexus NFS mounts, Ollama and virtual-console units before the test. After reboot its `/home/qubit` NFS mount also timed out. That separate mount problem was recorded without changing unrelated services.

Detailed results: `power-test-nexus.json`, `power-test-tensor.json`, and `POWER-TEST-2026-10-11.md` in the control Mac's preparation directory and the Nexus migration archive.

## Remaining limits

Qubit sleep/wake remains untested; it stayed running to control the Linux power-cycle tests. Wired USB-adapter standby/wake support and firmware power settings may affect Qubit wake. Qubit must remain connected to the recorded adapter; network wake is from sleep, not a guarantee of cold power-on after shutdown.

## Rollback and records

- Each Linux host: `/var/lib/homelab-power/before-20261011/manifest.json` records new/replaced power files. Matching prior files were saved before replacement where they existed.
- Disable/stop `homelab-boot-notify.timer` and its service before removing notification files. Remove the credentials file only if it is still exclusively used by this feature. Keep secrets and private backup archives private.
- Restore matching saved files or remove only new paths from the manifest; reload systemd. Remove only this feature’s sudoers rule, preserving existing administrator rules.
- On Qubit, `/var/root/homelab-power-before-20261011` records prior/absent privileged files. Remove or restore those files through administrator access. Remove the new user-level command wrappers/configuration if rolling back the CLI. Its original wake inventory is `~/.config/homelab/wake-hosts.before-power-20261011.json`.
- The prior wake sender source and two-Linux-host inventory remain in each Linux user’s earlier `~/wake-on-lan` preparation directory; review subsequent changes before restoring them.
- The migration archive holds this record. New private configuration backups include credentials and must not be shared publicly.

Apple reference: [Put your Mac to sleep or wake it](https://support.apple.com/en-gb/guide/mac-help/mh10330/mac).
