# I32 redline resumption verification — 2026-09-15

The frozen procurement redline was already complete and published when this session began. Its actual source, preserved execution evidence and release package have now been reverified. The exact nine-part JLC catalogue check was refreshed. This follow-up adds verification records only; the CAD, models, BOM/CPL and manufacturing outputs are unchanged.

- Repository / branch: `tranquilWorks/gr86-cca-telemetry` / `codex/rvb24-coordinated-closure`; PR #46 remains open and unmerged.
- Starting remote revision for this resumption: `0b4e3f8ef5d1535733990305315445d19c4ac5c2`.
- Original redline starting remote: `1c934f9ddd7a1b823e5136484f525485472528f6`.
- Engineering publication: `1ce3f9f9b8bdb68dc275334d22b63dd21d40e058`.
- Immutable CAD baseline: `e5ef8425dbe59c99e99eabb75c04342a47b27561`; it and all four handoff commits are preserved.
- Final publication revision: the commit containing this record, reported after remote readback.

## What was verified in this resumption

`ci_verify.py` passed with 2,006 indexed paths, 157 CAD inputs, 32 unchanged firmware files, 38 preserved waveform records, all 14 aggregate desktop gate categories and byte-identical aggregate reproduction. The release ZIP contains 188 verified members; its SHA256 remains `9a8fc224474f7744d2c8c46fdd7c82f6f1d414a18e7612d65a40dc281d79f0c5`.

`source_audit.py --procurement-redline` passed. SOURCE_AUDIT.json and SOURCE_BINDING.json reproduce byte-for-byte. The checkout remained clean after both checks. All eight hosted workflows passed on the exact starting revision; the two native workflows and evidence/package workflow job steps were checked, and native/source and package log identities were read back. See [verification record](VERIFICATION.json), [local reproduction](LOCAL_EVIDENCE_REPRODUCTION.json) and [hosted results](HOSTED_WORKFLOW_READBACK.json).

Native KiCad and ngspice were not rerun in this resumption. The existing post-redline executions remain applicable because no active circuit, model or physical source changed. The local recheck verifies that binding and retained results; it does not relabel an earlier execution as a new test.

## Final substitutions and refreshed JLC snapshot

All nine exact MPN/C-number records expose public purchase or preorder paths. The snapshot is dated by each response in [LIVE_JLC_SOURCEABILITY.json](LIVE_JLC_SOURCEABILITY.json). Six have stock; L121, R156 and R160 require preorder. Quantities are per-part catalogue snapshots.

