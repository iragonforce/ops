# Nexus Hermes MCP configuration

`nexus-mcp.yaml` is the Git-managed source for Nexus Hermes
MCP server definitions.

The live Hermes configuration is:

`/srv/containers/data/hermes/data/config.yaml`

## Dependencies

- Python 3
- PyYAML (`python3-yaml`)
- Gitleaks for pre-commit secret scanning

## Check configuration

```bash
python3 shared/hermes/deploy-nexus-mcp.py check
```

Exit status 0 means synchronized; 2 means drift detected.

## Apply configuration

After reviewing the Git diff and scanning for secrets:

```bash
python3 shared/hermes/deploy-nexus-mcp.py apply
```

Only `mcp_servers` is replaced. The utility does not restart
Hermes or test MCP server connections.

After a successful change, restart only the supervised
`gateway-default` service and verify the gateway, dashboard,
Codex inference and affected MCP connections.

## Rollback

Revert the relevant Git commit or check out a known-good
version of `nexus-mcp.yaml`, then deploy that version and
reload the default gateway.

Never commit the full live Hermes config: it may contain
credentials and private runtime configuration.
