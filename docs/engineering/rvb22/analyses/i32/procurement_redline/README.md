# I32 procurement redline — completed desktop verification

The frozen procurement set is applied to the actual native candidate, with regenerated assembly/fabrication outputs. All 14 requested desktop gate categories pass within the declared model and supplier-catalogue scope. This is not an order authorization, supplier acceptance, hardware validation or full-product qualification.

The starting remote revision was `1c934f9ddd7a1b823e5136484f525485472528f6` on `codex/rvb24-coordinated-closure`, PR #46. The immutable pre-redline CAD commit is `e5ef8425dbe59c99e99eabb75c04342a47b27561`. Its four subsequent evidence/handoff commits remain ancestors. The final publication commit is the commit containing this report; the PR publication record identifies the remote SHA without a self-referential file hash.

Current authority is [FINAL_REDLINE_VERIFICATION.json](FINAL_REDLINE_VERIFICATION.json), [SOURCE_BINDING.json](SOURCE_BINDING.json), and [the manufacturing manifest](../../../current/i32_manufacturing/SOURCE_MANIFEST.json). [CHANGED_PATHS.md](CHANGED_PATHS.md) enumerates every changed CAD, model, manufacturing and evidence path. Original current records are preserved under `history/pre_redline/`; existing experiment history and the controlling readiness/handoff documents remain intact.

| Native artifact | SHA256 |
|---|---|
| Authored PCB | `52ca35cf8cb4e2b4a27d053686ee3a85564f1e94dfdb7dcb4bca4083dd527312` |
| KiCad filled PCB | `896ca56bf4ad836d63b84537cfd20bfcbf1783c60ac5d92ab7c7783d54f57e92` |
| Native schematic XML | `3a3ac0ad2e7acc75bd5690a128a7d47e28859e017c66fe01276025dfa7dda93d` |

## Exact substitutions

| References | Frozen MPN | JLC/LCSC | Package |
|---|---|---|---|
| C152,C154,C165 | CGA3E3X7R1H224KT0Y0N | C342967 | 0603 |
| L121 | BPCI00121280470M00 | C6471075 | 12 × 12 mm SMD |
| R155 | PTFR0603B11K8N9 | C19679768 | 0603 |
| R156 | PLT1206Z5051LBTS | C4074185 | **1206** |
| R160 | RT0805BRB076K34L | C864499 | **0805** |
| R161,R163,R170 | PTFR0603Q1K00N9 | C23067434 | 0603 |
| R162 | PTFR0603Q4K70N9 | C23067437 | 0603 |
| R169 | PTFR0603B3K01N9 | C2692830 | 0603 |
| U101 | LTC4367HMS8#PBF | C688370 | MSOP-8 |

U101 remains the H-grade electrical device. The owner accepts losing the **#W controlled-manufacturing ordering pedigree**. The #PBF pedigree is not equivalent. This acceptance is recorded in the native schematic and PCB properties. F101 and U401 remain unchanged local/manual installations. No unrelated MPN was substituted. R151's previously missing PCB LCSC field was reconciled to the already-existing schematic/BOM value C190124; all its electrical and physical properties are unchanged.

## Physical and model changes

All 13 frozen references use checked `RevB:I32_PROCUREMENT_<ref>` footprints. Manufacturer documents, exact file hashes, pad/net checks, body dimensions, mask/paste membership and model distinctions are in [PACKAGE_QUALIFICATION.json](PACKAGE_QUALIFICATION.json). Nine new STEP files are dimensionally correct generic maximum-body envelopes, explicitly not vendor CAD. Existing capacitor and MSOP generic models remain, with maximum body/tolerance covered in the mechanical check. All 177 fitted models resolve in the populated STEP export.

