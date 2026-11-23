# Qubit Wi-Fi NFS authorization

Date: November 18, 2026
Host: nexus

Authorized Qubit Wi-Fi address 192.168.1.5 in the
existing NFS firewall and export configurations.

Preserved Qubit Ethernet 192.168.1.4 and Tailscale
100.103.67.56 access, along with all other clients.

NFS server was not restarted. Firewall was replaced
in one nftables transaction; exports were refreshed.

Git baseline: 457ed733fa7dc3e120d8a462de046a658baed4f5
Live rollback backup: /var/backups/homelab/qubit-nfs-20261118.EgLOVr

Rollback: restore the three live configuration files,
replace the nexus_nfs table using the previous firewall
definition, and run exportfs -ra.

Pending: verify NFS from Qubit over LAN and Tailscale.
