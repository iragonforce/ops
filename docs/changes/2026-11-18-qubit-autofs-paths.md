# Qubit hostname-based NFS migration

Date: November 18, 2026
Host: qubit

Final native macOS autofs mounts:

- /Users/nexus/bulk -> nexus:/bulk
- /Users/nexus/t7 -> nexus:/t7
- /Users/nexus/fast -> nexus:/fast
- /Users/tensor -> tensor:/home/iragonforce

Retired the four legacy entries under
/Users/Shared/NetworkStorage.

All final mount paths were verified locally.

Original map preserved in Git commit 08b3458.
Intermediate map preserved in Git commit 05f6ce4.

Existing NFS files and directories were not deleted.
No forced unmounts were performed.

Remote validation over Tailscale remains required.
