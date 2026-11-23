# Mem0: installed SDK, service disabled

Source: https://github.com/mem0ai/mem0 at the revision in sources.lock.json.
SDK: mem0ai 2.2.1; Ollama client 0.6.2, isolated from both agents' providers.
Host SDK: `.venv/bin/python`; Hermes SDK: `/opt/data/agent-tools-stage1/.venv/bin/python`.
Always set `MEM0_TELEMETRY=false` before importing or using the SDK.

Verified 2026-10-30: Tensor's existing private Ollama API is reachable at
`http://192.168.1.3:11434`. Its five model tags include qwen3.5:9b and gpt-oss,
but no embedding model. Nexus has no listener at port 11434. No model was pulled,
no cloud account created, and no inference API was called for Mem0.

Before enabling a production service, provide a local embedding model and select
a private durable vector-store deployment with backup and concurrency handling.
A suitable prospective setup uses Ollama for both extraction and embeddings,
an explicitly configured private vector store, a distinct collection and a distinct
user/agent identifier. Do not use Memory() defaults, which can select paid APIs.
An embedded local Qdrant store is suitable for an isolated single-writer experiment;
it is not claimed here as a production memory service.

Hermes' native memory stays authoritative. Mem0 has no MCP registration, startup
service, automatic extraction, automatic synchronization or provider replacement.
Both environments passed imports of Memory and the Ollama embedder implementation.
No Mem0 add/search/persistence test is claimed until the missing dependencies are
provided. The SDK and this operational reference are available to both agents
through the agent-tools-stage1 skill.

Update: stage a pinned mem0ai version in each isolated venv, review SDK/provider
changes, and repeat imports plus add/search/restart checks in an isolated store.
Rollback: remove the two stage1 venvs and skill references; existing Hermes memory
and credentials are outside them and require no migration.
