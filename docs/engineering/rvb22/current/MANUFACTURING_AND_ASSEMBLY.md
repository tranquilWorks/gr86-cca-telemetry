# Current I32 manufacturing and assembly effectivity

The controlling source is the 177-part I32 candidate, authored PCB SHA256 `45a2a679d9893d51fa641e539af45bc6ec1324169ea5f2226ecdea0ae2464da7`, native filled PCB SHA256 `249d7b584af71605ee160c1ff425fda16a11b3ba93458bb243a722214c66ab30`. `SOURCE_EFFECTIVITY.json` and `../product/PRODUCT_HANDOFF.md` identify the current exports and acceptance. Earlier I20/I22/I29 source counts, hashes and electrical values are superseded; their records remain in history.

| Item | Current instruction |
|---|---|
| Assembly | 177 fitted references, 175 automatic placements. F101 and U401 remain local/manual exceptions. Use the generated complete BOM and CPL; confirm supplier bottom-side rotation conventions. |
| Sourcing | 40 factory references have no assigned LCSC code. Confirm exact MPNs; a blank code is not approval for substitution. C203, R301 and R306 remain DNP. |
| Switches and capacitors | U152/U153 TPS22953QDQCRQ1, without QOD. C159 33 nF CGA4J1C0G2A333J125AE; C166 68 nF CGA5L1C0G2A683J160AE. C162 T598X477M010ATE025 470 uF/10 V; C206 T598X687M006ATE025 680 uF/6.3 V. Use the supplied maximum-body footprints/models. |
| C166 tab fit | B.Cu (85.85, −3.0) mm, 90°; maximum body 3.60 ×1.90 ×1.90 mm. Copper-edge clearance 0.30 mm; nominal maximum-body-to-tab-edge clearance 0.10 mm. Confirm edge/placement tolerance, solder fillets and installed fit with the supplier and first article. |
| Feedback and damping | R155/R156 11.8 k/5.05 k TNPU 0.02%, 2 ppm/K. R158 WSL2512R3000FEA 0.30 ohm. R165 **CRCW25124R70FKEGHP**, 4.7 ohm HP 1.5 W; the standard 1 W variant is not equivalent. R204 100 k selects the reset delay. |
| Input protection | D101 S5J 600 V; R101 CRCW251212K1FKEG 12.1 k/1 W; D105 SMCJ110A. Preserve clamp polarity and source-bound routes. |
| Layers and finish | Four layers, 70/30/30/70 um copper, 203/1030/203 um dielectric and ENIG. Retain all authored clearances and rules. Board nominal 1.6 mm, accepted thickness interval 1.44–1.76 mm. |
| Filled/capped vias | Exactly 49 enumerated locations: 48 at U201 exposed pad 41 and one at R153. Fill, cap and planarize for soldering. Ordinary tented vias do not substitute for these locations. |
| Plating and drill | At least 15 um **minimum finished wall**, not merely an average specification. New ordinary vias are at least 0.6 mm land/0.3 mm drill. Supplier drill/preplate process and connector/hardware fit require exact DFM acceptance. |
| Fuse process | F101 Littelfuse 0885001.DR is excluded from global paste/PnP. Its recommended 255–260 C process conflicts with the ESP32 module's 235–250 C range; use a qualified local solder process after global reflow. |
| Manual GPS | U401 PA1616D, PCB centre (54.5, 9.0) mm, F.Cu, 0°. Pin 1 is at PCB (46.7, 2.25) mm in top view. Preserve the verified land numbering and antenna keepout. |
| Probe access | 38 approaches checked with a 0.30 mm needle, 0.10 mm position allowance and at least 5 mm slender exposed shaft. Remove carrier for bottom access; retain latch and programming volumes. Use short-return or differential probing for fast signals. R153 remote test points share power copper; they are not four-terminal Kelvin sensing. |

The controlling mechanics remain C05/W02/T03 in `mechanics/`. Each flex member uses 200 annealed, unbonded C110 laminae, 0.010–0.011 mm each, with bonded terminals only, total 2.0–2.2 mm. Preserve cold-terminal support, material/hot-strength/contact requirements and maximum 220 g carrier mass. C05 support relief and cable restraint remain mandatory. Material, friction, clamp retention, creep/fatigue and installed construction remain acceptance gates.

The populated clearance model adds the full 1.71 mm: 0.25 mm solder, 0.51 mm capture freedom, 0.75 mm warp and 0.20 mm deflection. Component XY adds 0.30 mm; flex geometry includes the full 2.2 mm packet, 0.50 mm bow and 0.30 mm position allocation; carrier/support XY adds 0.15 mm. Current evidence covers 1,308 populated and 529 mated checks plus 38 probes, with no interference. Minimum allocated separation is 0.120 mm at R408/T03 and 0.200 mm at C159/W02. This does not establish installed fit.

Retain Adafruit 851 with Adafruit 960, 150 ±3 mm to the SMA shoulder, nominal cable OD 1.8 mm, receiving maximum OD 2.0 mm, 0.5 mm lateral uncertainty and 15 mm bend radius. The miniature mated-plug allocation is 3.4 ×5.3 ×3.25 mm. Preserve the negative-Y exit and independent carrier restraint. **851 local environment must remain at or below 60 C**, including during the 65 C cabin test; relocation or an approved rated alternative is required if exceeded.

Keep source-defined exposed-pad nets and stencil windows: U121/U151/U201/U301 ground topology, U201's nine 0.9 mm mask/paste windows and 48 filled/capped pad vias, and U501's separate OIL_EFUSE_RTN. Do not short the oil eFuse return to ground. Current native Gerbers and the authored PCB govern exact geometry; earlier package overlays and thermal/via screens apply only to unchanged geometry and retain their original scope. Independent stencil/reflow and human assembly review remain open.

Harness effectivity is the GR86 ASC mapping in the retained interface contract, with the single full-current F1.1 return and F1.2 unpopulated. Use switched fused accessory power, controlled terminations and strain relief. Preserve receive-only CAN, TCAN3403DRBRQ1, the GPIO contract, PA1616D 115200/10 Hz/PPS and the Honeywell MIP 150 psi 5 V ratiometric sensor.

The I25 profile and fixed 2.940859375 W heat budget remain. Both converters at exactly 80% with worst modeled leakage exceed it; at U151 80%, U121 requires about 83.3396% or an approved measured-loss alternative within the same budget. Retain the 112.8829809018675 C board-region correlation trigger, U201 immediate air at most 85 C and all I32/retained I26 qualification gates. No supplier approval, order or physical qualification is implied.

For historical detail, see `../analyses/i32/history/I22_MANUFACTURING_AND_ASSEMBLY.md`. Its old electrical values, source effectivity and numerical counts are not current instructions. Any part, geometry, material, process or firmware change requires impact review and regeneration of affected evidence.
