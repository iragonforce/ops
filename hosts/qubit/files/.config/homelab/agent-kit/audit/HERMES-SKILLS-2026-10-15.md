# Hermes skill audit — 2026-10-15, America/Toronto

Read-only inspection of live Nexus Docker skill files, configuration metadata and Hermes discovery/resolution. No skill content or supporting scripts were executed. No skills, configuration or running sessions were changed.

## Inventory

Default runtime: five skill files and five unique loadable skills. Named profiles nexus, tensor and qubit: six skill files each, with five loadable entries because two files declare the same hermes-agent name. All inspected SKILL.md frontmatter parses and all files are readable by the actual Hermes user. Disabled lists and external directory lists are empty; bundled reseeding opt-out markers are present.

Shared skills: blocked-page-recovery, grounded-citations, hermes-agent, plan and systematic-debugging. Reference library remains 623 entries; these are not enabled runtime skills. No additional homelab-specific skill was found in the active skill directories.

## Issues

- Each named profile has different-content copies at `skills/hermes-agent/SKILL.md` and `skills/autonomous-ai-agents/hermes-agent/SKILL.md`. Hermes marks both ambiguous. The nested copy remains loadable by `autonomous-ai-agents/hermes-agent`; bare `hermes-agent` fails with an ambiguity error. The root-level copy has no disambiguating load name. Default runtime is unaffected.
- The plan skill is enabled, but `/plan` belongs to a built-in command. Invoke `/skill plan` explicitly.
- Metadata/discovery checks do not prove every skill's instructions, external dependencies or supporting scripts function. No formal tests or provider inference were performed.

Recommendation: compare and consolidate the two Hermes skill versions in each named profile while preserving a recovery copy. This audit did not perform cleanup.
