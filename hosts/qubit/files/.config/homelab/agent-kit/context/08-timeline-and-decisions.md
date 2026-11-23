# Conversation timeline and corrections

Dates below come from implementation records; not every user message had an independently preserved timestamp.

1. **Preparation:** user requested TrueNAS → Debian migration, preserving boot/fast files on bulk, scripts/runbook and a physically disconnected bulk disk during installation. Archive references were intended for rebuilding, not guaranteed Docker image restoration.
2. **2026-10-08 onward:** replication/snapshot/EFI preservation and archive checks were prepared. A completed bulk scrub was required before reinstall; its later record reports no errors.
3. **2026-10-11:** Debian was installed. SSH trust was updated through verified host identities; shell/tmux/fastfetch/terminal support and boot behavior were configured. Bulk/fast restoration, NFS/SMB, packages, service upgrades and Telegram were handled in stages. Former TrueNAS system descriptions became historical.
4. **2026-10-11/12:** Wake-on-LAN, host `on/off` commands and Linux boot notifications were configured. Qubit `off` was explicitly chosen to mean sleep. Bell moved to the separate 192.168.100.0/24 upstream network; UDR7 handles LAN/VLAN policy.
5. **2026-10-12:** UDR7 VLANs/routing/firewalls, service networks, media Switzerland VPN and monitoring/Hermes preparation were recorded. Later user choices supersede this date's AdGuard DNS settings.
6. **2026-10-13:** user explicitly stopped using AdGuard DNS; final SSID layout uses native `wifi`, VLAN 4 `iotNet`, VLAN 2 `vpnNet`. Container IPs/MACs, UniFi names and local DNS/access were persisted. Qubit Wi-Fi reservation and local resolver were configured.
7. **2026-10-13:** iPhone HA access was repaired after a conflicting AdGuard DNS profile was identified. Sonoff/Nordic/ZBT-1 roles were settled; ZBT-1 ended as an unmapped spare, superseding its temporary HA passthrough.
8. **2026-10-13:** Bambu A1 Mini, PETLIBRO, partial power/container telemetry, Cockpit and HA/HomeKit additions were recorded. One shared Glance dashboard covering Nexus/Tensor was chosen. Public apex tunnel publication remained deferred.
9. **2026-10-13/14:** Tensor visual standby, RGB/fan state persistence, networking, portrait-display resets and desktop UI fixes were iterated. Repeated no-flicker checks were followed by recurrence; do not treat an earlier success as final.
10. **2026-10-14:** void disposable Arch VM was provisioned. Obsidian GPU startup, floating app rules, Waybar/workspace behavior and animations were adjusted.
11. **2026-10-14:** Input-control package hooks hit a root-manager reload failure; user rebooted Tensor. Subsequent SSH repair bypassed userdb IPC and replaced Tailscale SSH's browser gate with existing-key OpenSSH. Display mode cycling was removed and the cross-GPU setting was staged; desktop restart remained pending.
12. **2026-10-14:** MX Master 3 Solaar settings, service and five thumb gestures were configured; device online/readback confirmed, physical gestures unconfirmed.
13. **Current request:** prepare Hermes setup commands and this context pack. This does not authorize Hermes to replay the entire historical task list.
