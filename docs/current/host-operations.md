# Host operating boundaries

Owner-supplied operational constraints and dated facts carried forward from the November 5 shared instructions. Preserve these working behaviors. Physical display, clipboard, cooling and radio behavior was not re-exercised during source consolidation. Current runtime/Git changes are in README.md and docs/changes.

## Current hosts

| Host | Role / OS | LAN | Tailscale |
|---|---|---|---|
| qubit | Control Mac, macOS | wired 192.168.1.4; Wi-Fi 192.168.1.102 | 100.103.67.56 |
| tensor | Desktop, Arch/Hyprland | 192.168.1.3 | 100.114.178.50 |
| nexus | NAS/Docker/KVM, Debian 13 | 192.168.1.2 | 100.96.255.81 |
| UDR7 | UniFi router | 192.168.1.1 | existing management path |
| Bell | Upstream gateway | 192.168.100.1 | none |

SSH user is `iragonforce`. Existing aliases/keys should be preserved. Validate changed host keys through a trusted path. Tensor now uses normal OpenSSH over Tailscale; Tailscale SSH interception was disabled after its browser-authorization wait caused apparent timeouts.

From Qubit, Tensor or Nexus, the canonical `ssh qubit`, `ssh tensor` and `ssh nexus` names try the target's LAN IP for up to five seconds, then its Tailscale IP on TCP connection failure. The legacy `-lan` and `-ts` route aliases were removed on 2026-10-18. OpenSSH host-key checking remains strict; authentication or host-key failure is not a route fallback. Preserve separate bootstrap and numeric-address entries used for recovery or node automation.

Local names are `<host>.homelab.lan`; Qubit's wired alias is `qubit-wired.homelab.lan`. Tailnet domain is `tail4e4f0f.ts.net`. Nexus is no longer TrueNAS; older `truenas`, `archcore`, 100.96.131.75 and old service addresses are historical.

## Network and access

VLAN 1 / 192.168.1.0/24 is management. VLAN 2 / pia-vlan is media and vpnNet; VLAN 3 contains the existing AdGuard service; VLAN 4 / iot-vlan is IoT and iotNet; VLAN 5 / docker-vlan is general applications. New applications belong on VLAN 5 or 4, not VLAN 1. `wifi` uses the native/default network.

The user disabled AdGuard DNS. Keep public DNS and local split DNS; Qubit uses 1.1.1.1 generally and UDR7 for homelab.lan/local blinkwired.com. Media services use UDR7's Switzerland VPN and the independent WAN guard. Preserve VLAN routes, firewall segmentation, fixed Docker IPs/MACs and required Thread/IPv6/multicast behavior.

Public routes use Cloudflare → cloudflared → NPM → app. Local split-DNS success does not verify public access or Cloudflare Access login. Public apex dashboard publication was deferred.

## Nexus storage and services

Preserve bulk/fast pools, existing datasets, snapshots and migration references. Never format/recreate pools or upgrade features as routine setup. Migration archive: `/mnt/bulk/debian-migration`. Maintained Compose: `/srv/containers/compose`; active fast-backed data: `/srv/containers/data`; builds: `/srv/containers/builds`; private credentials: `/etc/nexus/secrets`.

NFS shares are selected shared files, not whole pool roots/live databases. UID/GID 1000 mapping and the macOS/Tensor recovery mechanisms are intentional. The bulk SMB limit belongs to its designated 1 TB share/dataset, not the whole pool. Do not recursively chmod/chown pools.

Record rollback before consequential changes. Database rollback needs the matching old data and image. Check bind sources before recreating services. Preserve credentials, HomeKit identities and radio network state.

Sonoff = Zigbee2MQTT; Nordic = Thread/OTBR; ZBT-1 = spare. Do not share a radio between services. Bambu is an A1 Mini in LAN/Developer mode; printing and feeding actions require a current user task. Telemetry measures CPU/GPU components, not total wall power.

## Tensor and terminals

`hibernate` means visual standby with processes/network/SSH awake. It is not true suspend/hibernation. The portrait AMD-connected 4K display still needs physical validation of a staged cross-GPU workaround after a fresh Hyprland session. Do not kill the desktop with unsaved work. Keep AIO cooling and the Off curve's 75°C safety ramp.

Tmux primary sessions are Qubit `main`, Tensor `1`, and Nexus `nexus`. Login fills only missing windows: 1 zsh, 2 nvim, 8 superfile, 9 btop. Preserve other windows and running applications. The interactive `ssh` wrapper detaches the source tmux client, and `exit` in a zsh pane with an SSH-backed tmux client detaches that remote client so the source reattaches. Tmux mouse capture is on on all three hosts for pane clicks and mouse-aware apps such as Neovim. Mouse drag and wheel do not enter tmux copy mode; shell-pane wheel events do not scroll tmux history. Use Shift-drag for terminal-native text selection. On Qubit/Tensor Ghostty, Super+Shift+M toggles mouse reporting off for plain-drag selection and native terminal scrollback, then back on for pane/Neovim mouse actions. New tmux client attachments load the primary-screen override; existing clients may need to reattach to gain native scrollback. Cmd+C/V use native Ghostty clipboard actions; Cmd+C/X also send Shift-F1/F2 for Neovim visual copy/cut through SSH. Zsh absorbs those keys outside tmux. Neovim mouse capture is on. Tensor Hyprland sends Cmd+C/V/X to Ghostty and translates them to Ctrl+C/V/X in other apps. Ctrl+C remains normal. Do not restore clipboard watchers.

Inside tmux, Zsh prompts request a thin bar cursor; Qubit/Tensor Ghostty defaults to a bar when tmux resets the cursor. Existing Zsh panes must reload their config for the prompt hook. Tensor's NVlime loads Quicklisp from `~/quicklisp` for its SBCL server and starts on the first Lisp buffer. Keep the maintained `tmux-ensure-layout` helper installed on all three hosts; the kit installer previously deleted it by mistake.


### Neovim standalone configuration

Verified November 11, 2026: Tensor runs Neovim 0.12.6 using a
standalone `~/.config/nvim` directory instead of the former symlink
to `~/.config/homelab/unified/nvim`.

The active 35-file configuration is synchronized with the repository
source `shared/unified/nvim`. Host-specific paths are resolved by
`lua/host_paths.lua`: Tensor uses `~/project` and `~/secondBrain`;
Nexus uses `/mnt/fast/project` for projects.

Tensor's `inventory/deployments.json` entries use the deployment group
`nvim-standalone`. The 35 registered targets passed installer
read-only validation with zero pending writes and zero conflicts.

The previous Tensor configuration remains in
`~/.config/homelab/unified/nvim`, with its original symlink preserved
as `~/.config/nvim-legacy-link` for rollback.

The shared source still has inactive legacy deployment records for
Nexus and Qubit. Do not apply those records as a way to deploy the
standalone configuration; their deployment paths have not been migrated.

Verified functionality includes Neovim startup, managed tmux RPC,
project and Obsidian paths, plugin initialization, Lua LSP attachment,
and Lua/Python/Shell/JSON formatting. SBCL evaluation works and Nvlime
is installed; interactive Nvlime operation remains unverified.
