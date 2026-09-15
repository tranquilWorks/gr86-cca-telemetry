# GR86 / BRZ Telemetry CCA Rev B — I32 Procurement Redline Execution Handoff

## Mission

Resume `tranquilWorks/gr86-cca-telemetry` on existing PR **#46**, branch:

`codex/rvb24-coordinated-closure`

Apply the **already frozen and electrically qualified procurement substitutions** to the real I32 schematic/PCB source, component metadata/models, footprints, placement/routing as required, BOM, PnP/CPL and manufacturing outputs. Then rerun the complete applicable native/source/manufacturing/electrical verification stack.

Do **not** restart component selection. Do **not** reopen the already-qualified substitutions unless an exact frozen MPN becomes genuinely unavailable or a physical CAD/package conflict proves it unusable.

Do not stop at a plan. Carry the redline through source update, regenerated outputs and verification.

## Mandatory start procedure

1. Fetch the **latest remote tip** of `codex/rvb24-coordinated-closure` and inspect current status before editing.
2. Preserve all newer work. Do not hard-reset, recreate the branch, or restore an older bundle over the current source.
3. The immutable **pre-redline CAD baseline** is commit:
   `e5ef8425dbe59c99e99eabb75c04342a47b27561`
4. Commits after that baseline currently publish procurement/readiness evidence only. Verify that fact from the actual Git history before starting CAD mutation.
5. Read these source-of-truth records first:
   - `docs/engineering/rvb22/I32_REDLINE_READINESS_FINAL.md`
   - `docs/engineering/rvb22/I32_REDLINE_READINESS_FINAL.json`
   - `docs/engineering/rvb22/analyses/i32/FINAL_PROCUREMENT_QUALIFICATION.json`
6. Qualification/replay source is preserved on branch `agent/i32-jlc-substitution-spice`:
   - `docs/engineering/rvb22/analyses/i32/substitution_spice_qual.py`
   - `docs/engineering/rvb22/analyses/i32/final_procurement_spice_qual.py`
   - final hosted run `34899316734`

The current CAD source is under:

`docs/engineering/rvb22/candidate/cad/`

Primary files include the hierarchical root `GR86_CCA_RevB.kicad_sch`, board `GR86_CCA_RevB.kicad_pcb`, `Power_5V.kicad_sch`, `Power_3V3.kicad_sch`, and the other hierarchical sheets. Locate each reference from the real native source rather than assuming a sheet from historical notes.

## Frozen substitutions — DO NOT SUBSTITUTE AGAIN WITHOUT EVIDENCE

| Refs | Current part | Frozen replacement | JLC/LCSC | Final package | Electrical status |
|---|---|---|---|---|---|
| C152,C154,C165 | `CGA3E3X7R1H224K080AB` | `CGA3E3X7R1H224KT0Y0N` | `C342967` | 0603 | PASS; same 220 nF / 50 V / X7R / ±10% electrical family |
| L121 | `MSS1246T-473MLC` | `BPCI00121280470M00` | `C6471075` | 12x12 mm SMD | PASS full transient; 30.08 µH superstress PASS; peak 0.9422 A vs 2.5 A Isat |
| R155 | `TNPU060311K8HWEA00` | `PTFR0603B11K8N9` | `C19679768` | 0603 | PASS |
| R156 | `TNPU06035K05HWEA00` | `PLT1206Z5051LBTS` | `C4074185` | **1206** | PASS exact final candidate; 5.05 kΩ ±0.01%, 5 ppm/°C |
| R160 | `TNPU06036K34HWEA00` | `RT0805BRB076K34L` | `C864499` | **0805** | PASS exact final candidate; 6.34 kΩ ±0.1%, 10 ppm/°C |
| R161,R163,R170 | `TNPU06031K00HWEA00` | `PTFR0603Q1K00N9` | `C23067434` | 0603 | PASS |
| R162 | `TNPU06034K70HWEA00` | `PTFR0603Q4K70N9` | `C23067437` | 0603 | PASS |
| R169 | `TNPU06033K01HWEA00` | `PTFR0603B3K01N9` | `C2692830` | 0603 | PASS exact final candidate |
| U101 | `LTC4367HMS8#WTRPBF` | `LTC4367HMS8#PBF` | `C688370` | MSOP-8 | PASS functionally; owner explicitly accepts loss of `#W` controlled-manufacturing pedigree |

