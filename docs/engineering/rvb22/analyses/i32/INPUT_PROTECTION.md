# I32 automotive input trajectory and component-stress assessment

The fixture is an explicit engineering envelope for a fused, switched cabin source. It is not a recovered OEM transient specification and is not ISO qualification. Final source identity and every accepted/rejected run are indexed in `FINAL_EVIDENCE.json`. Extrema below combine the retained eleven selected input cases and six completed supplementary cases, including the successful exact repeat of the initially incomplete unloaded-start record. Results use every finite sample, not the decimated plotting traces.

## Applied source envelope

| Event | Source fixture at harness input |
|---|---|
| Normal | 12 V nominal, intended steady on-window9-16 V; 0.1 ohm source resistance, 10 uH harness inductance. |
| Power-up | 0-to-12 V over1 ms after1 ms off; unloaded and loaded; downstream input MLCC maximum1.265 nominal. |
| Load dump | 12-to-100 V over5 ms; 400 ms plateau; 5 ms recovery; 2 ohm during the pulse. |
| Fast positive | 12-to-50 V over1 us; 50 us plateau; 1 us recovery; 2 ohm during the pulse. |
| Negative | 12-to-minus150 V over1 us; 2 ms plateau; 1 us recovery; 10 ohm during the pulse. |
| Reverse battery | minus14 V for60 ms, then recovery to12 V. |
| Jump/OV | 24 V for40 ms, with1 ms transitions; functional disconnect and recovery expected. |
| Crank/UV | 6 V for30 ms, 0.1 ms fall/1 ms recovery in the component-stress fixture; the cascade also tests a200 ms dip. Reset/restart during this fault is intentional. |
| Clamp routing | 0.06 ohm local lead allowance; 30/100/300 nH sensitivity; finite TVS capacitance and a low-Coss/Miller case. |
| Temperature/repetition | Q101 case and clamp/resistor local temperature allocated at125 C; hot/cold TVS envelopes include125 C and minus40 C. Single events; separate voltage pulses by at least60 s and restore the initial thermal state. Repetitive pulse qualification is additional. |

The final supplementary load is **0.75 A at VIN5, U121's input**, above5 V. It is a deliberately high short stress, not0.75 A at the5 V output and not a new sustained product allocation. At nominal VIN5 around10.7 V it exceeds the input power needed for the main0.75 A stress plus the other5 V consumers. R101 is exercised at +/-6%; the original eleven cases also retain the distinct clamp-lead extremes. The old low-impedance100 V/1 us fixture remains outside this envelope and outside the reliable range of the simple Q101 model; its ringing was not silently waived as a qualified automotive pulse.

## Source changes and stress-to-rating comparison

| Component/path | Calculated envelope | Rating/bound and disposition |
|---|---|---|
| Q101 STD25NF20 | VDS130.493 V maximum; VGS minus0.5537 to12.941 V; current10.351 A; instantaneous positive power417.88 W. | 200 V VDS, +/-20 V gate. Maximum derated SOA utilization0.52235 at the125 C case allocation. Keep part; do not use voltage rating alone as SOA proof. |
| Q101 SOA | Each contiguous interval with VDS>1 V and ID>10 mA is expanded by one adjacent sample and rounded **up** to10 us/100 us/1 ms/10 ms. | Conservative lower boundaries of ST Fig.2:60 A ceiling and6000/2400/600/240 W respectively, multiplied by(175-125)/150. No interval is extended into an invented DC SOA; no avalanche credit. The largest on-state instantaneous power3.424 W is separate from linear-mode pulse SOA. |
| D101 | Reverse277.609 V; forward peak10.353 A, microsecond event. | **Changed S5D to S5JHE3_A/H,600 V** in the same SMC package. Published5 A average and100 A8.3 ms surge provide a much larger surge envelope; event duration/current and hot solder-lead temperature still require correlation. No claimed reverse-avalanche operation. |
| D105 | 2.1605 A,348.46 W,74.12 uJ positive clamp energy; about3.03 us above1 mA. | **Added SMCJ110AHE3_A/H**. At125 C the conservative10 us pulse-curve bound is2000 W after derating. A348.46 W x10 us enclosing box is3.485 mJ, below the20 mJ corresponding bound. The100 V load dump is below the cold breakdown allocation. |
| D103 SMCJ24A | 4.1693 A,139.96 W,349.85 uJ; about4.65 us above1 mA. Protected rail33.569 V. | Retained. Same conservative2000 W/10 us hot pulse bound encloses this event. This is a pulse comparison, not permission to dissipate arbitrary joules at any duration. |
| D102 SMAJ30A | 5.094 mA,0.20634 W,83.20 mJ over approximately405 ms. Controller feed40.5078 V. | Retained. Treat the load dump as a **steady thermal bound**, not a10 us TVS event. At a125 C lead allocation and an explicitly allocated60 K/W junction-to-lead bound (twice the published30 K/W typical metric), Tj<=137.38 C versus150 C. That thermal allocation is a physical acceptance condition, not a guaranteed datasheet maximum. |
| D104 BZT52H-B15-QX | No positive avalanche in the selected records; Q101 gate remains within +/-20 V. | Retained15 V gate clamp. Forward conduction of the controller/gate network is included in the source; the gate-voltage envelope is the controlling result. Zero modeled avalanche energy is not proof of zero physical switching current. |
| R101 | Peak153.08 V and1.974 W for a few microseconds; worst dump plateau bounded0.3115 W including low resistance/life. | **Changed to12.1 kohm/1 W CRCW2512**.125 C steady bound1 W x30/85=0.35294 W. A conservative3 ms/6 W room-temperature pulse-curve bound becomes2.1176 W at125 C and encloses the shorter peak. Working voltage is separately below the2512 rating. |
| R110 WSL2512R4700FEA | Peak30.11 W for microseconds; full-resolution resistor event energy retained. Final0.75 A fixture gives0.2672 W nominal on-state dissipation. | Retained. Vishay's exact-value calculator plus published WSL voltage/temperature limits controls pulse overload. Using deliberately lower0.8 W-at70 C and2.4 J/ohm wire-energy bounds gives0.36 W at125 C and0.7809 J wire energy; the enclosing10 us peak box is0.3011 mJ. The short0.75 A fixture does not authorize that current continuously through the fuse. |
| U101 LTC4367 | VIN/SHDN minus0.00057..40.5078 V; UV up to10.8538 V; OV up to4.0911 V; gate drive minus0.1909..40.781 V; VOUT minus0.00166..33.5691 V. | Retained. Compare individually with VIN minus40..100 V, UV/SHDN minus0.3..80 V, OV minus0.3..5 V, VOUT minus0.3..80 V, GATE minus40..75 V. A common80 V limit would be wrong for OV. |
| U121/caps | VIN5 up to32.6125 V; protected node up to33.5691 V. | Retained100 V U121 and source-rated input capacitors. The transient occurs before the functional disconnect; no claim that protected voltage always equals12 V. |
| F101 0885001.DR | Largest **whole-record** integral0.04083 A²s; pulse-only I²t is reported separately and is much smaller. | 1 A,500 VDC fuse retained.0.80 A²s is nominal melting data, not a guaranteed clearing/minimum non-opening limit.105 C maximum local ambient, approximate93% temperature x75% continuous-use factors give0.69 A screening allocation. Confirm final source fuse/harness coordination; do not infer clearing from the voltage-controller model. |

