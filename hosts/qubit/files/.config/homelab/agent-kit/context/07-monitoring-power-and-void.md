# Monitoring, power controls and disposable lab VM

## Monitoring

Checkmk Community 2.5.0p15 was configured on Nexus at VLAN 5 address `192.168.5.56`. Collectors cover Nexus, Tensor, Qubit and UDR7 using restricted SSH commands rather than a new public agent port. Checks include Docker state/health/restarts, ZFS, systemd, network/router/VPN state and limited agent activity.

Grafana has the Checkmk datasource/plugin and **Homelab - Checkmk**, UID `homelab-checkmk`. It also has **Homelab - Hardware Energy and Containers**, UID `homelab-hardware-energy`, backed by Prometheus.

`homelab-telemetry.service` publishes CPU/GPU power, cumulative component energy and Docker status to MQTT/HA. Persistent counters are `/var/lib/homelab-telemetry/energy.json`. These are not total wall-power measurements. Runtime checks show agent processes/activity, not that an AI agent's answers are correct or that inference authentication succeeds.

## Host commands and wake

Host-named commands exist on the three control machines:

```text
nexus on     nexus off     nexus status
tensor on    tensor off    tensor status
qubit on     qubit off     qubit status
```

Linux `off` requests a graceful shutdown. `qubit off` sleeps the Mac through a narrowly scoped, previously approved permission rule, without an interactive sudo prompt. Qubit network wake is best-effort and depends on wired adapter/power state. `on` sends a magic packet directly or through the existing relay. It is Wake-on-LAN, not PXE network installation.

`homelab-boot-notify.service` and its timer send one startup Telegram notification per boot on Nexus and Tensor, retrying after network availability. Tokens are private systemd credentials. Existing automation is authorized; do not send new ad-hoc messages during context ingestion.

## void VM on Nexus

Disposable Arch CLI university-lab VM, no desktop. QEMU/KVM/libvirt, 1 vCPU, 1024 MiB RAM, 8 GiB thin disk; approximately 2.13 GiB host allocation at provisioning. AMD-V/KVM/IOMMU were previously available.

Commands from Qubit, Nexus or Tensor: `void on`, `ssh void`, `void status`, `void off`. Guest user `student`, keys-only SSH and passwordless sudo inside the guest. Working directory `~/labs`.

Installed Java 21, Python, GCC/g++, SBCL, GHC/cabal, Neovim, tmux, Git, make, GDB and small CLI tools. No personal editor plugins or GUI were added. It does not autostart with Nexus.

**All guest disk changes are discarded after full power-off.** Copy lab work out before shutdown. A normal reboot may keep the same overlay; full off/on starts clean. Base `/mnt/fast/vms/void/base.qcow2`; libvirt transient overlay handles reset. No host NAS filesystem or physical device is passed into the guest. Do not alter the baseline or shut down the VM casually.
