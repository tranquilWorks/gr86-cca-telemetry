# Recovery addendum — 2026-09-14 UTC

**Digital closure update:** I32-RCV-FW-01 is closed by a genuine unchanged-source ESP32-S3 build at `CPUFreq=160`; the compiler log contains `-DF_CPU=160000000L` and all 28 preserved release checks pass. Evidence is under `recovery_20260914/firmware_160mhz/`. Historical 240 MHz images remain quarantined. Nothing was flashed or executed on hardware, and supplier, thermal-correlation, EMC, silicon, first-article, vehicle, and manufacturing-acceptance gates remain open.

---

# I32 coordinated power engineering

I32 adopts input isolation and source discharge, controlled bulk-capacitor charging and reset sequencing, measured routing/return allocations, and an automotive input clamp/diode/resistor correction. `FINAL_EVIDENCE.json` and `SOURCE_AUDIT.json` bind the work to the actual177-part candidate. The result is suitable for supplier DFM and a controlled first-article qualification build, with the explicit sourcing, construction and physical gates below. It is not an automotive compliance or finished-product qualification claim.

| Topic | Current authority |
|---|---|
| Exact parts, source pin paths and bounds | `DESIGN_AND_MODEL_BASIS.md`, `AUTHORED_CHANGES.json`, `SOURCE_AUDIT.json` |
| Startup, load release, shutdown and recovery | `POWER_RESULTS.json`, selected case files and `evidence/runs/` |
| Automotive envelope, SOA and component energy | `INPUT_PROTECTION.md`, `INPUT_RESULTS.json` |
| Actual coordinates, paths, returns and annotated views | `LAYOUT_ASSESSMENT.md`, `evidence/layout/`, `evidence/filled_returns/`, `evidence/ground/` |
| Native ERC/DRC/parity,177-part STEP, BOM and manufacturing outputs | `evidence/native/` |
| Populated/mated/probe and thermal checks | `evidence/mechanics/`, `evidence/thermal/`, `THERMAL_RESULTS.json` |
| Dispositions and physical gates | `FINDINGS_REGISTER.json`, `QUALIFICATION_AND_SERVICE.md` |
| Full and rejected experiment records | `FULL_RECORD_ARCHIVES.json`, `evidence/EXPERIMENT_INDEX.json`, `evidence/rejected/` |

The fitted U121 divider sets 4.908 V nominal; the final suite covers the retained 4.75–5.25 V interface envelope. Cold 750 mA startup at the low endpoint exposed excessive reservoir charging demand. C166 is now 68 nF C0G, with exact capacitor/IC timing bounds; the rejected longer PG delay and extra input capacitance trials remain recorded. The main final power suite has31 completed cases; two PG-tolerance cases and one discharge-copper case supplement it. Seventeen input-stress cases completed; one initially incomplete unloaded-start record is retained separately from its successful repeat. The final modeled normal main range is3.13255965–3.57139192 V. The lower supervisor margin is16.50965 mV; upper3.6 V margin28.60808 mV. The worst modeled reverse differential is about−0.067006 V against−0.3 V. All normal cases release READY once and have no SNS retries; supply-fault resets are classified separately. Results use full finite records; decimated traces are for plotting only.

The final native KiCad9.0.9 run has zero ERC, DRC, unconnected and schematic-parity findings, zero exclusions,13 successful output postconditions, and177 resolved fitted STEP components. The actual source has25 new references (24 fitted parts and TP154),41 added ordinary vias and four removed obsolete vias. Source audits preserve the49 special via identities, four-layer stackup/rules, CAN/GPIO/RF/GPS/oil contracts,32 unchanged firmware files and adopted mechanics. Mechanical review covers1308 populated plus529 mated checks and38 probes with no interferences; minimum allocated clearance0.120 mm includes the full1.71 mm stack.