Explicit non-substitution/local-assembly exceptions:

- **F101:** unchanged; local/manual install.
- **U401 PA1616D GPS:** unchanged; local/manual install; intentionally excluded from JLC substitution mission.

All other exact BOM parts were already inventoried as JLC-stocked or JLC-preorderable/sourceable. Do not replace them opportunistically during this redline.

## Proven electrical envelope

The exact final procurement set was freshly executed under ngspice 42/KLU using the recovered I32 31-case selected transient matrix plus the additional L121 superstress case.

Final result: **PASS**.

- 32/32 swap/stress cases completed.
- 17/17 normal cases: exactly one READY rise, zero SNS faults, final READY asserted.
- Worst normal rail minimum: **3.12786634 V**.
- Reset floor: **3.116050 V**.
- Reset margin: **+11.81634 mV**.
- Worst rail maximum: **3.57660977 V**.
- 3.600 V headroom: **+23.39023 mV**.
- 1 µs-resolution upper confirmation: **3.5766084 V**.
- Worst VIN-minus-source: **-0.06700731 V**, versus -0.300 V allocation.
- L121 peak current: **0.942206123 A** versus **2.5 A** Isat.
- L121 30.08 µH out-of-spec superstress: **PASS**.

Do not weaken these limits. If the CAD redline changes electrical values/connectivity beyond the frozen part substitutions, rerun and re-evaluate rather than inheriting the pass.

## Required CAD redline work

### 1. Schematic/component metadata

For every frozen substitution:

- update fitted `Value`/MPN fields where the repository convention uses them;
- update JLC/LCSC/C-number fields;
- update datasheet/manufacturer metadata;
- update tolerance/TCR/rating metadata where represented;
- keep reference designators and electrical nominal values correct;
- ensure hierarchical schematic and PCB instance metadata agree;
- remove stale old-MPN references from active release data while preserving historical evidence files.

For U101, preserve a release note that `LTC4367HMS8#PBF` is electrically accepted but is **not** claimed equivalent to the `#W` automotive controlled-manufacturing ordering option.

### 2. Footprints and physical models

#### R156

Change from the current 0603 implementation to a **1206** land pattern suitable for `PLT1206Z5051LBTS / C4074185`.

Verify:
- manufacturer/package dimensions;
- pad geometry and solder fillet allowance;
- courtyard and component-to-component clearance;
- solder mask/paste apertures;
- orientation and pin/net continuity;
- nearby routing/via clearance;
- JLC assembly compatibility.

#### R160

Change from 0603 to **0805** for `RT0805BRB076K34L / C864499` and perform the same physical checks.

#### L121

Replace the Coilcraft-specific physical implementation with a qualified land pattern for `BPCI00121280470M00 / C6471075`.

The candidate is approximately 12x12 mm. Use manufacturer dimensional/land-pattern data where available. Do not scale or guess the old footprint.

Verify especially:
- copper/pad size;
- courtyard and height;
- switch-node / output-node geometry;
- hot-loop implications;
- clearance to adjacent parts/vias/tracks;
- mechanical fit;
- assembly orientation;
- no degradation of the already-reviewed power return path.

#### Other replacements

For same-package 0603/MSOP-8 substitutions, still verify the actual package suffix and footprint rather than assuming equivalence from the nominal package name.

Update 3D/package models where the repository maintains them. If an exact vendor 3D model is unavailable, use a dimensionally correct generic model and document that choice; do not fabricate geometry evidence.

### 3. Simulation/model metadata

Update active repository models/parameter records so they correspond to the frozen final procurement set:

- R155 11.8 kΩ: `PTFR0603B11K8N9`.
- R156 5.05 kΩ: `PLT1206Z5051LBTS`, ±0.01%, 5 ppm/°C.
- R160 6.34 kΩ: `RT0805BRB076K34L`, ±0.1%, 10 ppm/°C.
- R161/R163/R170 1 kΩ: `PTFR0603Q1K00N9`.
- R162 4.7 kΩ: `PTFR0603Q4K70N9`.
- R169 3.01 kΩ: `PTFR0603B3K01N9`, ±0.1%, 10 ppm/°C.
- L121: 47 µH ±20%, 100 mΩ max DCR at 25 °C, 2.5 A Isat/Irated; retain the documented hot-DCR and 30.08 µH superstress evidence.
- C152/C154/C165: same 220 nF / 50 V / X7R / ±10% electrical model.
- U101: retain LTC4367 H-grade behavioral model; change ordering identity/qualification note only.

