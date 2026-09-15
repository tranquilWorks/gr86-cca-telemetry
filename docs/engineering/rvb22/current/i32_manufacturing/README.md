# I32 procurement-redline manufacturing package

Source and member hashes: `SOURCE_MANIFEST.json`. This package contains 177 fitted parts, 175 factory CPL rows, two local/manual installs (F101/U401) and the unchanged DNP set C203/R301/R306. It is a reviewed source/DFM package, not an authorized production order.

All 13 frozen substitutions are applied to native CAD and generated files. U101 uses the owner-accepted #PBF ordering option without equivalent #W pedigree. See `ASSEMBLY_AND_ACCEPTANCE.md` for the retained construction and physical gates.

`assembly/SOURCING_REQUIRED.csv` lists 29 unchanged factory references still requiring exact source assignment. JLC lists L121/C6471075 for manual/wave handling; supplier process/orientation approval is required. All nine frozen MPN/C-number pairs had public purchase/preorder paths at the retained snapshot; no inventory is reserved. F101 and U401 are the only local-install exceptions.

CPL coordinates follow native KiCad auxiliary-origin export: origin (0,41.288863) mm; X=board X and Y=41.288863-board Y. Angles are native footprint angles. Confirm feeder and bottom-side interpretation with the supplier.

Firmware source is unchanged; `FIRMWARE_EFFECTIVITY.json` identifies the verified 160 MHz build and source hashes. Historical 240 MHz images must not be used. No hardware has been flashed.

Physical qualification remains open: thermal correlation, fit/material/process acceptance, electrical/transient/EMC tests, vehicle and unit acceptance.
