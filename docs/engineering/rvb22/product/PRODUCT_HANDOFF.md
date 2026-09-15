# I32 procurement redline product handoff

Current package: [GR86_I32_PROCUREMENT_REDLINE.zip](GR86_I32_PROCUREMENT_REDLINE.zip). Current native source is `../candidate/cad/`; [SOURCE_EFFECTIVITY.json](../current/SOURCE_EFFECTIVITY.json) and [PACKAGE_VERIFICATION.json](PACKAGE_VERIFICATION.json) bind source and generated output hashes.

The package contains 177 fitted parts, 175 factory CPL rows, F101/U401 local/manual assembly and the unchanged C203/R301/R306 DNP set. All 13 frozen substitutions use exact MPN/C-number properties and checked native packages. [The completed engineering report](../analyses/i32/procurement_redline/README.md) records the full change set, all 14 desktop verification categories, fresh ngspice margins, thermal/model limitations and the live JLC snapshot.

U101 is LTC4367HMS8#PBF, with the explicitly accepted loss of #W controlled-manufacturing pedigree. R156 is 1206, R160 is 0805 and L121 uses the manufacturer BPCI land pattern.

Supplier acceptance is still required for L121 manual/wave handling, exact special-via/stackup/plating/stencil DFM and 29 unchanged factory references without assigned LCSC codes. Physical first-article, thermal correlation, electrical/EMC, installed vehicle and unit validation remain open. No order, hardware flashing, assembly validation or physical tests were performed.

Earlier I29/I32 packages and their previous manifests remain historical and are not the current manufacturing authority. `build_package.py` is a historical I29 authoring recipe; use `../analyses/i32/procurement_redline/generate_manufacturing.py` for this package. Firmware remains bound to the verified 160 MHz recovery build; old 240 MHz images remain excluded.
