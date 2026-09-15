# I32 power placement and copper assessment

The source PCB is `45a2a679d9893d51fa641e539af45bc6ec1324169ea5f2226ecdea0ae2464da7`; native filled PCB is `249d7b584af71605ee160c1ff425fda16a11b3ba93458bb243a722214c66ab30`. `evidence/layout/LAYOUT_MEASUREMENTS.json` records 80 pad pairs with actual coordinates, layer sets, track/via UUIDs, neck widths and routed distances. Seven annotated views accompany it. Twenty-three ground pairs are separately connected through actual native fill in `evidence/filled_returns/`. An explicit-route graph reporting “zone return required” is not an open circuit when that filled-ground check passes.

Distances below are centerline lengths **outside pad/via regions**, not center-to-center placement distances. Calculated resistance uses 150 C copper, 50 um outer /24 um inner thickness and 0.06 mm total width loss. Pad spreading and barrels are added separately where they affect the power model. These are engineering bounds and geometric measurements, not field extraction.

| Path | Routed length mm | Minimum width mm | Vias | Assessment |
|---|---:|---:|---:|---|
| U121 C123 to VIN | 0.051 | 0.40 | 1 land encountered; no layer transition | Retain local input bypass. Pad-edge gap0.650 mm. |
| U121 C123 to PGND / EP | 1.306 /1.756 | 0.60 | 0 | Direct front copper plus confirmed filled return. |
| U121 bootstrap BST /SW | 0.650 /0.655 | 0.30 /0.70 | 0 | Local loop retained. |
| U121 SW to L121 | 4.625 | 0.70 | 0 | Front only. |
| L121 to C127 | 13.875 | 1.20 | 0 | Wide output path; filled return confirmed. |
| U121 FB upper /lower | 3.058 /1.932 | 0.20 | 0 | Divider beside FB, away from inductor switching land. |
| U151 C152 to VIN13 /PGND15 | 0.876 /0.876 | 0.35 | 0 | Both pad-edge gaps0.875 mm; nearest adjacent power pins meet the published1 mm placement recommendation. |
| U151 C152 to VIN12 /PGND16 | 1.300 /1.300 | 0.35 | 0 | Additional package power pins share the adjacent local connection; no claim that all pad centers lie within1 mm. |
| U151 VCC /BOOT /SW bootstrap | 1.203 /0.627 /0.772 | 0.20 /0.25 /0.35 | 0 | Local back copper retained; VCC ground verified through fill. |
| U151 SW to L151 /L151 to C155 | 2.784 /3.741 | 0.35 /1.00 | 0 | Compact switching connection, wider output copper. |
| U151 FB upper /lower /quiet return | 4.695 /2.345 /2.125 | 0.15 /0.15 /0.25 | 0 | Lower divider returns to AGND; output sense remains before R153. |
| C157 to R155 source sense | 20.180 | 0.15 | 3 | High impedance source-sense route, not a remote main-rail sense. |
| R153 output to U201 | 58.949 | 0.60 | 3 | 41.537 milliohm track contribution; main-loop allocation75 milliohm includes return. |
| U201 to U153 input | 62.089 | 0.20 | 5 | 65.278 milliohm track contribution; final branch model includes this route. |
| U153 output to R158 /R158 to C206 | 2.140 /1.615 | 0.60 /0.80 | 0 /1 | 3.012 milliohm combined tracks; controlled bulk charging, not the converter's high-frequency input loop. |
| C162 to C151 | 27.193 | 0.30 | 3 | 34.114 milliohm tracks; local C151/C152 supply the switching loop. |
| U152 CT /U153 CT | 2.781 /6.686 | 0.15 | 0 | C0G capacitors on their controller side; actual ground fill verified. |
| U152 PG to R166 /R166 to actual EN | 50.418 /36.627 | 0.15 | 2 /2 | Slow, filtered signals; PG and actual EN are separate nets. |
| U152 PG to Q153 | 102.973 | 0.15 | 2 | 1.200 ohm track estimate versus47 kohm pull-up; length is explicitly modeled as a slow control connection. |
| U202 CT to R204 | 11.579 | 0.15 | 2 | 100 kohm timing selection; two ordinary0.6/0.3 mm vias. |
| C157 source to R165 | 35.203 | 0.20 | 3 | 117.514 milliohm tracks; supplementary shutdown case includes150 milliohm total lead/return allowance. |
| D101 to added D105 clamp | 25.756 | 0.60 | 2 | 36.494 milliohm tracks;60 milliohm lead allocation and30/100/300 nH sensitivities retained. |
| U101 gate output to R106 /R106 to Q101 | 3.030 /2.948 | 0.20 | 0 /1 | Gate stopper and source-referenced clamp retained. |
| D104 to Q101 gate /source | 1.532 /3.383 | 0.30 /0.80 | 0 | Gate/source clamp loop remains local. |

