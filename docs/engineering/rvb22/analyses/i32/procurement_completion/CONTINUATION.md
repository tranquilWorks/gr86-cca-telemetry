# Continuation checkpoint — 2026-09-15

Objective: make the actual ECAD, BOM, CPL and manufacturing package coherent
with the qualified logical/simulation design and close procurement assignments.
Owner requires every factory part in JLC's catalog; Global Sourcing and
consignment are not accepted factory routes. Keep the 13 frozen references,
177/175/2 population, DNP set and engineering constraints.

Repository: tranquilWorks/gr86-cca-telemetry, PR #46, branch
`codex/rvb24-coordinated-closure`; starting SHA
`ad507920488976ff03e4598e79c9bbe5e9f0ba3b`. Work appends to that handoff.
Do not merge, order parts, contact suppliers or operate hardware.

The sourced successor is generated from `candidate/cad/` and `SOURCES.json`.
All 175 factory references / 86 unique catalog parts have verified public JLC
purchase/preorder paths. All 29 missing reference assignments were filled using
the exact design MPNs. Five documented catalog/format aliases cover twelve other
references. None of the circuit values, MPNs, footprints, models or routes changed.

Fresh KiCad 9.0.9 on the sourced project: ERC/DRC/unconnected/parity 0/0/0/0.
The full filled native tree, schematic nets, all native positions and fourteen
fabrication files are equivalent to the qualified baseline, apart from explicitly
listed procurement fields, property IDs and generation headers. Prior executed
SPICE, thermal, STEP and firmware evidence is retained without claiming reruns.

General search-engine coverage missed several valid JLC parts. The public search
endpoint used by the JLC website resolved the final seven exact MPNs (eight
references); sanitized search receipts are in `catalog_search/`. Detail-page
responses and identity/orderability extracts are in `catalog/`. TDK apparent
MPN differences were resolved using exact distributor alias fields and TDK's
catalog-versus-label naming notice; do not reintroduce unresolved sourcing gates
for them. No general suffix stripping is permitted.

Build and verification commands are in README.md. Current manufacturing entry is
`product/PRODUCT_HANDOFF.md`; current source is the generated native project in
`current/i32_sourced_manufacturing/editable_source/cad/`. The old package remains
historical. All factory requests are catalog-only; preorders, inventory/attrition
allocation and supplier process approval remain open. F101/U401 stay local;
exact GPS module supply/receiving acceptance and physical qualification are open.

Local verification completed: seven procurement/fabrication regression tests;
current package with 368 ZIP members; 2,774 indexed paths; all fourteen retained
desktop gates and byte-identical prior aggregate/package reproduction. The
catalog snapshot lists 34 factory references / 26 unique parts requiring preorder.
Next action is append-only publication to PR #46 and hosted verification.