Vishay's calculator returns different material/energy parameters by resistance: the saved0.30 ohm R158 result is4.33 J/ohm,170 C,0.90 W,5x overload; the saved0.33 ohm hypothesis is3.2 J/ohm,0.84 W. They are not the same dataset. R158's selected dissipation is below even the lower0.47 ohm conservative screen; the exact0.30 ohm values are preserved as manufacturer evidence.

## Approximation boundaries

Q101 is a transparent Level-1 MOSFET approximation, not an ST macromodel. Gate pull-up/down bounds, Miller/input/output capacitances, diode capacitance, source R/L and clamp slope/temperature are explicit. The trajectory is compared independently with the manufacturer SOA. The model has no semiconductor avalanche or fuse-clearing mechanism. Maximum gate charge and a10 us controller turn-off allowance bound the fixture; the published6 us figure is tied to its stated2.2 nF load and is not transplanted as a universal maximum.

The LTC4367 detects voltage faults; it is not a downstream current-limiting switch. A sustained downstream short within its allowed voltage window is outside this voltage-transient acceptance and must be covered by fuse/wiring/current-source coordination. An open primary ground can create alternate RF/sensor/programmer returns; existing single-return and lost-ground restrictions remain controlling. No chassis-bonded programmer is permitted during vehicle operation.

The selected raw clamp and600 V diode resolve the actionable voltage/SOA findings within the declared harness envelope. Changing clamp lead inductance, source impedance, pulse repetition or local temperature invalidates the corresponding numerical bound. Final qualification must measure both clamp voltage/current and Q101 VDS/VGS/current together; testing only the3.3 V output cannot confirm these component stresses.

## Primary references

- [ST STD25NF20](https://www.st.com/resource/en/datasheet/std25nf20.pdf), maximum ratings, thermal data and Fig.2 SOA. The125 C SOA curve scaling is an explicit engineering bound.
- [ADI LTC4367](https://www.analog.com/media/en/technical-documentation/data-sheets/ltc4367.pdf), absolute pin limits, electrical timing and gate-control application conditions.
- [Vishay S5](https://www.vishay.com/docs/88931/s5a.pdf), S5J600 V selection, forward/surge data; [SMAJ](https://www.vishay.com/docs/88390/smaj.pdf), and [SMCJ](https://www.vishay.com/docs/88394/smcj.pdf), pulse-width and temperature curves and thermal conditions.
- [Vishay CRCW](https://www.vishay.com/docs/20035/dcrcwe3.pdf),2512 power/working voltage and pulse curves; [CRCW-HP](https://www.vishay.com/docs/20043/crcwhpe3.pdf), R165 pulse part; [WSL](https://www.vishay.com/docs/30100/wsl.pdf) and [manufacturer pulse calculator](https://www.vishay.com/en/resistors/calculator-power-metal-strip/), exact resistance/material data and derating equations.
- [Littelfuse885](https://www.littelfuse.com/assetdocs/littelfuse-fuse-885-datasheet?assetguid=f4426cf6-2a53-41b3-b8da-211f7a44fad1),1 A500 VDC product and datasheet current-temperature/I²t conditions.

Reference files, retrieval URLs and hashes are retained where bytes were available. Manufacturer curves are not modeled silicon measurements, and no supplier or vehicle acceptance is claimed.
