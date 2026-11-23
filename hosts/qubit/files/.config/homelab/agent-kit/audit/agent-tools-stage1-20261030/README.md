# Nexus Hermes and Codex agent tools — implementation report

Completed 2026-10-30, America/Toronto. Scope: Nexus user Codex CLI and Hermes'
shared `qubit` profile. Paperclip-managed runtime homes, roles, providers and
connection permissions were inspected as context and left unchanged.

All ten repositories were evaluated. Nine integrations are operational in their
appropriate form, including a reference catalog and a management CLI. Mem0's SDK
and operational skill are installed in both environments; its service remains
disabled under the explicitly permitted fallback. No new paid API/account was
introduced. Both agents completed actual model-driven skill and MCP workflows.

## Original environment and access

| Item | Observed baseline |
|---|---|
| Host/user | Nexus, Debian 13, `iragonforce`, UID/GID 1000; existing sudo and Docker access |
| Codex | Initially 0.163.0 at `/usr/local/bin/codex`; configuration in `~/.codex/config.toml`; final observed CLI 0.166.0 |
| Codex provider/model | Existing authentication unchanged; `gpt-6.1-sol`, reasoning `high` |
| Codex extensions | context-mode 1.0.169 and visualize enabled locally; existing connected remote plugins retained; no direct MCP definitions |
| Codex skills | Built-in `.codex/skills/.system`, plugin skills; `.agents/skills` initially absent |
| Hermes launcher | `~/.local/bin/hermes` → `hermes-homelab` → `/usr/local/bin/hermes` → Docker exec; defaults to `-p qubit` |
| Hermes version | v0.21.6, build 2026.9.24, upstream a28a5d03; image digest `55e192fba0cd4fde61142abbff5adeacff40efdb482ccd0ff877924bd274f909` |
| Hermes identity | Container configured as root, but its launcher drops CLI commands to `hermes`, UID/GID 10000; supervised gateway also runs as that user |
| Hermes runtime home | Container `/opt/data`; host `/srv/containers/data/hermes/data`; shared profile `/opt/data/profiles/qubit` |
| Hermes configuration | Profile `config.yaml`, `SOUL.md`, `skills/`, `plugins/`, `memories/`; root profile and separate Paperclip profiles also exist |
| Hermes provider/model | Existing openai-codex provider and gpt-6-sol model preserved; no authentication or provider migration |
| Hermes native tools | File, terminal, web, memory, session search, skills, todo; existing Home Assistant plugin, UniFi and Prometheus MCPs |
| Hermes overlaps | Existing local plan, debugging, handoff/recovery and homelab skills; native shell/files/Git/web/memory; separate scoped Paperclip tools and browser |
| Hermes state | Existing gateway and interactive session were active; no gateway/container or user session was restarted |
| Host dependencies | Node 20.19.2, npm 9.2.0, Python 3.13.5, pip, Git 2.47.3, Docker; no host uv |
| Container dependencies | Node 26.7.0, npm, Python 3.14.7 and Hermes' package manager; optional MCP support available |
| Storage | Approximately 78 GiB available on host root before installations; persistent fast-backed Hermes storage already mounted |
| Capture helper | `~/.config/shell/capture.sh`; inspected. Its clipboard side effect was unsuitable for private noninteractive audit output; private log files used instead |
| Documentation | Existing kit is a mirror of Qubit's canonical kit. This implementation has its own local Git repository and linked kit records |

The initial managed sandbox denied Docker and sudo with `NoNewPrivs=1`; work
continued after the user relaunched with full host access. No sudoers changes were
made by this implementation. Codex's global CLI version was observed as 0.166.0
at final verification; no command in this implementation updated the Codex package.

Paperclip already uses the Hermes gateway/relay and separate role profiles, with
some existing Context7, browser and Serena integrations. Those are not equivalent
to the user's CLI profile and were not duplicated into Paperclip's role scopes.

## Compact repository inventory

Exact evaluated source revisions are in [sources.lock.json](sources.lock.json).
The release revision for the installed Codebase Memory binary differs from its
evaluated main-branch source and is recorded below.

