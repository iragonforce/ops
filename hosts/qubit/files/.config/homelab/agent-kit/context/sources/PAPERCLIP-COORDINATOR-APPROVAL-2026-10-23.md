# Paperclip coordinator approval-policy change

Date: 2026-10-23, America/Toronto
Execution: Hermes container on Nexus; Paperclip REST API

## Scope and prior state

The user asked for the coordinator to stop prompting for approval. The target is coordinator `0f719caa-3aa4-4bdc-8343-2eda1b64996a` (`codex_local`). Before the change it was idle with zero live runs. Its saved adapter config already had `dangerouslyBypassApprovalsAndSandbox=true`; that broad command/sandbox setting was not changed.

The coordinator's effective tool profiles already included the `record_change` tool on the Homelab Knowledge connection (`5905dfd8-f0ff-4b65-8d0a-b0b6f6580022`, catalog entry `2bc73d7b-2fdd-45ee-9e87-91b48552df01`). A policy test showed the specific tool was blocked pending approval by policy `459b9eeb-0665-43f6-8659-a8325c439383`, type `require_approval`, scoped to this coordinator and tool.

## Change and verification

- Direct PATCH to convert the connection-intent policy returned HTTP 422; readback confirmed it was unchanged.
- Created a narrowly scoped `allow` override as an experiment. Policy-test still returned `require_approval`, so that temporary policy (`4c60f6a2-c1f2-4fac-9659-5de771eb0864`) was deleted and readback confirmed removal.
- Deleted only the coordinator-specific `require_approval` policy using `DELETE /api/companies/{companyId}/tools/policies/{policyId}`.
- Readback and `POST /api/companies/{companyId}/tools/policy/test` verified that the coordinator's `record_change` request now resolves `decision=allow`, `allowed=true`, `reasonCode=allow_explicit_grant`. The other agent's approval policy remains intact. No tool profile, connection, credential or other agent permission was broadened.
- No coordinator run or MCP tool call was started. This verifies the policy decision, not end-to-end behavior.

## Remaining limit

Paperclip currently reports Homelab Knowledge connection health `error`: `connect ECONNREFUSED 172.18.0.3:8768`. Therefore `record_change` execution and its Obsidian/Qubit sync are unverified and likely unavailable until that connection is healthy. The coordinator retains its existing default-deny tool profiles and other access limits; this change removes only this one explicit approval gate.

## Rollback

Private rollback record: `/srv/containers/data/paperclip/recovery/coordinator-record-change-approval-20261023/rollback.txt`, mode 0600. It contains the prior rule fields and the POST payload needed to recreate its `require_approval` behavior (the restored rule will receive a new ID).
