# Current I32 sourced ECAD and manufacturing — 2026-09-15

Use the [sourced manufacturing handoff](product/PRODUCT_HANDOFF.md) and
[sourced native project/package](current/i32_sourced_manufacturing/README.md).
All 175 factory references have verified JLC catalog assignments; all 29 missing
assignments are resolved using the exact specified parts. Native schematic/PCB
procurement fields, BOM, CPL and fabrication outputs are regenerated. Fresh
ERC/DRC/parity/unconnected findings are zero. The qualified circuit, geometry,
models and simulation bindings are preserved. Preorders, supplier process
acceptance and physical qualification remain open. Earlier procurement counts
and package pointers below are historical.

## Qualified frozen-parts baseline — 2026-09-15

The native frozen-parts redline is completed and desktop-verified. Current source, BOM/CPL, manufacturing files and affected verification are controlled by [the redline report](analyses/i32/procurement_redline/README.md), [final verification](analyses/i32/procurement_redline/FINAL_REDLINE_VERIFICATION.json), and [source effectivity](current/SOURCE_EFFECTIVITY.json). Supplier and physical gates remain open. Earlier source hashes, active parts, numerical results and package pointers below are historical where superseded; the original document is preserved under `analyses/i32/procurement_redline/history/pre_redline/`.

---

# I32 recovery and digital closure — 2026-09-14 UTC

The authoritative 177-part I32 recovery overlay is applied. The authored PCB remains SHA-256 `45a2a679d9893d51fa641e539af45bc6ec1324169ea5f2226ecdea0ae2464da7`; preserved KiCad 9.0.9 evidence reports zero ERC, DRC, unconnected, parity, and exclusion findings with 177 resolved STEP components.

I32-RCV-FW-01 is digitally closed by a genuine unchanged-source ESP32-S3 build using Arduino CLI 1.3.1, Arduino-ESP32 3.3.6, NimBLE-Arduino 2.3.6, GCC 14.2.0_20251107, and `CPUFreq=160`. All 28 source/image/ELF release checks pass. See `analyses/i32/recovery_20260914/firmware_160mhz/`.

No hardware was connected, flashed, or operated. Supplier sourcing/DFM, construction, thermal correlation, EMC, silicon behavior, first-article, installed fit, and vehicle qualification remain acceptance gates.

---

# GR86 CCA I24 engineering checkpoint

This checkpoint preserves completed I24 PCB, return-path, manufacturing/ground and authored mechanical evidence while the final fine thermal retry and register/workbook reconciliation are still running. It is not the final I24 package or a fabrication release.

Native source commit `49e5aaf04127c61ab0b967150a24e59a57323872` passes all 14 CAD/build postconditions in run `34499455561`; exact hashes are in `current/I24_SOURCE_VERIFICATION.json`. Independent review reduces adjacent-reference interruptions from 15 to 6 with no regression across 313 critical outer segments. All nine CAN_RX gaps and the simultaneous inner-plane gap are removed. Six CAN_TX nearest-plane gaps remain open. See `analyses/return_i24/NATIVE_REFERENCE_REVIEW.json`.

The C06/W03/T04 source is under `current/mechanics/I24_trial`. It is an authored, unaccepted trial; C05/W02/T03 acceptance was withdrawn in I23. [Independent mechanical review](analyses/mechanics_i24/independent_review/FINAL_INDEPENDENT_REVIEW.md) passes 9,982 expanded motion checks after cable/post, root-support and motion-envelope corrections. Material, nonlinear, joint, preload and installed sink/support acceptance remain open.

The corrected ground calculation includes all 348 real bores and retains the original 15/11 mΩ allocations. Actual native copper/Gerber/net/drill reconciliation passes. Evidence is under `analyses/power_i24` and `analyses/manufacturing_i24`.

The recovered original-criteria status is 139 closed /147 open /4 not applicable, reflecting I23's MECH-03 reopening. Earlier I22 whole-assembly acceptance and 140/146 counts are historical. The register/workbook in this intermediate commit has not yet received the final I24 dispositions. The final fine thermal solver exceeded its silent-stage time budget without a result; a checkpointed, observable retry retains the full equations and residual gates. Final thermal reports and reconciled spreadsheet will follow in PR46.

Adafruit 851/960, Honeywell MIPAN2XX150PSAAX, GR86 ASC mapping, Compact TW artwork and full 4.815 W /65°C air /70°C landings /70 kPa remain unchanged. The linked 851 60°C limit remains unresolved. No mechanical/thermal product acceptance, fabrication, flashing or physical test is claimed.