| Ref | Native placement (mm, degrees) | Physical change |
|---|---|---|
| R156 | B.Cu, (41.25, 10.101), −90° | 0603 → 1206. Vishay 60119 lands: 0.9144 × 1.7018 mm at ±1.524 mm. Maximum body 3.4032 × 1.7272 × 0.8382 mm; courtyard 4.5 × 2.25 mm. Ground-pad centre retained at (41.25, 11.625). Added 0.25 mm feedback copper to the moved pad. |
| R160 | F.Cu, (27.0, −7.5), 0° | 0603 → 0805. Lands 1.0 × 1.45 mm at ±1.025 mm; maximum body 2.1 × 1.35 × 0.6 mm. Courtyard 3.55 × 1.95 mm. Centre/orientation unchanged. |
| L121 | F.Cu, (59.8, 29.05), 90° | Replaced Coilcraft-specific pattern with the BPCI manufacturer pattern: 5.4 × 2.8 mm pads, 7 mm inner gap, 9.8 mm centre spacing, 12.6 mm outer span. Maximum body 12.5 × 12.5 × 8 mm; 13.1 mm courtyard. Moved −0.2/+0.05 mm to preserve nearby protected clearances. |
| R155 | B.Cu, (44.0, 10.8), 90° | Qualified PTFR lands; shifted −0.55 mm in X for package spacing. |
| R169 | B.Cu, (79.8, 1.7), 0° | Qualified PTFR lands; shifted −0.2/−0.3 mm. |
| R170 | B.Cu, (83.2, 1.7), 0° | Qualified PTFR lands; shifted −0.1/−0.3 mm. |

R161/R162/R163 also receive the actual PTFR pattern: 0.9 × 1.2 mm pads at ±0.95 mm, within the manufacturer's dimensional land-pattern range. The same-package capacitor and U101 substitutions preserve pad sizes and pin/net identity. Pads, paste, mask, courtyards, copper/via clearances and native orientation are checked for all changed references.

Routing moves the 3V3_ENABLE left leg to X25.1 and crossbar to Y−8.6; the 3V3_VIN sense crossbar to Y−5.0; and the 5V_RIPPLE leg to X53.1375. The LED_OIL ordinary 0.6/0.3 mm via moves from (41.1, 8.3) to (38.3, 8.9), with its B.Cu and In2.Cu connections rerouted. These changes clear enlarged pads while preserving all pad nets. The source audit records one added segment, 18 modified copper objects, no removed copper objects and no added or removed vias. All 49 special vias, stackup, custom clearances and rules remain unchanged. The complete UUID-level delta is in [SOURCE_AUDIT.json](SOURCE_AUDIT.json); annotated route views are in `layout/`.

## Verification and manufacturing

| Gate | Result and retained evidence |
|---|---|
| Native KiCad 9.0.9 | ERC 0, DRC 0, unconnected 0, schematic/PCB parity 0, exclusions 0; 13/13 output postconditions. `native_final/` |
| Exact source | 157 CAD files bound; 32 firmware files unchanged. Original GPIO, receive-only CAN, RF, GPS and oil signal contracts retained. `SOURCE_AUDIT.json` |
| Independent copper/export reconstruction | PASS across 145 nets and 571 net-bearing pads, with no disconnected pad nets or pad/net mismatches; Gerber flashes/traces/fills and drill exports matched. `manufacturing_audit_final/` |
| Explicit source copper | Zero new/worsened foreign-net gaps below 0.15 mm, zero prior pad-connectivity regressions and no unsupported primitives. `EXPLICIT_COPPER_FINAL.json` plus exact metadata rebind |
| Power returns | 23/23 actual-filled ground pairs connected. Source return 11.282 mΩ against 15 mΩ; C206 allocation 10.919 mΩ against 11 mΩ. `filled_returns_final/`, `ground_final/` |
| Packages/models | 13/13 exact identities, pad nets, lands, models and mask/paste memberships checked. `PACKAGE_QUALIFICATION.json` |
| BOM/CPL | 177 fitted; 175 factory CPL rows; F101/U401 local; C203/R301/R306 DNP. Every frozen ref has its exact MPN/C-number; zero old frozen MPNs in active BOM. `MANUFACTURING_RECONCILIATION.json` |
| Manufacturing | 11 Gerber layers, 2 drill files, 1 job file; IPC-D-356, schematic PDF/XML, populated STEP, 49-via list and editable CAD copy regenerated. `current/i32_manufacturing/` |
| Mechanical | 1,308 populated checks, 529 mated checks, 38 probe approaches; no modeled interference. Full 1.71 mm height stack; minimum allocated clearance 0.120 mm. `mechanics_final/` |
| Analysis binding | 16 existing native-binding unit tests passed. Full filled-tree comparison preserves every physical/model token and native filled polygon across the final descriptive cleanup. `NATIVE_BINDING_TESTS.log`, `METADATA_ONLY_REBIND.json` |

