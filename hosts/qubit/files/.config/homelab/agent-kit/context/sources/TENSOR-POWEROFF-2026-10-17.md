# Tensor poweroff/restart investigation — 2026-10-17

Scope: read-only investigation after user reported `sudo poweroff` did not keep Tensor off. No shutdown/reboot/wake packet, firmware write, wake-policy edit or service restart was performed.

## Verified evidence

- Tensor returned online with boot ID 3d3eef3eab4648f291add182a6d5a1e5 at 2026-10-17 11:17:47 America/Toronto, kernel 7.2.10-arch1-1; systemd reported running.
- On 2026-10-16 at 21:26:26, sudo invoked /usr/bin/poweroff; logind requested poweroff. Journal reached System Power Off and systemd-shutdown at 21:26:28. Next boot began 21:26:50. This corroborates the reported quick return but cannot alone distinguish a final kernel/firmware reset from power-off followed by hardware wake or a manual power-on.
- Next poweroff request was 21:31:31; journal reached System Power Off, filesystem synchronization and journal stop at 21:31:33. No Linux boot is recorded between that shutdown and today's 11:17:47 boot. Persistent logging ends before final hardware power removal, so this is not proof the chassis was physically off.
- /usr/bin/poweroff resolves to systemctl; no local systemd-poweroff.service drop-ins. No evidence that the request was translated into suspend or reboot.
- Board: ASUS ROG STRIX X870-A GAMING WIFI, BIOS 2503 dated 2026-09-18.
- Intel I226-V enp6s0 at PCI 0000:06:00.0, LAN 192.168.1.3. ethtool and NetworkManager both report magic-packet-only WOL (`g`/`magic`), not generic link/broadcast wake.
- Enabled ACPI wake path consists of the wired NIC and bridges 04:06.0, 03:00.0, 00:02.1. Listed USB controllers and other endpoints are disabled. RTC wakealarm empty; pstore empty; current wake counters do not identify a past S5 wake cause.
- Existing tensor-disable-spurious-wake.service executes its policy at startup and shutdown; its homelab-wol.conf explicitly re-arms the NIC and upstream PCIe path afterward. This was observed during both preceding shutdowns; it is intentional WOL support, not a proven defect.
- Operational SSH follow-up from Qubit: `ssh tensor hostname`, `ssh tensor-lan hostname` and `ssh tensor-ts hostname` all succeeded and returned tensor, with the installed strict host-key configuration and fresh connections.

## Remaining uncertainty and next controlled check

Need user description of physical behavior: whether fans stop and POST returns, or fans remain running with a black screen. Shutdown journal cannot distinguish this after logging stops. A new poweroff/power-on cycle must be coordinated to protect unsaved work. If reproducing, capture network magic-packet evidence from an awake machine and observe chassis behavior; then isolate the wired wake path one variable at a time. Do not disable WOL permanently or shut down remotely without a confirmed physical recovery path. Firmware PME/AC-restore or final-kernel shutdown behavior remain hypotheses, not findings. No rollback is needed because system settings were not changed.


## 2026-10-17 — Authorized Tensor seven-minute poweroff check FAILED

At user request executed sudo poweroff at 11:30:49 America/Toronto; final logged shutdown 11:30:52. After waiting more than seven minutes, SSH at 11:38:03 confirmed a new boot ID fd7e0af6-93c4-42f6-a4e9-d1913a513bf4 and boot time 11:31:11. Tensor came back within roughly half a minute; cause and physical power-off versus reset remain unproven. No wake packet or configuration change was sent. Foreground observation tool timed out at 420 seconds without intermediate output; findings rely on the separate final SSH check and retrieved journals. No second power cycle performed.


## 2026-10-17 — Tensor poweroff issue deferred

User explicitly requested marking the reproduced poweroff/restart problem as a known unresolved issue and moving on. Added open-issues entry; investigation paused. Cause remains unproven and no corrective configuration was applied. Proposed diagnostic actions are not queued work.
