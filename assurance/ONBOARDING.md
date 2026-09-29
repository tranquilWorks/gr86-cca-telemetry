# GR86 Rev B assurance integration contract

Owner request: integrate GR86 CCA after the adapter and effects assurance handoffs.
Scope: findings-only integration and local Codex bootstrap, not engineering repair.

Discovery: `2258e48fc9397b64154747cf04adf97da5974f07`, branch
`codex/rvb24-coordinated-closure`, draft PR #46. Integrate on a separate feature
branch stacked above it; preserve newer local changes and leave merge to owner.

Target: `docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad`.
This sourced project is generated from maintained `candidate/cad` and the
procurement completion SOURCES registry. Do not hand-edit it or run generators
against canonical paths during assessment. Historical packages stay historical.

Reuse external `pcb-design-assurance` 0.2.0, its exact wheel/file hashes, and the
ACT custody bridge foundation. Only repository/domain bindings, input catalog,
review routing and local guidance are specialized. No new audit engine.

Allowed changes: assurance/, a scoped software-test workflow, and README pointer.
Canonical ECAD, firmware, BOM/CPL, manufacturing payload, accepted criteria,
native suppressions and prior evidence are out of this integration's write scope.
No ACT changes, portfolio registration, supplier actions, hardware/vehicle access,
CAN transmission, flashing, manufacturing orders, merge or gate approvals.

Acceptance: source-bound external capture; pinned installed CLI and real MCP
entry points; rejected cross-domain/drift/symlink/overwrite/code-tamper cases;
six draft packet routes; findings/disposition separation; complete local prompts;
retained verification evidence with explicit blocked/unperformed outcomes.

Known compatibility gap: GR86 is KiCad 9.0.9 / PCB 20241229, whereas the pinned
framework supports 10.0.6 / PCB 20260206. Shared native assessment must remain
BLOCKED. Do not migrate CAD, spoof tools/versions or relabel historical KiCad 9
reports to obtain PASS. A separate framework compatibility change needs its own
synthetic positive/negative/boundary qualification. JLC applicability of the
schema-required Z1 slot also remains unresolved, not an instruction to use Z1.

Independent sessions require actual qualified isolation and custodian-curated
sealed packets. Preparation/import is not independence. Repairs require a
separate authorized task with accepted finding IDs. Physical/supplier evidence
and vehicle/unit acceptance remain separate from software and desktop results.