Native CPL coordinates use the retained auxiliary origin (0, 41.288863) mm. R156: Bottom, X41.25/Y31.187863, −90°; R160: Top, X27/Y48.788863, 0°; L121: Top, X59.8/Y12.238863, 90°. All 175 rows reconcile against native reference, side, X/Y and rotation. Supplier feeder/pin-one and bottom-side interpretation remain assembly setup acceptance items.

The factory list contains **29 unchanged references without assigned LCSC codes**, enumerated in `assembly/SOURCING_REQUIRED.csv`. This redline resolves the frozen set; it does not authorize opportunistic substitutions or claim that the entire BOM is turnkey-order-ready.

## Fresh electrical replay

The recovered final-procurement ngspice 42/KLU runner completed 32/32 swap/stress cases and 6/6 controls; all 17 normal cases sequenced correctly. All 38 full waveform records are retained losslessly as gzip, with compressed and decompressed hashes in `spice/RAW_RECORD_MANIFEST.json`. 38 large gzip files are stored as exact byte parts of at most 8 MiB; `python restore_waveforms.py --restore` reconstructs them after checking each part, the complete compressed stream and the decompressed waveform hashes. No waveform samples or precision are discarded. Executed scripts, decks, solver logs and results are retained; the prior hosted qualification run remains 34899316734. No acceptance threshold was relaxed.

| Metric | Final result |
|---|---|
| Worst normal 3.3 V minimum | 3.12786634 V |
| Reset limit / margin | 3.116050 V / **+11.81634 mV** |
| Maximum rail / margin below 3.600 V | 3.57660977 V / **+23.39023 mV** |
| 1 µs-resolution high-side confirmation | 3.5766084 V |
| Worst reverse allocation | −0.06700731 V against −0.3 V |
| L121 peak / conservative saturation allocation | 0.942206123 A / 2.5 A |
| 30.08 µH superstress | PASS |

This uses the recovered transparent current-mode derivative model, not a final vendor-macromodel or hardware-validation claim. U101's electrical model is unchanged; unchanged input protection and signal-domain results remain applicable through the audited source contracts. The −55/155 °C inductor DCR corners are deliberate superstress, not an extension of its −40…125 °C operating rating.

SPICE and thermal runs bind to authored PCB `177454910e8699749c42599a13c613f3155a52760af65763f2c7982ffec90e66`, after the physical redline. Subsequent changes only corrected footprint descriptions/tags, R151's existing catalogue code and a README rail label. The full native tree, including every filled polygon and model, is identical after excluding precisely those fields and native-generated property UUIDs. Their original hashes/results are preserved; `METADATA_ONLY_REBIND.json` explicitly binds them to the final descriptive source. Native CAD, mechanical, ground and manufacturing checks ran again on the final source.

## Thermal and physical boundaries

The 0.5/0.25 mm actual-copper runs use the adopted C05/W02/T03 cooling and unchanged 2.940859375 W release budget. Fine result plus one positive coarse-to-fine difference gives 113.271698 °C for the same-budget allocation and 113.763359 °C for the stacked 80%-efficiency sensitivity. This is a mesh allowance, not demonstrated convergence. The historical **112.8829809018675 °C correlation trigger is unchanged**; exceeding it requires physical correlation. At U151 exactly 80%, the worst leakage allocation requires U121 efficiency at least 83.4631% or an approved measured-loss alternative within the same budget. No losses were silently scaled away.