| References | Exact MPN | JLC/LCSC | Package | Stock | Preorder minimum |
|---|---|---|---|---:|---:|
| C152,C154,C165 | `CGA3E3X7R1H224KT0Y0N` | [C342967](https://jlcpcb.com/partdetail/C342967) | 0603 | 3670 | 390 |
| L121 | `BPCI00121280470M00` | [C6471075](https://jlcpcb.com/partdetail/C6471075) | SMD,12x12mm | 0 | 35 |
| R155 | `PTFR0603B11K8N9` | [C19679768](https://jlcpcb.com/partdetail/C19679768) | 0603 | 3964 | 85 |
| R156 | `PLT1206Z5051LBTS` | [C4074185](https://jlcpcb.com/partdetail/C4074185) | 1206 | 0 | 2 |
| R160 | `RT0805BRB076K34L` | [C864499](https://jlcpcb.com/partdetail/C864499) | 0805 | 0 | 72 |
| R161,R163,R170 | `PTFR0603Q1K00N9` | [C23067434](https://jlcpcb.com/partdetail/C23067434) | 0603 | 12905 | 19 |
| R162 | `PTFR0603Q4K70N9` | [C23067437](https://jlcpcb.com/partdetail/C23067437) | 0603 | 6642 | 20 |
| R169 | `PTFR0603B3K01N9` | [C2692830](https://jlcpcb.com/partdetail/C2692830) | 0603 | 317 | 66 |
| U101 | `LTC4367HMS8#PBF` | [C688370](https://jlcpcb.com/partdetail/C688370) | MSOP-8 | 2 | 2 |

JLC labels L121 as manual/wave handling. It remains a factory-supplied CPL placement, subject to supplier process and orientation acceptance; it is not a third local-install exception. The CPL count is 175 factory placements, not a claim of 175 automatic SMT placements. F101 and U401 remain the two local installations. U101 retains the owner-accepted loss of #W controlled-manufacturing pedigree; pedigree equivalence is not claimed.

The first parser pass encountered four missing optional `noBuyReason` fields. Those failures are preserved in [LIVE_JLC_FIRST_ATTEMPT.json](LIVE_JLC_FIRST_ATTEMPT.json). The corrected extraction uses explicit purchase/preorder flags and separately records whether the optional field exists. All four retries passed exact-identity and availability checks. No component was changed.

## Physical redline and output reconciliation

- R156 uses the qualified 1206 footprint on B.Cu at (41.25, 10.101) mm, -90 degrees; its ground-pad centre is retained and feedback copper reaches the relocated pad.
- R160 uses the qualified 0805 footprint on F.Cu at (27, -7.5) mm, 0 degrees.
- L121 uses the manufacturer BPCI lands (5.4 x 2.8 mm pads, 7 mm inner gap) on F.Cu at (59.8, 29.05) mm, 90 degrees, with the 12.5 x 12.5 x 8 mm maximum body envelope.
- R155, R169 and R170 were shifted for clearance. The other PTFR lands, 13 changed reference identities and nine new generic STEP envelopes are qualified in the existing package record.
- One copper segment was added and 18 copper objects modified; no copper objects were removed. One ordinary LED_OIL via was moved with its connections. The 49 special vias, stackup and native rules remain unchanged.
- ERC 0; DRC 0; unconnected 0; schematic/PCB parity mismatches 0; exclusions 0. Independent export reconstruction covers 145 nets and 571 net-bearing pads.
- 177 fitted placements; 175 factory BOM/CPL rows; 2 local installations; C203/R301/R306 remain DNP. All 13 changed references bind to the frozen MPN/C-number; no old frozen MPN remains in the active BOM.
- CPL side, X/Y and rotation reconcile against native source. R156: Bottom, 41.25/31.187863 mm, -90 degrees. R160: Top, 27/48.788863 mm, 0 degrees. L121: Top, 59.8/12.238863 mm, 90 degrees.

## Retained post-redline electrical and thermal results

32/32 swap/stress cases and 6/6 controls completed under ngspice 42/KLU; all 17 normal cases sequenced correctly. Minimum 3.3 V: 3.12786634 V against a 3.116050 V reset limit, giving +11.81634 mV. Maximum: 3.57660977 V, giving +23.39023 mV below 3.600 V. The 1 us high-side confirmation is 3.5766084 V. Worst reverse allocation: -0.06700731 V. L121 peak: 0.942206123 A against 2.5 A; 30.08 uH superstress passes. These are model results, not hardware measurements.

The fixed release heat budget remains 2.940859375 W. The stacked board screening result is 113.763359283458 C; the historical 112.8829809018675 C physical-correlation trigger is unchanged. L121 conditional winding screening is 121.60197565712534 C against 125 C, a 3.3980243428746633 C margin. Physical temperature and loss correlation remain required; mesh convergence and measured junction/immediate-air temperatures are not claimed.

## Changed CAD/model/manufacturing paths

The complete original engineering/evidence inventory is [CHANGED_PATHS.md](../CHANGED_PATHS.md), with hashes and sizes in [CHANGED_PATHS.json](../CHANGED_PATHS.json). This includes every regenerated manufacturing, model, BOM/CPL and analysis path. The 29 native CAD/model paths changed by the redline are:

- `docs/engineering/rvb22/candidate/cad/CANDIDATE_README.md`
- `docs/engineering/rvb22/candidate/cad/GR86_CCA_RevB.kicad_pcb`
- `docs/engineering/rvb22/candidate/cad/Input_Protection.kicad_sch`
- `docs/engineering/rvb22/candidate/cad/Power_3V3.kicad_sch`
- `docs/engineering/rvb22/candidate/cad/Power_5V.kicad_sch`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.kicad_sym`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_FINISHED_R151.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_C152.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_C154.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_C165.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_L121.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R155.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R156.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R160.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R161.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R162.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R163.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R169.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_R170.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/libraries/RevB.pretty/I32_PROCUREMENT_U101.kicad_mod`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_L121.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R155.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R156.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R160.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R161.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R162.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R163.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R169.step`
- `docs/engineering/rvb22/candidate/cad/models/ENVELOPE_I32_PROCUREMENT_R170.step`

The [manufacturing source manifest](../../../../current/i32_manufacturing/SOURCE_MANIFEST.json) binds the generated outputs. The [release ZIP](../../../../product/GR86_I32_PROCUREMENT_REDLINE.zip) is unchanged and verified. This resumption adds only the files in its own directory.

## Remaining supplier and physical gates

29 unchanged factory references still lack LCSC assignments in the release BOM and remain listed in SOURCING_REQUIRED.csv. The frozen substitutions are resolved; the whole board is not turnkey-order-ready. JLC must accept L121 handling/orientation and the specified stackup, finished plating, filled/capped/planarized vias and stencil/assembly process.

First-article fit and assembly, C166 edge tolerance, probe access, cooling materials/contacts, converter losses and thermal correlation remain open. Retain the I25 workload, 65 C cabin, U201 immediate air <=85 C and Adafruit 851 local environment <=60 C limits. Bench startup/brownout/reset/reverse-protection and EMC/transient tests, vehicle validation and unit acceptance remain physical gates. No order, hardware flash, physical measurement or PR merge occurred.
