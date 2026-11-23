# Hermes homelab context pack

Prepared on 2026-10-14 for the existing Nexus Hermes installation. This is a curated handoff, with topic files, dated source notes and a selected live metadata capture. No raw conversation or credential values are included.

## Run from Qubit

Authenticate using the existing interactive helper. It offers ChatGPT OAuth or an API key:

```bash
ssh -t nexus hermes-login
```

Alternatively choose exactly one mode explicitly:

```bash
ssh -t nexus 'hermes-login chatgpt'
# OR
ssh -t nexus 'hermes-login api'
```

Choose a model your selected account supports; this avoids assuming the previously configured model is still available:

```bash
ssh -t nexus 'hermes model'
```

Start an interactive session in the new context directory with the prepared first prompt:

```bash
ssh -t nexus 'hermes chat --in /opt/data/workspace/homelab-context --query-file /opt/data/workspace/homelab-context/BOOTSTRAP_PROMPT.md'
```

Start a later fresh session in this workspace:

```bash
ssh -t nexus 'hermes chat --in /opt/data/workspace/homelab-context'
```

Resume the most recent workspace session:

```bash
ssh -t nexus 'hermes chat --in /opt/data/workspace/homelab-context --continue'
```

Do not use `--yolo`, the auto-approval oneshot mode or `--ignore-rules` for the orientation workflow. The initial prompt is a read-only handoff request. No inference was run during preparation; these commands authenticate/start it when you run them.

## Already logged in on Nexus

Run the same `hermes-login`, `hermes model` and `hermes chat ...` commands without the `ssh -t nexus` wrapper. The `--in` and prompt paths refer to the container, not the host shell.

## Locations

- Qubit working copy: `outputs/hermes-context` inside this Codex workspace.
- Nexus host: `/srv/containers/data/hermes/data/workspace/homelab-context`.
- Hermes container: `/opt/data/workspace/homelab-context`.
- Recovery copy: `/mnt/bulk/debian-migration/post-install/hermes-context-20261014`.

Existing Hermes home, global SOUL.md, default workspace AGENTS.md, memories, credentials, model configuration and integrations are preserved. A project-local AGENTS.md in this folder supplies the handoff when started with the explicit workspace path. Other topic files are read through the prepared prompt; they are not all automatically injected.

## Files and upkeep

See START-HERE.md for read order. `sources/INDEX.md` describes the preserved implementation notes. `11-live-nexus-inventory.json` is a point-in-time snapshot, not a monitoring feed. `SHA256SUMS` covers the pack files at creation; regenerate it deliberately after documented updates. The inventory collector is metadata-only and should run on the Nexus host when a fresh capture is requested.

## References

- [Hermes context-file discovery](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files/)
- [Hermes quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart/)
- The installed v0.21.6 CLI help was checked for `chat --in`, `--query-file`, `--continue`, `model`, and `auth add`.
