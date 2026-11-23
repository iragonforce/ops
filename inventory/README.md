# Inventory

The initial metadata captures are in `audit-2026-11-06/`. They cover bounded user executable/configuration paths, local privileged scripts, systemd units, shared agent/editor sources and Qubit launch agents.

Each row includes host, absolute path, modification date, file mode, digest where applicable, Git ownership at capture, static consumer candidates, documentation/manual evidence and exact-copy candidates. A static reference is not proof of runtime execution. An absent reference is not proof that a utility is unused. Third-party wrappers and package symlinks are retained in discovery until classified.

Known deployed consumers additionally include SSH configuration, shell startup, tmux bindings, Hammerspoon, launchd, systemd, Docker Compose and user-facing CLI calls. The migration manifest will distinguish adopted, vendor-owned, private-reference, historical and unresolved assets.

Never use this metadata to delete files automatically. Recheck the current digest before deployment; the capture is dated evidence, not an instruction to overwrite newer work.
