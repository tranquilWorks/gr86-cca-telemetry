# GR86 / BRZ telemetry Rev B — product handoff

## What this package is

A source-bound **PCBA quotation, assembly-planning and first-article package**, not an assertion that an installed product has been physically qualified. It collects the actual board, firmware, manufacturing outputs and construction conditions in one place. Waiting for another CI run is not a prerequisite for using this handoff.

The controlling product source is PR #46, branch `codex/rvb24-coordinated-closure`. The reviewed handoff parent is `296a86495ae665c8a377be777a413a2c1d4baa73`. Authored PCB SHA-256 is `a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936`.

The matched native export was generated from commit `1aa1b2e880d94e36a8017087241ed954d2aa4f3f`. Its 101 CAD inputs and 32 firmware inputs match the current product files byte-for-byte. This is reuse of an already executed native build, not a claim that KiCad or the target compiler ran again during packaging. Every retained native output is checked against its archived byte count and SHA-256. The native result records zero ERC/DRC findings, 153 fitted component models, and actual target firmware images.

## Start with the right files

`fabrication/JLCPCB_GERBERS.zip` contains the copper, mask, paste, silkscreen, board outline and separate plated/nonplated drill files. `assembly/JLCPCB_BOM.csv` and `assembly/JLCPCB_CPL.csv` are the 151-part automatic-placement set; the CPL preserves native side, datum and rotation rather than applying guessed vendor rotation offsets.

`assembly/COMPLETE_FITTED_BOM.csv` is the full 153-part inventory. `assembly/LOCAL_ASSEMBLY_BOM.csv` explicitly retains F101 and U401; they are not DNP components. `assembly/DO_NOT_POPULATE.json` freezes C203, R301 and R306 as DNP. The native schematic, populated STEP, IPC-D-356 netlist, editable KiCad files and firmware source/images are included separately.

**This is not yet a one-click, fully sourced PCBA order.** Fourteen automatic-placement references have exact manufacturer part numbers but no assigned LCSC code in the controlled source. They are listed in `assembly/SOURCING_REQUIRED.csv`, not silently substituted or omitted. Arrange exact-part sourcing/consignment with the assembler before order approval. The separate manual GPS module also has no LCSC allocation. Existing LCSC codes are identifiers, not a claim of live stock or supplier acceptance.

## Product variant and operating intent

The board is the receive-only 500 kbit/s CAN variant, with R301 open, R303 fitted as the recessive TXD pull-up, no transmit API/queue, and R306 unpopulated on the vehicle bus. Do not convert it into an active CAN transmitter or add termination without a separate review.

The firmware selects the PA1616D GPS-only configuration, 115200 baud, 10 Hz, and the selected external GPS L1 antenna. Acknowledgment/readback and actual solution cadence are checked; a sent configuration command is not treated as proof of acceptance. The oil path supports the named Honeywell MIPAN2XX150PSAAX 150 psi sealed-gauge, 5 V ratiometric sensor. Calibration is against known pressure and measured excitation, not an assumed key-on zero. The source programming/calibration guide controls the procedure.

The adopted thermal operating profile remains 160 MHz, BLE +3 dBm, no Wi-Fi, at most 120 notifications/s, a 0.45 A sustained main-profile allocation and at least 80% converter efficiency or the recorded loss alternative. The adopted heat allocation is 2.940859375 W. Earlier approximately 4.8 W cases remain stress sensitivities, not the release steady-state source. The current main-rail parts are R155 11.8 kohm / R156 4.99 kohm TNPU, R153 10 milliohm, R158 82 milliohm and C206 T598X477M006ATE025. U121 is **LM5164QDDARQ1 / C2072225**, not LM5164DDAR.

Deep 6 V crank is intentionally an undervoltage shutdown/restart case, not guaranteed uninterrupted telemetry. The input protector and Q101 provide isolation; the downstream buck is not credited with absorbing unsuppressed load dump directly.

## Manufacturing and assembly conditions