The historical112.88298 C board-region correlation trigger is retained. The revised same-budget one-step board screen is113.220731 C; that difference requires physical model correlation, not a relaxed threshold. Worst leakage with both converters at exactly80% also exceeds the fixed heat budget; the measured-loss requirement is explicit. Immediate U201 air≤85 C, bulk cabin65 C, Adafruit851 local≤60 C and the sustained I25 workload remain mandatory.

## Replay

Use a checkout containing this I32 source. Python3 with NumPy/SciPy/Shapely/networkx/Matplotlib/pyamg and native KiCad9.0.9/pcbnew is required; mechanical replay also uses the repository's declared geometry dependencies. Run `--help` for individual paths. Do not save this board with an unreviewed newer KiCad serializer.

```sh
python docs/engineering/rvb22/candidate/run_native_candidate.py --cad-dir docs/engineering/rvb22/candidate/cad --output /path/to/native_i32 --kicad-cli /path/to/kicad-cli --pcbnew-python /path/to/python-with-pcbnew --component-step
python docs/engineering/rvb22/analyses/i32/source_audit.py --native-dir /path/to/native_i32 --out /path/to/source_audit
python docs/engineering/rvb22/analyses/i32/power_chain.py --cases docs/engineering/rvb22/analyses/i32/SELECTED_POWER_CASES.json --output /path/to/power --jobs 2
python docs/engineering/rvb22/analyses/i32/input_stress.py --cases docs/engineering/rvb22/analyses/i32/FINAL_INPUT_CASES.json --output /path/to/input --jobs 2
python docs/engineering/rvb22/analyses/i32/layout_audit.py --pcb docs/engineering/rvb22/candidate/cad/GR86_CCA_RevB.kicad_pcb --output /path/to/layout
```

Replay the PG and discharge supplementary case files similarly. `FINAL_INPUT_CASES.json` includes the originally incomplete unloaded case; replay is a new execution, not retroactive completion of that record. The current 34 cases are selected by exact parameters and `record_directory` in `POWER_RESULTS.json`; 15 use the first final execution and 19 use complete repeats after record-write interruption. Older groups, including previous narrow-voltage passes, are historical even if their directory names or old archive metadata say selected. Full native input/output inventories, exact decks, controller libraries, command logs and raw hashes remain the execution authority. `evidence/REPLAY_COMMANDS.json` records the geometry/ground/thermal commands and retained baseline dependencies. Vendor trial summaries have their own explicit abort/end-time status.

`author_candidate.py`, `controlled_reservoir.py`, `refine_candidate.py`, `refine_bulk_charge.py`, old route tasks and `history/` preserve intermediate design work. They are **not an idempotent way to reconstruct the final board** and must not be run on the delivered candidate. Reproduce the selected source by checkout and verify it with the native runner/source audit. `ADOPTED_ROUTE_INVENTORY.json` records surviving task UUIDs; rejected or partially replaced routes are not silently counted as complete.

The recovered I31 ZIP with61 cases and SHA256`92788424fa8389690963c58553d177a2e55a9ba1fec3674175d1477569b8f1ca` remains distinct from the newer132-case repository summary whose full ZIP is missing. I32 does not add those counts or invent the missing logs. The unmodified U121 vendor baseline completed; the historical170-part closed attempts on ngspice42/47 aborted near21.3 ms. They do not validate the final177-part design. Manufacturer-controller correlation, hot soak, pulse survival, installed fit and supplier process acceptance remain genuine physical gates.

The record index contains 664 experiment directories, 622 positive-size retained waveform payloads and one explicitly invalid zero-byte historical artifact in 19 original ZIP containers. These counts are preservation inventory, not passing case counts. `RAW_ARCHIVE_DISTRIBUTION.json` maps the original containers to exact byte parts where needed. Restore with `record_archive_parts.py restore --manifest RAW_ARCHIVE_DISTRIBUTION.json --parts-dir /path/to/downloaded --output-dir /path/to/restored`; each part and restored ZIP is checked. Failed or superseded executions stay separate from the accepted 34 power and 17 input cases.
