# Hermes runtime finalization — 2026-11-18

Host: Nexus. Application: Hermes Agent.

## Coordinator instructions

- SOUL.md deployed and SHA-256 verified:
  `e0521c4b62d3b6793697124b7cba259d0ea162706c825af183a9b86150c1c709`
- AGENTS.md runtime instructions synchronized:
  `f9d346fa69923d93f70077121c044168e5bdad6f1c689a8a2920c0101b262783`
- Four independent runtime instruction copies updated.
- DevOps and Research profile links redirected to the runtime workspace instructions.
- The independent Hermes `workspace/ops` Git checkout was not modified.

## SSH access

- Tensor: authenticated SSH returned `tensor`.
- Qubit: authenticated SSH returned `qubit`.
- Existing SSH identities and strict host-key verification retained.
- Hermes SSH configuration was replaced at runtime.
- No additional SSH service or routing skill is required.

## Skills

- Removed `homelab-host-operations`.
- Removed the selected obsolete networking, infrastructure and document skills.
- Retained the Hermes, GitHub, Playwright and agent-tools skill functionality.
- Final acceptance identified an inactive Obsidian skill remaining on disk.

## Tools

Installed in the running Hermes container:

- GitHub CLI (`gh`)
- rsync
- fd-find (`fd` compatibility link)
- wget

The Hermes CLI, Git, SSH, Python, Node and Docker were already available.

GitHub Git access through the existing SSH identity was verified.
GitHub CLI API authentication was not configured.

## Acceptance

Fresh-session checks confirmed:

- Coordinator identity and instructions
- Repository source-of-truth knowledge
- Tensor and Qubit SSH connectivity
- Infrastructure reasoning and safety boundaries

The remaining optional skill observations do not block coordinator operation.

## Persistence and follow-up

The running container was not restarted.

Container-local package installations are not guaranteed to survive
container recreation. The runtime SSH configuration, skill removals,
and profile-link changes require reconciliation with deployment source
before claiming fully reproducible deployment.

The Hermes `workspace/ops` checkout remains independently divergent
and was intentionally not reset, cleaned or merged.

This record documents verified runtime state; it does not itself
deploy or persist those changes.