After CAD/model edits, run the final procurement qualification again from the exact resulting source context. Do not simply cite the historical run if the active values/connectivity have changed.

### 4. Placement/routing

Because R156, R160 and L121 have physical changes, perform an actual placement/routing review rather than metadata-only substitution.

Preserve:
- existing net connectivity;
- power/current return paths;
- feedback/Kelvin intent;
- switch-node containment;
- creepage/clearance requirements;
- existing via/stackup requirements;
- all previously closed I32 engineering constraints unless the redline explicitly proves a necessary change.

If a larger package forces movement of adjacent components or traces, make the minimum controlled change and then re-run all geometry/electrical checks affected by that movement.

## BOM / PnP / manufacturing output requirements

Regenerate the actual release-facing outputs after the CAD changes.

Expected product semantics should remain:

- **177 fitted placements** unless a documented real design change requires otherwise.
- F101 and U401 remain explicit local/manual assembly exceptions.
- DNP set remains unchanged unless current source proves otherwise; historically C203/R301/R306 are DNP.
- Automatic placement count should remain consistent with the two local-install exceptions.

For the regenerated BOM:

- every frozen substitution must carry the exact MPN and C-number above;
- no old unavailable exact MPN should remain in active BOM rows;
- no blank/unassigned factory source field should remain for these substitution refs;
- local/manual parts must be intentionally labeled rather than appearing accidentally unsourceable;
- confirm JLC recognizes each final part and assembly/preorder path immediately before declaring orderability.

For regenerated PnP/CPL:

- validate reference, X/Y, side, rotation and package mapping for every changed footprint;
- specifically inspect R156, R160 and L121 orientation after footprint changes;
- ensure local-install F101/U401 are handled according to the existing manufacturing contract rather than silently entering factory placement.

Regenerate any repository-standard Gerber, drill, assembly, source manifest, review-table and output-check artifacts invalidated by the redline.

## Mandatory verification before completion

Do not declare redline complete until the actual updated source passes the applicable current repository gates.

At minimum:

1. Native KiCad schematic parse/ERC.
2. Native PCB DRC.
3. Zero unintended unconnected pads/nets.
4. Schematic ↔ PCB reference/value/net parity.
5. Footprint/package identity checks for every changed ref.
6. BOM source-binding and exact MPN/C-number checks.
7. BOM fitted/DNP/local-install count reconciliation.
8. PnP/CPL fitted-reference, side, coordinate and rotation reconciliation.
9. Manufacturing output regeneration and internal source/hash consistency.
10. Existing special-via/stackup constraints remain intact.
11. Existing I32 native/source audit scripts applicable to the changed source.
12. Fresh final-procurement ngspice replay after the redline; retain exact solver/version, deck hashes and result summary.
13. Re-run any thermal/package screen invalidated by material placement/package changes. R156/R169 are 125 °C-rated and the existing stacked board-region desktop screen is 113.697 °C; preserve first-article physical thermal correlation as a physical gate rather than claiming it was measured.
14. Live JLC sourceability/preorder check of the exact final MPN/C-number set.

Do not waive a gate just because the pre-redline simulation passed.

## Completion criterion

The redline milestone is complete when:

- all frozen substitutions are present in actual native schematic and PCB source;
- footprint changes are physically valid and routed cleanly;
- active models/metadata match the frozen procurement identities;
- regenerated BOM and PnP/CPL are internally consistent and JLC-resolvable;
- native ERC/DRC/connectivity/parity/manufacturing checks pass;
- the final exact procurement simulation remains PASS;
- no new desktop-actionable issue from the redline remains unresolved.

Physical first-article validation may remain, and must not be falsely claimed complete.

## Publication

Publish the completed redline to the existing `codex/rvb24-coordinated-closure` / PR #46 branch, preserving all newer work and evidence. Do not merge PR #46, place an order, flash hardware, or claim physical validation unless separately authorized.

At handoff completion report:

- starting remote SHA;
- final remote SHA;
- every changed CAD/model/manufacturing path;
- exact final BOM substitutions and C-numbers;
- footprint/placement changes;
- ERC/DRC/unconnected/parity results;
- BOM/PnP reconciliation counts;
- final ngspice margins;
- live JLC sourceability status;
- any remaining physical-only validation gates.
