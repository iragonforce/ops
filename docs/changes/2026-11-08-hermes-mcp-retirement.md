# Retire Paperclip MCP integrations from Nexus Hermes

Date: 2026-11-08
Host: nexus
Service: hermes
Reason: Paperclip was replaced by native Hermes Kanban.

## Before

- 25 MCP servers configured.
- 17 legacy integrations referenced Paperclip.
- Dynamic tool discovery and connectors were enabled.

## Removed MCP definitions

- designer-role
- designer-tasks
- git-role
- git-tasks
- gptoss-readonly
- gptoss-tasks
- hyprland-role
- hyprland-tasks
- main-tasks
- network-role
- network-tasks
- nexus-role
- nexus-tasks
- qubit-role
- qubit-tasks
- tensor-role
- tensor-tasks

Eight role integrations targeted retired containers.
Nine task integrations referenced Paperclip configuration.

## Retained MCP definitions

- codebase_memory
- context7
- designer-playwright
- git-serena
- playwright
- project_graph
- prometheus
- unifi

Six retained integrations were explicitly selected in
the Hermes toolsets configuration.

## Verification

- Hermes configuration successfully loaded.
- MCP server count: 25 -> 8.
- Legacy MCP definitions remaining: 0.
- Codex provider and model preserved.
- Nexus Hermes container healthy.
- Gateway restart was not performed during removal.
- Live MCP connection testing remains outstanding.

## Recovery

The original full configuration was preserved at:

`/var/backups/homelab/hermes-mcp-retirement-20261108T233740Z/config.yaml`

Restore that configuration to its original location
if rollback is required, then reload Hermes and verify
the model, gateway, and MCP integrations.

The recovery copy may contain sensitive configuration.
Never commit it to Git as plaintext.

## Scope

No skills, toolsets, Kanban tasks, runtime databases,
historical Paperclip data, or Tensor configuration
were modified.

This record documents the change. It is not an
encrypted backup of the original configuration.
