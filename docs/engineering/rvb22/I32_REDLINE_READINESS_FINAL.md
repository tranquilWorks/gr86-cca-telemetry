# GR86 Rev B I32 — Final Redline Readiness Gate

**Disposition: FULLY READY FOR REDLINE**

**Date:** 2026-09-14  
**CAD status:** no substitution redlines have been applied yet.

## Gate result

There are **zero unresolved non-GPS procurement choices**. Every sourcing hole is now either:

- bound to one exact JLCPCB MPN/C-number and source path; or
- explicitly retained as a local/manual assembly exception (F101 and PA1616D U401).

The exact final procurement choices were rerun through the full recovered I32 ngspice qualification. The result is **PASS**.

### Final procurement-bound electrical margins

| Gate | Limit | Final result | Margin |
|---|---:|---:|---:|
| Normal 3.3 V minimum | > 3.116050 V | **3.12786634 V** | **+11.81634 mV** |
| 3.3 V maximum | < 3.600000 V | **3.57660977 V** | **+23.39023 mV** |
| Reverse allocation | > -0.300 V | **-0.06700731 V** | **+232.99269 mV** |
| Normal sequencing | 1 READY / 0 SNS faults | **17/17 conform** | PASS |
| L121 saturation | < 2.5 A | **0.942206123 A** | **+1.557793877 A** |

The high-reference case was independently run at a 1 µs maximum step and peaked at **3.5766084 V**, confirming the upper result is not a coarse-timestep artifact. The extra 30.08 µH L121 superstress also passed.

## Closed procurement inventory

| Refs | Final MPN | JLC # | Package | Procurement disposition | Simulation disposition |
|---|---|---|---|---|---|
| C152,C154,C165 | `CGA3E3X7R1H224KT0Y0N` | `C342967` | 0603 | JLC-listed SMT / sourceable | Electrical alias/same 220 nF 50 V X7R ±10%; no model delta |
| L121 | `BPCI00121280470M00` | `C6471075` | SMD 12x12 mm | JLC-listed SMT / pre-order path | 47 uH ±20%, 100 mΩ DCR, 2.5 A Isat/Irated; full transient + 30.08 uH superstress PASS |
| R155 | `PTFR0603B11K8N9` | `C19679768` | 0603 | JLC-listed SMT / pre-order path | 11.8 kΩ; modeled ±0.33% total lifetime/temp/drift corner; PASS |
| R156 | `PLT1206Z5051LBTS` | `C4074185` | 1206 | JLC PRE-ORDER | 5.05 kΩ ±0.01%, 5 ppm/°C; modeled ±0.16% total corner; exact final candidate PASS |
| R160 | `RT0805BRB076K34L` | `C864499` | 0805 | JLC PRE-ORDER | 6.34 kΩ ±0.1%, 10 ppm/°C; modeled ±0.33% total corner; exact final candidate PASS |
| R161,R163,R170 | `PTFR0603Q1K00N9` | `C23067434` | 0603 | JLC sourceable | 1 kΩ ±0.02%, 10 ppm/°C; modeled ±0.25% total corner; PASS |
| R162 | `PTFR0603Q4K70N9` | `C23067437` | 0603 | JLC-listed SMT / pre-order path | 4.7 kΩ ±0.02%, 10 ppm/°C; modeled ±0.25% total corner; PASS |
| R169 | `PTFR0603B3K01N9` | `C2692830` | 0603 | JLC sourceable | 3.01 kΩ ±0.1%, 10 ppm/°C; modeled ±0.30% total corner; exact final candidate rerun PASS |
| U101 | `LTC4367HMS8#PBF` | `C688370` | MSOP-8 | JLC sourceable | Same H-grade LTC4367 electrical behavior; existing U101 behavioral model carries over; PASS |
| F101 | `UNCHANGED` | `LOCAL INSTALL` | existing | Explicit local/manual assembly | Existing I32 behavior retained |
| U401 | `UNCHANGED` | `LOCAL INSTALL` | existing module | Explicit local/manual assembly; intentionally excluded from JLC substitution mission | Not part of substitution qualification |

## Known redline implementation work

These are **not unresolved engineering decisions**. They are the implementation scope we can now begin:

1. R156: change footprint from 0603 to **1206** for `PLT1206Z5051LBTS / C4074185`.
2. R160: change footprint from 0603 to **0805** for `RT0805BRB076K34L / C864499`.
3. L121: adapt/check land pattern, courtyard and placement for `BPCI00121280470M00`, SMD 12x12 mm.
4. Update MPN/JLC/datasheet metadata for all substitutions.
5. Regenerate BOM/PnP and rerun native ERC, DRC, unconnected, schematic/PCB parity, assembly and source-binding gates.
6. Preserve U101 qualification note: `LTC4367HMS8#PBF` is functionally accepted, but it is not represented as the `#W` automotive controlled-manufacturing ordering option.
7. Preserve F101 and U401 as explicit local/manual assembly exceptions.

## Thermal / physical boundary

The existing I32 stacked board-region screen is **113.697 °C**. The final 125 °C-rated R156/R169 choices retain about **11.303 °C** of board-region screening margin, with resistor self-heating only milliwatt-scale. This is sufficient for the desktop redline gate; actual board/device temperature remains a first-article physical validation item.

## Reproducibility

- Repository: `tranquilWorks/gr86-cca-telemetry`
- Design PR: `#46`
- Pre-redline CAD baseline head: `e5ef8425dbe59c99e99eabb75c04342a47b27561`
- Qualification branch: `agent/i32-jlc-substitution-spice`
- Qualification head: `f27f48357ae49480ce82f324f700159c732640ef`
- Final procurement workflow run: `34899316734`
- Solver: ngspice 42 / KLU
- Final solver status: **PASS**

The replay sources live on the qualification branch at:
- `docs/engineering/rvb22/analyses/i32/substitution_spice_qual.py`
- `docs/engineering/rvb22/analyses/i32/final_procurement_spice_qual.py`

## Final statement

**The substitution package is fully ready to enter redline.**

There is no remaining non-GPS sourcing-selection question and no unmodeled electrical candidate in the final set. The next work is CAD implementation and post-redline verification, not further candidate selection.