Use the authored four-layer stackup in `fabrication/AUTHORED_STACKUP.json`: 70 micrometre outer copper, 30 micrometre inner copper, specified FR4 dielectric layers and ENIG. Have the supplier confirm the actual stackup rather than choosing an unreviewed standard substitution.

There are **49 required filled, capped and planarized via locations**: 48 under U201 pad 41 and one at R153 pad 2. Their current PCB coordinates, UUIDs, drill and land sizes are in `fabrication/FILL_CAP_PLANARIZE_49_VIAS.csv`. Tenting is not equivalent. The 15 micrometre minimum finished plated wall is a construction condition; an average-wall specification does not prove it.

F101 is the Littelfuse 0885001.DR fuse. It must receive the separately qualified **local, post-reflow solder process**, not global paste/PnP. U401 is the manual GPS assembly. Preserve the native pin-one and polarity orientation, local soldering access, exposed-pad stencil treatment and source-defined isolated returns. Use the supplier's final placement preview to reconcile its zero-degree conventions; do not rotate parts by guessing.

The current mechanical source is C05/W02/T03 in `mechanics/current_C05_W02_T03/`. C02 additional cooling and the I24 trial geometry are not adopted. The existing flexure construction is 200 unbonded C110 laminae per flex member, 0.010–0.011 mm each, bonded at terminals only. Do not replace this with a solid bonded packet. The historical I22 manufacturing document is provided for detailed retained construction instructions; its old PCB hashes, old source locations and superseded thermal-state paragraphs are not the current electrical or thermal authority. I25 governs the adopted thermal profile.

## What remains outside desktop completion

The 290-row I27 register distinguishes 141 source/documentary dispositions, 31 conditional-model dispositions, 114 hardware/supplier/installation acceptances and four not-applicable rows. Its zero actionable desktop count **does not mean 290 physically passed requirements**.

Before approving fabrication, resolve exact-part sourcing, the supplier's actual stackup/plating/via-fill process, and its final assembly preview. No order, supplier approval, programming, bench energization or vehicle test was performed by this handoff.

Before use, execute the retained input protection, rail transient/reset, current/efficiency, GPS/antenna, oil calibration/fault, BLE/RaceChrono, CAN non-interference and mechanical/thermal checks. I26 qualification gates provide numerical limits and uncertainty rules. The 112.883 C thermal screening value is a board-region model allowance, not semiconductor junction temperature; immediate air at U201 must remain within its 85 C limit.

**The Adafruit 851 adapter is rated for a 60 C local environment, below the 65 C bulk-air design case.** Its installed thermal environment must be kept within 60 C, or a correctly rated equivalent must be approved. A chamber measurement cannot waive the manufacturer's rating. Do not treat this as an unrestricted 65 C-rated finished assembly.

I28's power arithmetic and acquired TI model files are not full-board vendor-macromodel SPICE validation. The model execution findings in `SPICE_EXECUTION.md` state exactly what ran and what did not. The encrypted LM63615-Q1 model and full coupled-power transient/corner correlation remain unverified; no idealized substitute is silently promoted to a vendor-model pass.

## Reproduce this package

From the repository checkout matching the controlled source:

```sh
python docs/engineering/rvb22/product/build_package.py \
  --native-zip /path/to/native-sync-i28.zip \
  --output /path/to/GR86_RevB_I29_Quote_And_Build_Package.zip
```

The builder performs local integrity/population checks, rejects a mismatched native archive or changed source, and refuses to overwrite an existing output. It does not poll CI, push branches, place orders or operate hardware. `PACKAGE_VERIFICATION.json` records the actual result, and `SHA256SUMS.json` covers every other package member. The PR remains unmerged; this publication does not alter `main`.

Supplier file-format references: JLCPCB's official *Pick & Place File for PCB Assembly* and *How To Export BOM and Pick & Place Files From KiCad* articles, reviewed September 12, 2026. Model references: TI's LM5164-Q1 and LM63615-Q1 official product/model pages. Their URLs are retained in `SOURCES.json`.
