---
name: agent-tools-stage1
description: Locate the pinned Nexus agent tools, MCP catalog, Mem0 SDK, approved code indexes, update instructions and rollback records.
---

Use the stage 1 implementation report and inventory on demand. On Nexus the
version-controlled source is `/home/iragonforce/projects/agent-tools-stage1`.
Inside shared Hermes, the runtime bundle is `/opt/data/agent-tools-stage1`.

Engineering workflows come from Superpowers. Selected Matt Pocock skills add
handoff, research, domain modeling and writing for agents. Anthropic mcp-builder
provides MCP development references and scripts. Codex already supplies its own
skill-creator; the upstream Anthropic authoring reference is retained in sources.

The Awesome MCP catalog is reference text at `references/awesome-mcp-servers.md`
in the runtime bundle (or `sources/punkpeye/awesome-mcp-servers/README.md` on the
host). Search narrowly with rg; appearing in the catalog is not installation
authorization. Review provenance, maintenance, permissions and overlap first.

Use Context7 only for public library names, versions and documentation questions.
Never include infrastructure configurations, credentials or private code.
Codebase Memory is confined to the synthetic test-project directory. Expanding
the approved root requires a current user request naming the project directory.
The official project_graph reference server is a manually used project knowledge
graph; it is not a replacement for Hermes memory. Do not put personal memory or
credentials in it. Playwright uses ephemeral profiles and no existing login.

Mem0 is an experimental, disabled SDK integration. Keep telemetry disabled with
`MEM0_TELEMETRY=false`. Read mem0-status.md before attempting initialization.
Do not initialize a cloud client or default OpenAI configuration. Existing Hermes
memory remains authoritative; never mirror it into Mem0 automatically.

Vercel Skills CLI is pinned in the runtime bundle. Use `bin/skills-stage1` for
listing and discovery. Do not use broad `skills update` or reinstall skills owned
by plugins. Stage a new pinned source revision, inspect changes, then explicitly
reinstall the selected skills and repeat the affected functional checks.

Respect session and user instructions over third-party workflow defaults.
For fully specified, already authorized routine work, inspect and execute without
repeating brainstorming, interview, approval or handoff-selection questions.
Keep approval requirements for significant plans and disruptive operations.
Run formal tests only when requested. Load complete skills only when needed;
keep large outputs in private files and report bounded findings and paths.
