# Sourced I32 assembly and acceptance

Use this package's native project, BOM, CPL, Gerbers and manifest together.
The assembly population is 177 fitted / 175 factory / 2 local (F101, U401).
C203, R301 and R306 are DNP. Every factory reference stays in the full CPL even
when its sourcing or handling requires supplier review.

## Supplier sourcing review

`assembly/PROCUREMENT_BOM.csv` lists exact MPNs, documented supplier spellings,
catalog handling, stock snapshots and preorder minima. All 175 factory references
have JLC catalog assignments; Global Sourcing and consignment are not permitted
factory sourcing routes for this package. No substitutions are authorized by a
blank field or by a supplier's similar-part recommendation.

The purchasing quantity must cover the build quantity and the supplier's assembly
attrition allowance. Complete the parts listed in `PREORDER_REQUIREMENTS.csv`
and confirm receipt into the parts library before scheduling assembly. Snapshot
stock and a public preorder button do not reserve inventory or guarantee lead time.

JLC marks several entries `manualWeld` (wave/manual handling), including L121,
C162, F1, D104, J202 and J203 as identified by the generated procurement BOM. Confirm
each actual part's process, orientation and fixture requirements with the
manufacturer; catalog handling is not a board-level solder-process approval.
In particular, C162's catalog package description is inconsistent with its
manufacturer dimensions. The supplied KEMET maximum-body footprint and model
remain controlling. No footprint is resized to match that catalog label.

## Placement and fabrication

CPL coordinates retain KiCad's auxiliary origin (0, 41.288863) mm:
X = board X, Y = 41.288863 − board Y. Layer and angles are the native exports;
obtain the supplier's feeder/bottom-side orientation acceptance. Do not add
blanket 90°/180° corrections. F101 and U401 are excluded from factory CPL.

R156 remains 1206, R160 remains 0805 and L121 keeps its qualified BPCI land
pattern. All 13 frozen MPN/C-number bindings are unchanged. Preserve C166's
edge/placement allocation and maximum-body model. U101 retains the accepted
LTC4367HMS8#PBF ordering pedigree; #W equivalence is not claimed.

Retain four layers, 70/30/30/70 µm copper, 203/1030/203 µm dielectric, ENIG,
1.44–1.76 mm accepted finished thickness and at least 15 µm minimum finished
hole-wall plating. Exactly 49 enumerated vias require fill, cap and planarize:
48 at U201 and one at R153. Use the supplied process JSON and location CSV.
Preserve all exposed-pad net isolation and stencil windows, including U501's
separate OIL_EFUSE_RTN. Ordinary tented vias are not an approved replacement.

F101 requires its qualified local solder process after global reflow. U401
PA1616D remains local installation at PCB (54.5, 9.0) mm, F.Cu, 0°; pin 1 is
(46.7, 2.25) mm in top view. Exact module supply and receiving inspection remain
required. Preserve all antenna and connector keepouts.

## Retained qualification

The controlling C05/W02/T03 mechanics, harness and receiving/installation
requirements remain those in `documentation/QUALIFIED_ASSEMBLY_REQUIREMENTS.md`;
its earlier procurement counts are superseded by this package. Retain all
material, fit, clamping, thermal-contact and cable-restraint acceptance gates.

The I25 release profile and 2.940859375 W heat budget remain fixed. Retain the
112.8829809018675 °C board-region correlation trigger and U201 immediate-air
limit of 85 °C. At U151 efficiency of 80%, the retained loss allocation requires
U121 efficiency about 83.4631% or an accepted measured-loss alternative within
the same budget. Neither board temperature nor simulated power proves physical
junction temperature or efficiency. Adafruit 851's retained local 60 °C limit
also remains a qualification condition.

Use only the source-bound 160 MHz firmware identified in FIRMWARE_EFFECTIVITY.json.
Fit/assembly, thermal and electrical correlation, transient/reset/EMC tests,
vehicle validation and unit acceptance remain open. This package records no
supplier acceptance, manufacturing order, flashing or physical test.
