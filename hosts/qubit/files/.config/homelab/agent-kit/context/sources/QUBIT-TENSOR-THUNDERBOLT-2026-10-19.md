# Qubit–Tensor Thunderbolt direct link — 2026-10-19

## Initial state and changes

- Qubit `system_profiler SPThunderboltDataType` saw Tensor's Linux Internet Protocol service at a reported 40 Gb/s on Mac Thunderbolt Bus 2, receptacle 3. Qubit's existing Thunderbolt Bridge (`bridge0`, members en1/en2/en3) was on DHCP with no IPv4 address.
- Tensor had an existing NetworkManager `thunderbolt-link` profile on `thunderbolt0` with manual `10.0.0.2/30` and no gateway. Ethernet LAN and the normal default route stayed on `192.168.1.3` / `enp6s0`.
- Set Qubit's Thunderbolt Bridge to manual `10.0.0.1/30`, no router. Added Qubit `~/.ssh/config.d/80-thunderbolt.conf`: `tensor-tb` goes to `10.0.0.2`, uses the existing Tensor SSH identity and `HostKeyAlias 192.168.1.3` with strict key checking. The canonical short-name SSH routes were not changed.

## Checks and current limit

- Briefly, ICMP passed three of three packets at about 0.5 ms. Over 15 seconds, only two of 15 passed. A subsequent ten-packet check passed one packet; a direct `ssh tensor-tb` timed out. Qubit uses its LAN default route while the bridge carrier is down.
- Tensor kernel logs repeatedly show `thunderbolt 0-1: host disconnected` and a new Apple Mac15,6 host every five to ten seconds. Its controller is ASMedia ASM4242 (`0000:72:00.0`). Qubit's bridge changes between active and inactive. The physical carrier is unstable; file throughput was not measured.
- User reported a firmly seated 1 m Intel-certified Cable Matters 40 Gb/s Thunderbolt 4 cable. Reseating both ends did not stop the cycles.
- Temporarily set the Tensor controller `/sys/bus/pci/devices/0000:72:00.0/power/control` from `auto` to `on` for 18 seconds; disconnects continued, then restored `auto`. Temporarily unloaded `thunderbolt_net` for 15 seconds; disconnects continued, then reloaded it. This points below the IP and network-driver layer but does not prove a cable, port, or controller fault.
- A few minutes after reseating, the carrier held for 15/15 direct pings (about 0.5 ms), and `ssh tensor-tb` reached Tensor with a return route through `thunderbolt0`.
- A short four-stream `iperf3` memory run reached approximately 10.5 Gb/s in reported one-second intervals, then stalled before a valid final receiver result. The interrupted client reported 8.35 Gb/s sender aggregate, but this is not accepted throughput. Direct ICMP then failed 6/6 despite apparent carrier. Tensor logged `TCP: thunderbolt0: Driver has suspect GRO implementation` and, during a `thunderbolt_net` reload, USB4 config-space read timeouts plus hop-deactivation failures. Driver module reloaded; direct traffic remained down. No files were transferred and no disk changes were made for the throughput run.
- The user tried Tensor's second rear 40 Gb/s USB4 port. Neither Tensor nor Qubit detected a peer at that point. A targeted reset of Tensor's ASMedia NHI PCI function `0000:72:00.0` at 01:23 completed (`reset done`) but did not restore peer detection. Normal LAN SSH stayed up. This reset was limited to the USB4 host-router function; no other Thunderbolt devices were observed on it.
- Pending user confirmation: unplug/replug the second rear USB4 port after the controller reset. If still absent, coordinate any full system power cycle around Tensor's unsaved desktop work and known poweroff issue. When the peer returns, check interface naming, sustained carrier, direct SSH and a conservative real transfer before any further high-load run.

## Rollback

- Qubit: `networksetup -setdhcp 'Thunderbolt Bridge'`; remove `~/.ssh/config.d/80-thunderbolt.conf`.
- Tensor's existing NetworkManager Thunderbolt profile was not changed. Its temporary controller setting and driver state were restored during checks.
