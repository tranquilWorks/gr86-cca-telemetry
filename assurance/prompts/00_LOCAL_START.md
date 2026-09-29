# Start in the local GR86 CCA repository

```text
Use the GR86 findings-only assurance integration in assurance/. Read root
AGENTS.md, .agents/skills/engineering-execution/SKILL.md, assurance/ONBOARDING.md,
README.md, DISCOVERY.md and evidence/INTEGRATION.json. Inspect origin, branch,
HEAD and dirty changes. The source discovery commit is
2258e48fc9397b64154747cf04adf97da5974f07 on codex/rvb24-coordinated-closure (PR46).
The integration branch is codex/gr86-assurance-integration, stacked above it.
Do not reset, clean, force-push or replace newer local work.

Scope is gr86-revb-jlcpcb, GR86-REVB / I32-SOURCED-MANUFACTURING. Current sourced
native files live under docs/engineering/rvb22/current/i32_sourced_manufacturing/
editable_source/cad. They are generated from candidate/cad and procurement
completion SOURCES.json. Audit copies only; never regenerate or edit canonical
native/firmware/manufacturing files during assurance. No other board onboarding.

Use the exact external pcb-design-assurance 0.2.0 wheel and installed-file hashes
in assurance/framework.lock.json. Use the owner's saved generic handoff if its
remote remains unavailable. Do not install an unrelated PyPI package or vendor
a replacement engine. Preserve existing Codex provider/model, Qwen and MCP setup.

Run 01 then 02. Capture actual current bytes externally, reconciling catalog
changes explicitly. Drift acceptance approves capture, not engineering changes.
The 219 input bindings and 14 candidate review routes are not approved criteria.
Source/runtime/BOM/CPL/coverage mappings are empty; JLC settings remain unset.
The schema-required Z1 slot is an applicability blocker, not a GR86 process rule.

This project is KiCad 9.0.9, while the pinned native backend accepts KiCad 10.0.6
and a different PCB format. Record native assessment BLOCKED and fresh ERC/DRC
NOT_RUN. Do not migrate, spoof versions, substitute historical zeros, bypass the
format guard or alter the engine locally. A separately qualified shared-framework
extension is required before this integration can claim fresh native assessment.

Use 03 and roles only after actual packet-only isolation is qualified. Zero
independent sessions have run. Reconcile sealed findings with 04; request owner
dispositions before any separately authorized repairs. 05 and 06 are later repair
and verification tasks, not permission to begin them now. 07 is optional MCP.

Report implemented, tested, pushed, merged, registered, blocked and unperformed
separately. No supplier action, manufacturing, flash, energization, vehicle
connection, CAN transmission, release, merge or acceptance follows from checks.
```
