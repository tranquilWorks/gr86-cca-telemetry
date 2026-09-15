# I32 sourced ECAD and manufacturing package

**All 175 factory references have verified JLC catalog assignments.** All 29
previously missing assignments are resolved with the exact specified MPNs. Both
native schematics and PCB carry the assignments, source URLs and supplier MPNs.
KiCad 9.0.9 regenerates the BOM, CPL, schematic PDF/XML, Gerbers and drills.
Supplier acceptance and physical qualification remain open; no order is placed.

## Files to use

- `editable_source/cad/GR86_CCA_RevB.kicad_pro`: current sourced native project.
- `assembly/COMPLETE_FITTED_BOM.csv`: all 177 fitted references exported from the schematic.
- `assembly/PROCUREMENT_BOM.csv`: all 177 references with source and acceptance status.
- `assembly/PROCUREMENT_REDLINE.csv`: every new assignment and documented identity alias.
- `assembly/JLCPCB_BOM.csv` and `assembly/JLCPCB_CPL.csv`: the same 175 factory references, with no blank JLC codes.
- `assembly/PREORDER_REQUIREMENTS.csv`: factory parts with zero stock in the captured JLC snapshot.
- `assembly/LOCAL_ASSEMBLY_BOM.csv`: F101 and U401 only.
- `assembly/DO_NOT_POPULATE.json`: C203, R301 and R306 remain DNP.
- `fabrication/JLCPCB_GERBERS.zip`: regenerated fabrication outputs.
- `COHERENCE.json` and `SOURCE_MANIFEST.json`: scope and hashes for every package member.

In the repository these files live in `docs/engineering/rvb22/current/i32_sourced_manufacturing/`.
The archive is `docs/engineering/rvb22/product/GR86_I32_SOURCED_MANUFACTURING.zip`.

## Exact parts and documented aliases

Every factory part has a JLC catalog purchase/preorder path at the retained
snapshot. No factory part uses Global Sourcing or consignment. The public catalog
search, rather than general web-search coverage, resolved the final exact MPNs.
The generated redline lists all 29 new assignments. No component value, MPN,
footprint, package model, placement or route was substituted in this continuation.

Five part-specific spelling mappings cover twelve references: three TDK catalog
numbers versus packaging-label item descriptions, F1's leading zero and R104's
separator. `SupplierMPN` records the catalog spelling while `MPN` retains the
qualified design identity. The JLC import uses the verified supplier spelling.
`IDENTITY_ALIASES.md` records the evidence; arbitrary suffix/punctuation stripping
is rejected. All 13 frozen substitution references retain their exact MPN/C-number
bindings.

## Engineering binding

The maintained inputs are the qualified `candidate/cad/` circuit/geometry and
`analyses/i32/procurement_completion/SOURCES.json` procurement decisions.
`build.py prepare` generates the sourced native project. Edit those maintained
inputs and regenerate; do not hand-edit generated copies.

Only `LCSC`, `ProcurementRoute`, `ProcurementURL` and `SupplierMPN` may differ.
Complete parsed-tree comparisons protect all values, MPNs, connections, pad and
route geometry, models, stackup, rules and the 49 special vias. Fresh native ERC,
DRC, unconnected and schematic/PCB parity checks are zero. The filled PCB is
identical after removing procurement fields and regenerated property IDs. All
14 fabrication files match the qualified outputs apart from generation headers;
the complete native placement table and schematic nets also match.

The existing populated STEP, 32/32 electrical cases, 17/17 normal sequences,
thermal results and 160 MHz firmware build are carried forward through this
exact physics comparison. **No new SPICE, thermal solver, component STEP export
or firmware build is claimed.** Historical executed evidence remains in
`analyses/i32/procurement_redline/` with its original source binding.

## Reproduction in the repository

```sh
python docs/engineering/rvb22/analyses/i32/procurement_completion/build.py prepare
# Use KiCad 9.0.9 and its matching Python pcbnew bindings; choose a new output directory.
python docs/engineering/rvb22/candidate/run_native_candidate.py \
  --cad-dir docs/engineering/rvb22/current/i32_sourced_manufacturing/editable_source/cad \
  --output /tmp/gr86-sourced-native --pcbnew-python /usr/bin/python3
python docs/engineering/rvb22/analyses/i32/procurement_completion/build.py package \
  --native-dir /tmp/gr86-sourced-native
python docs/engineering/rvb22/analyses/i32/procurement_completion/build.py verify \
  --native-dir /tmp/gr86-sourced-native
```

The committed native run is in `analyses/i32/procurement_completion/native/`.
Omit `--native-dir` to verify it. Package ZIPs use deterministic member timestamps.
JLC responses and extracts are retained in `catalog/` beside the script and in
`sourcing_evidence/catalog/` inside the package. Verification makes no network
calls. The pinned Docker image and native execution scope are in
`NATIVE_TOOLCHAIN.json`; CI repeats the sourced native run.

## Remaining ordering gates

Catalog assignment is complete. Purchase the required preorders and obtain
supplier confirmation of build quantities/attrition, inventory allocation,
handling, orientation, stackup, via fill/cap/planarization, minimum plating and
stencil before ordering assembly. Stock snapshots do not reserve inventory.
See `ASSEMBLY_AND_ACCEPTANCE.md` for the retained construction requirements.
F101 and U401 remain local installs; exact PA1616D supply/receiving acceptance is
still required. Physical fit, thermal/loss correlation, bench electrical/EMC and
vehicle testing remain open. Nothing has been purchased, submitted to a supplier
or merged.
