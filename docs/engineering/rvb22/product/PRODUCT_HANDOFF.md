# I32 sourced ECAD and manufacturing handoff

**All 175 factory references now have JLC catalog assignments.** The 29 previously
missing assignments use the exact specified parts. No factory Global Sourcing,
consignment or new component substitution is required.

**Current package:** [GR86_I32_SOURCED_MANUFACTURING.zip](GR86_I32_SOURCED_MANUFACTURING.zip).
Open [GR86_CCA_RevB.kicad_pro](../current/i32_sourced_manufacturing/editable_source/cad/GR86_CCA_RevB.kicad_pro)
for the sourced native project. Use its [BOM, CPL and fabrication files](../current/i32_sourced_manufacturing/README.md)
together. [Verification](../analyses/i32/procurement_completion/VERIFICATION.json)
and [member manifest](../current/i32_sourced_manufacturing/SOURCE_MANIFEST.json)
bind the actual editable CAD and exported package.

Both schematics and PCB carry the sourcing route, URL, supplier MPN and verified
LCSC assignments. The package retains 177 fitted references, 175 factory
placements, F101/U401 local installs and C203/R301/R306 DNP. All 13 frozen
substitution identities, R156 1206, R160 0805 and L121's BPCI land pattern remain.
The [procurement redline](../current/i32_sourced_manufacturing/assembly/PROCUREMENT_REDLINE.csv)
lists all new assignments and the five documented identity mappings covering
twelve references. Original design MPNs are retained; supplier spellings are
recorded explicitly, including TDK catalog-to-label aliases.

Fresh KiCad 9.0.9 ERC/DRC/unconnected/parity results are **0/0/0/0**. Every native
placement and schematic net matches the qualified baseline. The complete filled
PCB and all 14 fabrication files match that baseline after removing only
procurement fields, regenerated property IDs and export generation headers.
The prior 32/32 SPICE cases, thermal analyses, populated STEP and 160 MHz firmware
build are retained through exact source/physics comparison. These solvers and
the firmware build were not rerun.

**Ordering still requires** the [listed preorders](../current/i32_sourced_manufacturing/assembly/PREORDER_REQUIREMENTS.csv),
build quantities/attrition, stock allocation and supplier process acceptance.
Six factory references have manual/wave catalog handling, including L121 and
C162. Obtain orientation, exact stackup, 49 filled/capped vias, minimum plating
and stencil acceptance. F101 and U401 remain local installations; exact PA1616D
supply and receiving acceptance remain required. Physical fit, thermal/loss
correlation, bench electrical/EMC, vehicle and unit validation remain open.

Reproduce with [build.py](../analyses/i32/procurement_completion/build.py) using
the [documented commands](../analyses/i32/procurement_completion/README.md).
The qualified circuit/geometry baseline remains `candidate/cad/`; procurement
decisions are maintained in [SOURCES.json](../analyses/i32/procurement_completion/SOURCES.json).
Their generated successor is the current manufacturing project linked above.
Earlier packages, including `GR86_I32_PROCUREMENT_REDLINE.zip`, remain historical
evidence. No order, supplier message, merge, hardware flash or physical test is
claimed.