The U151 external bypass loop's four pad-center vertices are VIN13(37.8625,13.325), C152+(40,13.2), C152−(40,14.75), PGND15(37.8625,14.625) mm. Its projected quadrilateral is3.046 mm². U121's corresponding VIN(44.3,25.865), C123+(42.15,25.75), C123−(42.15,23.85), PGND(44.3,24.595) gives3.408 mm². These quantify the external geometry; neither includes the unknown die/bond-wire path or claims an inductance extraction.

U151 switch copper is9.836 mm² on B.Cu only; the nearest same-layer sensitive copper is its FB pin,5.511 mm away. U121 switch copper is28.784 mm² on F.Cu only; its nearest sensitive item is the package's FB pin,1.055 mm away. The practical larger U121 land accommodates the selected12 mm inductor and bootstrap. No SW copper is routed through the GPS keepout or inner layers. The quiet feedback networks are on the opposite side of their power packages from SW. Compare the supplied views with TI's **correct HTSSOP16 LM63615** and **DDA LM5164** examples; the different WSON pin layout is not substituted. These dimensions do not certify EMI or switch-node ringing.

The R153 source/main test-point routes share power copper and are31.670 /55.736 mm respectively. They are **not a four-terminal Kelvin measurement**. Measure across R153's actual pads for small-current inference and measure main voltage differentially at the load's own ground. Remote test-point differences include power-route voltage drop. The added ground via at(38.6,21.6), with1.091 mm of0.6 mm back copper from C157's return, improves the source ground connection while retaining the original via(37.675,24).

The restricted In1 ground calculation uses complete copper cells, all via/PTH/NPTH bores, two meshes0.100/0.075 mm,15 um minimum barrel plating,150 C resistivity and10% numerical/spreading inflation. It obtains11.282 milliohm source-to-load against15 milliohm allocated; C206-to-load is10.919 milliohm against11 milliohm allocated. The latter has only0.081 milliohm residual allocation margin; it already includes the stated inflation and is a conditional numerical screen, not an exact continuum bound. Other parallel ground layers receive no resistance credit.

The final bulk-branch110 milliohm allocation includes65.278 milliohm positive routing,3.012 milliohm local output tracks, six full-length0.3 mm barrels at15 um plating (about16.84 milliohm),11 milliohm ground spreading and3 milliohm pad spreading: about99.1 milliohm total. R158 and U153 on-resistance are additional model elements. The200 nH branch and300 nH main/input-feed inductances are explicit engineering allocations. The previously used65 milliohm/100 nH branch model is superseded. The final power suite uses110 milliohm/200 nH and20 pF on actual EN.

I32 adds41 ordinary vias and removes four obsolete vias; all new ordinary vias are at least0.6 mm land/0.3 mm drill. The49 required filled/capped/planarized via identities remain unchanged. Source rules and stackup are unchanged. Rule areas retain their layer/permission sets; native nanometre coordinate quantization and removal of redundant polygon vertices are measured in `SOURCE_AUDIT.json`. They are not treated as a new keepout shape. Fitted CAN/GPS/oil/RF signal copper and firmware contracts remain preserved.

Disposition: retain the U121/U151 high-frequency placements, local bootstrap/VCC and feedback topology; adopt the input isolation, discharge, reservoir and reset routes, the improved C157 ground access, and corrected silk/probe legends. Native ERC/DRC/parity/connectivity are all zero. CT/supervisor noise, switch-node overshoot and conducted/radiated behavior remain measured acceptance gates after these digital inspections.

Primary layout sources: [TI LM63615-Q1](https://www.ti.com/lit/ds/symlink/lm63615-q1.pdf), June2026, pin table and§8.5; [TI LM5164-Q1](https://www.ti.com/lit/ds/symlink/lm5164-q1.pdf), layout guidance and DDA example; [TI TPS22953-Q1](https://www.ti.com/lit/ds/symlink/tps22953-q1.pdf), DQC package/layout and CT guidance.

C166 is the final 68 nF TDK CGA5L1C0G2A683J160AE at B.Cu (85.85, −3.0) mm, 90°. The 3.60 ×1.90 ×1.90 mm maximum body, supplied land pattern and STEP replace the earlier 33 nF envelope. The CT tail reaches pad1 at (85.85, −1.35); the ground trace starts at pad2 (85.85, −4.65). Copper-to-edge clearance is 0.30 mm; maximum-body clearance to the nominal tab edge is 0.10 mm. Confirm placement/edge tolerance and installed fit with the supplier and first article. The initial (86.05, −3.0) trial failed native edge clearance and was corrected before the final run.