Conditional U152/U153 junction screens are 105.7765/105.6562 °C against 130 °C using the retained 51 K/W allocation and fresh peak dissipation. The R156/R169 global board screen is 11.2366 °C below 125 °C. L121's conservative peak-as-RMS screen, using the manufacturer's typical rated-current temperature-rise definition and copper temperature feedback, is 121.6020 °C, 3.3980 °C below its 125 °C limit including self-rise. These conditional allocations require measured package-temperature and loss correlation. They are not guaranteed vendor thermal models, package measurements or evidence of immediate-air temperature.

Remaining physical gates include first-article assembly and populated/mated fit, C166 edge tolerance, probe access, material/contact/retention/fatigue acceptance, package and cooling-temperature correlation, bench electrical/transient/EMC tests, installed vehicle validation and unit acceptance. Retain the I25 workload, 65 °C cabin, U201 immediate air ≤85 °C and Adafruit 851 local environment ≤60 °C. No board was ordered, flashed, assembled or tested during this redline.

## Live frozen-source snapshot

The public exact JLC catalogue records were retrieved on 2026-09-14 at approximately 23:01–23:04 UTC and are retained in [LIVE_JLC_SOURCEABILITY.json](LIVE_JLC_SOURCEABILITY.json). All nine exact MPN/C-number pairs expose stock purchase or preorder paths. No stock or assembly capacity is reserved.

| C-number | Stock snapshot | Preorder minimum | Catalogue process |
|---|---:|---:|---|
| C342967 | 3,670 | 390 | SMT |
| C6471075 | 0 | 35 | Manual/wave |
| C19679768 | 3,984 | 85 | SMT |
| C4074185 | 0 | 2 | SMT |
| C864499 | 0 | 72 | SMT |
| C23067434 | 12,948 | 19 | SMT |
| C23067437 | 6,817 | 20 | SMT |
| C2692830 | 317 | 66 | SMT |
| C688370 | 2 | 2 | SMT |

[JLC's L121 listing](https://jlcpcb.com/partdetail/C6471075) identifies manual/wave handling. L121 remains factory-supplied in the 175-row CPL; this is not proof that all 175 rows are machine SMT placements, nor a third local-install exception. Supplier process/orientation approval, the 29 unchanged sourcing assignments, exact stackup/plating/special-via/stencil DFM and physical qualification remain before ordering.

## Reproduction

Use native KiCad 9.0.9 and the dependencies pinned in `requirements.txt`. The native workflow binds the current authored source explicitly and retains its existing CAD and 160 MHz firmware gates. Run `candidate/run_native_candidate.py` against `candidate/cad` with `--component-step`; the native runner refuses incomplete outputs. Run `analyses/i32/source_audit.py --help` and use `--procurement-redline` with the explicit source and filled hashes. Run the existing native export, layout, filled-ground, ground-return, mechanical and thermal checkers against those same native outputs. The authored candidate is authoritative; one-shot historical authoring recipes must not be reapplied over it.

`final_procurement_spice_qual.py` reruns the frozen suite into a new `I32_PROCUREMENT_SPICE_OUT` directory; it refuses an existing output directory. `spice/replay_source/` preserves the scripts actually executed for this result. The common runner's later default-bound cleanup matches the already-executed final wrapper and does not change those executed decks. `finalize_redline.py` validates evidence and the exact metadata rebind before writing the aggregate. `generate_manufacturing.py` regenerates the package from the verified `native_final/` source/export inventory.

Historical failed intermediate native checks are retained in `history/` and are not accepted results. The current native, manufacturing and source records are named `native_final/`, `manufacturing_audit_final/`, `SOURCE_AUDIT.json` and `FINAL_REDLINE_VERIFICATION.json`.