| Official repository | Version / revision | Integration | Hermes | Codex |
|---|---|---|---|---|
| [obra/superpowers](https://github.com/obra/superpowers) | 7.0.1; 2ce8aa15d05b | Independent native plugins | PASS | PASS |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 1.3.2 source; a496f5513d4a | Four selected pinned skills | PASS | PASS |
| [anthropics/skills](https://github.com/anthropics/skills) | ca45fc496a34 | mcp-builder skill with references/scripts/license | PASS | PASS |
| [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) | f225f117f926 | Searchable local reference; no executable server | Available | Available |
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | Source 194cc86e3ae6; server-memory 2.0.1 | Scoped explicit project graph MCP | PASS | PASS |
| [mem0ai/mem0](https://github.com/mem0ai/mem0) | Source 26cdefb46600; mem0ai 2.2.1 | SDK + operational skill; service disabled | SDK PASS | SDK PASS |
| [upstash/context7](https://github.com/upstash/context7) | Source eabe36965ec6; context7-mcp 4.4.4 | Anonymous stdio MCP client | PASS | PASS |
| [DeusData/codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | v0.12.1, release a7158ac2f48ca646b4527341b76f930f2aeff87e | Verified portable Linux binary + MCP | PASS | PASS |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | Source 0c4107acbecb; @playwright/mcp 0.0.83 | Isolated browser MCP | PASS, private host socket | PASS, native stdio |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | Source 92a9a34ac3bf; skills 1.7.4 | Pinned management CLI | PASS | PASS |

### Integration details and limitations

1. **Superpowers.** Hermes used its supported `plugins install obra/superpowers
   --ref <40-character revision> --enable` command. Its scanner's caution result
   came from documentation/test patterns including removal examples and an
   environment-presence check that redirects its output; reviewed before retrying
   with `--force`. The Python bootstrap was inspected. No Node dependency was
   needed for the Hermes hook and skills. Native skill loading passed.
   Codex's implicit official curated marketplace returned an installation result
   for version 6.3.0 but omitted it from both plugin and skill discovery. That
   installation was removed. The supported native `plugin marketplace add` +
   `plugin add` procedure against the author's pinned local marketplace works,
   independently installs 7.0.1, and passed discovery and model invocation.
   No second Superpowers skill copy was installed via Vercel CLI. Plugin skills
   run with agent permissions; their availability is not an execution sandbox.

2. **Matt Pocock.** Inspected native Codex marketplace metadata and its complete
   skill list. The documented full plugin auto-updates at startup and overlaps
   Superpowers. Instead, pinned CLI copies install `handoff`, `research`,
   `domain-modeling`, and `writing-for-agents`. Global targets are Codex
   `~/.agents/skills` and Hermes `/opt/data/profiles/qubit/skills` using the CLI's
   supported `HERMES_HOME` override. Original files, references and MIT notices
   remain in pinned source checkouts. Related skills not installed can be read
   from the source reference; tracker-specific orchestration is not enabled.

3. **Anthropic.** Inspected the 20 actual skills: technical, API, design, document,
   creative and communication packages. Installed portable `mcp-builder` only,
   with its Apache license, Python evaluation scripts and TypeScript/Python
   references. No PDF/Office/design dependency stack was installed. Existing
   Codex skill-creator and Superpowers writing-skills cover authoring; Anthropic's
   authoring material remains a reference rather than another active duplicate.
   Skill loading does not require Claude tooling. Scripts require Python and
   their documented packages only when used for a specific MCP project. The
   optional evaluator specifically imports anthropic>=0.39.0 and mcp>=1.1.0;
   it was not provisioned or run against a paid Anthropic API. This limitation
   does not affect the portable server-development guide and references.

4. **Awesome MCP.** Retained the exact catalog source and a compact routing skill.
   Hermes has `references/awesome-mcp-servers.md`; Codex can search the pinned
   source. Reviewed catalog entries for Context7, memory and browser integrations;
   no unrelated catalog server was installed. It supplies no tool schemas and
   makes no security or maintenance guarantee for listed projects.

5. **Reference servers.** Evaluated Git, Fetch, Filesystem and Memory. Native agent
   tools already cover Git/file/fetch operations, so those redundant servers were
   omitted. Selected Memory's explicit project entity/relation graph, named
   `project_graph`, with a separate state file per runtime. It is not automatic
   user memory and does not mirror Hermes memory. Exposed only create_entities,
   create_relations, add_observations, search_nodes and open_nodes. It runs as the
   invoking user; its path is scoped configuration rather than an OS filesystem
   sandbox. The upstream repository explicitly labels these reference examples,
   not production-ready infrastructure. Create/search and reconnect persistence
   passed; no unrestricted Filesystem server exists.

6. **Mem0.** Isolated host/container SDKs both import successfully with telemetry
   disabled. Ollama on Tensor is reachable but has no embedding model; Nexus has
   no Ollama listener. No inference or embedding model was downloaded and no
   external account/key/cost was introduced. A production private vector-store
   deployment, an embedding model and an explicit distinct memory identity are
   prerequisites. See [mem0-status.md](mem0-status.md). No Mem0 tool/service,
   inference test, automatic memory ingestion or provider replacement is claimed.

7. **Context7.** Pinned official npm client, two tools, anonymous mode. Both
   agents retrieved documentation whose source URL explicitly contains Next.js
   `v15.1.8`. Anonymous limits and the remote documentation backend remain outside
   local version control. No new credentials were needed. Hermes disables this
   server's optional sign-in elicitation rather than auto-accepting it; data
   retrieval remains functional. Only public library names/queries were sent.

8. **Codebase Memory.** Read the installer before choosing direct extraction of
   the official `linux-amd64-portable` release artifact. Verified the published
   SHA-256 before extracting just the binary; did not execute its auto-configurer
   or updater. Digest: `8c3d0341064301e78ecc84cf7348d4e2c6562a0f57448243ea560aaa34de36c1`.
   Separate caches, `CBM_ALLOWED_ROOT` restricted to each synthetic test-project,
   two workers, 512 MiB configured graph budget, UI disabled. The upstream process
   has additional daemon/worker overhead; 512 MiB is not a total cgroup limit.
   Out-of-root indexing was refused, add_numbers found, architecture returned,
   and fresh native agent sessions reused the persisted index. No infrastructure
   volumes or user projects were indexed. Semantic search was not separately
   evaluated. A larger approved root requires a current named-project request.

9. **Playwright.** Official package with its exact Playwright dependency and
   Chromium revision 1247 (Chrome for Testing 155.0.8059.12). Headless, ephemeral
   profiles, no existing storage state, service workers/WebMCP disabled, image
   output omitted by default. Host Chromium sandbox works; container sandbox did
   not. Hermes therefore uses a systemd socket-activated host process running
   as iragonforce. Its Unix socket is mode 0660, group hermes-agent-tools (GID
   10000), with parent mode 0750 and inherited ACLs removed only on this new
   directory. No new TCP listener, root browser, sandbox disable flag, key or
   external login was added. Ten ordinary browser tools are exposed; unsafe code
   runner, file upload and other unused tools are excluded. The browser's network
   reach is not an origin-enforced sandbox; initial tests visited only loopback.
   Snapshot files are returned by reference, with inspection reading only needed
   content. A test-page favicon 404 is harmless and does not affect interaction.

10. **Vercel CLI.** 1.7.4 requires Node >=22.20.0, so a pinned Node 24.15.0 runtime
    is supplied inside the tooling bundle; system Node is unchanged. `skills-stage1`
    wrappers expose it to both agents. CLI version, local selected-skill install,
    listing and public discovery were exercised. Hermes targeting uses
    HERMES_HOME explicitly; defaults to ~/.hermes would be wrong here. Do not use
    broad updates or reinstall plugin-owned skills through this CLI.

## Configuration, persistence and token efficiency

- Codex gains four concise MCP definitions, explicit enabled tool lists and a
  short developer-instruction policy. Its model, reasoning, credentials, original
  marketplace settings, hooks and enabled unrelated plugins remain intact.
- Hermes gains those servers in the shared profile and its CLI platform allowlist.
  Other messaging-platform allowlists and Paperclip profiles remain unchanged.
  Existing native memory and compression sections compare equal to the backup.
- Hermes Tool Search is explicitly on, listing capped at 1,200 tokens, and new
  servers use lazy startup with cached schemas. Output limits are 24,000 bytes /
  400 lines. Actual CLI logs confirmed deferred tool assembly and native calls
  through tool_search/tool_describe. Original compression settings are unchanged.
- New native exposure is 28 selected server tools. Hermes adds eight generated
  MCP resource/prompt utility tools, yielding 36 registry entries for these four
  connections. No duplicate names were present. Catalogs and Mem0 add no tools.
- Full skill instructions remain loaded on demand. The Superpowers Hermes hook
  supplies its own first-turn bootstrap. Compatibility policy appended to Hermes
  SOUL and Codex developer instructions prevents repeated interviews for routine
  authorized work, preserves significant-plan requirements, and respects the
  user's restriction on unsolicited formal tests.
- Codex's new ~/.local/bin/codex wrapper runs the original absolute launcher while
  supplying the pinned Node runtime to plugin children. This fixes the pre-existing
  context-mode missing-better-sqlite3 failure by using Node's built-in SQLite.
  Fresh native ctx_execute and SQLite-backed ctx_batch_execute both passed.
  An attempted native-addon repair is retained only in the private recovery
  directory as unused data; it is not required at runtime.
- Persistent Hermes components live in /opt/data, backed by the existing fast
  bind mount; original container images were not modified or recreated. Host
  browser socket activation is enabled at boot. Fresh CLI sessions passed.
  A full machine reboot/container recreation was not performed.

## Functional verification

Sanitized receipts: [verification.json](verification.json). Raw agent traces and
private diagnostics are excluded from Git under logs/ and private/.

| Requested check | Evidence / result |
|---|---|
| Hermes engineering skill | Native skills_list + namespaced skill_view, and model session invocation: PASS |
| Codex engineering skill | Native app-server skills/list: 35 enabled skills, no discovery errors; model loaded verification-before-completion: PASS |
| Context7, both agents | Actual MCP query-docs returned source paths pinned to Next.js v15.1.8: PASS |
| Codebase Memory, both | Synthetic repository indexed, add_numbers symbol found, architecture returned, invalid root refused: PASS |
| Official reference MCP, both | Entity creation/search; both fresh native sessions searched stored entity: PASS |
| Playwright, both | Loopback page title/content, button click, Interaction passed, browser close: PASS |
| Mem0 | Host and container SDK/provider imports: PASS; production service intentionally disabled, prerequisites recorded |
| Existing Hermes memory | Native MemoryStore loaded 1 memory entry and 11 user entries; before/after file hashes equal: PASS |
| Existing Codex functionality | Actual model-driven tools plus working pre-existing context-mode in a fresh session: PASS |
| Duplicate tools | Four unique definitions; selected tools and native registry names checked: PASS |
| Unnecessary questions | Final Codex and Hermes routine verification completed with zero clarification calls: PASS |
| Restart persistence | Fresh app-server/CLI processes rediscovered skills, MCP schemas and persisted graph results: PASS |
| Provider/config preservation | Before/after selected configuration equality and unchanged Hermes messaging scopes: PASS |

Important failed attempts were diagnosed, not counted as successes: implicit
curated Superpowers discovery on Linux; a root-owned new host state directory;
container Chromium sandboxing; inherited ACLs on the new Unix socket directory;
and Hermes' separate CLI platform allowlist. Recovery used supported local
marketplace discovery, corrected ownership only on new directories, a private
host transport, scoped ACL correction and the CLI allowlist addition. Hermes'
pre-existing unknown-stt warning remains; it did not prevent final verification.

The requested checks were run. No unrelated project's formal test suite, physical
hardware test, production dashboard interaction or outgoing message was performed.

## Updates and rollback

See [OPERATIONS.md](OPERATIONS.md) for component-specific procedures and private
backup locations. Exact npm transitive versions/integrities are in package-lock;
separate Python dependency locks cover both interpreter versions. Revisions are
pinned snapshots; there is no new scheduled updater or unattended update job.

Stage 1 provides tested tools and rollback material for the next milestone.
Persistent quota-aware automatic agent resumption is not implemented or enabled.
That milestone still needs quota/reset detection, durable checkpoints, bounded
retry scheduling, idempotency, single-run ownership and reboot recovery design.
Mem0 is not a prerequisite for that work; existing agent memory remains available.
