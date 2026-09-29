# GR86 source and authority discovery

Discovery source: `tranquilWorks/gr86-cca-telemetry`, engineering branch
`codex/rvb24-coordinated-closure`, commit
`2258e48fc9397b64154747cf04adf97da5974f07`, draft PR #46. Main is older.
The assurance branch is stacked above that engineering branch, not a new board
baseline. Never reset newer local work to these historical discovery hashes.

## Source ownership

Current sourced project: `docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad/GR86_CCA_RevB`.
Maintained circuit/geometry: `docs/engineering/rvb22/candidate/cad/`.
Procurement ownership: `docs/engineering/rvb22/analyses/i32/procurement_completion/SOURCES.json`.
The existing `build.py` generates sourced native CAD from those owners and adds
only four procurement properties to fitted objects. It owns subsequent package
generation. Assessment must not invoke its mutating prepare/package/verify
commands on canonical paths. Separate accepted repairs must follow that source
model in a complete disposable repair checkout, with controlled regeneration.

The catalog binds 219 files: 156 native-domain files and 63 context inputs,
including all 32 source-bound firmware files. One tracked KiCad session/cache
file is deliberately excluded. There are 12 schematic files (root plus 11), one
PCB, project/rules, local libraries, and 33 STEP envelope models. These models are
not equivalent to vendor-qualified mechanical models. The initial reviewer
projection contains 120 design files; envelope models and design-history
metadata require custodian inspection before being added to a curated packet.
Historical approvals/reviews, firmware, BOM/CPL, process records and generated
summaries remain bound context, never automatic first-pass reviewer authority.

## Effective package facts to reconcile, not new acceptance criteria

The I32 sourced package records 177 fitted references, 175 factory placements,
F101/U401 local install and C203/R301/R306 DNP. Thirteen frozen procurement
bindings and documented aliases must survive any source reconciliation. Dated
catalog captures establish what was recorded then, not present stock or a
supplier's acceptance of this order. The U101 H-grade #PBF selection does not
silently acquire #W pedigree. C162 catalog package wording does not supersede
the exact manufacturer's drawing.

Use `HARNESS_INTERFACE_CONTRACT.json` and `SINGLE_RETURN_EFFECTIVITY.json` for
vehicle/F1 cavities and views: one full-current vehicle ground return, the spare
ground cavity unpopulated, a fused switched feed, and explicit CAN/sensor routes.
Read current native/firmware pin maps; the older root README/Rev A descriptions
do not override I32 effectivity. The bound candidate firmware is the effective
160 MHz build, with listen-only CAN and source-specific GPS/oil/BLE behavior.
No flash, energization, vehicle connection or CAN transmission is part of this
integration. Virtual BLE oil frames do not authorize transmitting vehicle CAN.

Current assembly requirements bind C05/W02/T03 mechanics and retained thermal
limits/budget. Older trial cases do not silently override them. Historical I25
heat/loss/correlation results are model evidence, not a fresh solve or measured
junction-temperature/physical-fit result. Retain local-air and auxiliary module
limits as distinct requirements. The supplier process includes a specific
four-layer stack, 49 special fill/cap/planarize vias, exact placement conventions,
manual/wave handling and two local installs. Supplier approval and physical
acceptance remain separate from the repository's digital checks.

Existing `FINAL_REVIEW_REGISTER.json`, `FINAL_GATES.json`, I32 supplement and
source manifests retain their canonical IDs and historical scope. Fourteen new
GR86-REVIEW routes are navigation, not replacements for those requirements,
findings, dispositions or approvals. Reconcile conflicts through existing
change control; never infer closure from a previous headline or zero count.

## Compatibility and assurance gaps

The current native design is KiCad 9.0.9, PCB format 20241229 and schematic
format 20250114. The pinned shared engine supports KiCad 10.0.6 / PCB 20260206.
Installed CLI/MCP correctly stop with `unsupported PCB format; no automatic
migration`. They run only the native version probe, not fresh ERC/DRC. A separate
shared-framework compatibility change needs synthetic positive/negative/boundary
tests; this board integration must not migrate inputs or duplicate the engine.

The projection has no approved sources, numeric rules, parts, cases, BOM/CPL or
coverage mappings. Its process fields are unset. The shared schema's mandatory
Z1 slot remains empty/CANDIDATE: this is an applicability gap, not an instruction
to apply machining rules to JLCPCB. Historical process documents are retained
for controlled mapping, not promoted to approved runtime criteria.

Independent reviewer host/tool isolation is not qualified. Six packet routes
exist, but no independent sessions ran. Held-out adequacy, exact primary-source
completeness, supplier acceptance, bench/thermal/fit/vehicle/unit results and
release approval remain blocked or unperformed as recorded. Prior results are
not erased, and are not represented as new verification.
