# I30 — executed derivative SPICE, U121 scope

## Outcome

**A derivative SPICE route is working. Thirteen independently derived U121 switching-model experiments completed locally. Whole-board power startup and automotive survival are NOT signed off by this work.** There were no production ECAD changes, physical tests, fabrication orders or merges. No CI completion was required for this publication.

The reviewed source is `ccbf75e8da97895afa900d5a4ae53cc0641fc97c`, PR #46, branch `codex/rvb24-coordinated-closure`. Authored PCB SHA-256 is `a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936`. `SOURCE_COMPONENTS.json` freezes the U121 external network extracted from the matched native schematic netlist, including exact MPNs and pins. It does not automatically validate a later CAD change.

## What was simulated

Engine: ngspice 39 / Debian 39.3+ds-1, with the matching XSPICE analog code-model library loaded. `cot_derived.lib` is independently derived from the published constant-on-time architecture; it is neither a TI-validated macromodel nor a decrypted library. Inductor/capacitor dynamics, switched power delivery, finite switch resistance, feedback/ripple injection, external EN divider, soft-start ramp and simplified peak/valley limits are simulated. There is no ideal regulated 5 V output source.

The fitted network includes L121 47 uH, R121 31.6 kohm timing parameter, R122/R123 309/100 kohm, R124/C125/C126 43.2 kohm/3.3 nF/100 pF ripple injection, C127/C128 22 uF each, input capacitors, and the 100/26.1 kohm EN divider. The bootstrap, internal bias and PGOOD circuits are outside this model.

## Actual results — derivative-model predictions

Thirteen completed runs comprise twelve source-configuration/sensitivity cases (including an expected EN-off case) and one wrong-feedback negative control. Each reached its requested end time with finite waveforms. `RESULTS_SUMMARY.json` records the numbers and explicit nonclaims.

| Experiment | Result |
|---|---|
| Nominal release-equivalent resistive load | 4.99742 V settled; 0.599 A startup peak inductor current |
| First crossing of 4.75 V during nominal startup | 2.904 ms from simulation start |
| 8 / 13 / 17 V converter-input fixtures | 4.96764 / 5.01314 / 5.03028 V settled |
| 0.10 to approximately 0.75 A load transition, 10 us rise, on the 5 V output | 4.85633–5.01754 V after the step; 0.964 A peak inductor current |
| Selected 50% large-capacitance, 80% inductance, 150% resistance sensitivity | 4.99475 V settled |
| -2% / +2% reference sensitivity | 4.90099 / 5.09384 V settled |
| Maximum timestep 20 ns to 10 ns | Mean output changed by approximately 9.50 uV |
| 7 V converter input | Off, consistent with the external EN-divider model |
| Deliberately wrong R122 618 kohm, simulation only | 8.65357 V: overvoltage detected, not accepted as the product configuration |

The default 10.6877 V fixture is at the CONVERTER INPUT, representing the earlier conservative operating-point calculation for a 12 V battery input. This is not a new completed end-to-end automotive input simulation. The nominal resistive load is approximately 0.467 A at 5 V. The load step is on the 5 V stage, not the downstream 3.3 V rail.

The scoped voltage screen is 4.75–5.25 V after regulation, with peak inductor current below the selected 1.25 A peak-limit reference. Timestep agreement supports numerical consistency, NOT physical accuracy. The nominal modeled output ripple is about 0.96 mV peak-to-peak, excluding real switching-edge ringing and layout parasitics. Do not replace the established 80% thermal-design efficiency assumption with the apparent efficiency of this simplified loss model.

## Limits and uncompleted attempts

The model uses nominal typical 0.725/0.34 ohm switch resistances, 0.134 ohm nominal-reference-temperature inductor DCR, assumed capacitor ESR, 100 pF switch-node capacitance, and smoothed comparator/one-shot transitions. Detailed bootstrap starvation, gate charge/deadtime, inductor saturation, capacitor DC-bias/temperature guarantees, exact foldback/sleep behavior, operating quiescent current, thermal shutdown, semiconductor safe operating area and extracted PCB parasitics are not represented. Selected sensitivity cases are not an exhaustive tolerance or Monte Carlo campaign. The simplified valley-limit gating is exposed rather than claimed to be the exact internal device state machine.

The larger hybrid model (protector, switching U121, averaged U151 and reset supervisor) aborted numerically before its requested endpoint. Later functional protection models also failed to complete undervoltage, overvoltage, reverse-input and illustrative surge sequences. These are unaccepted simulation attempts, not observed hardware failures and not passes. Their logs/decks and rejected early prototypes are retained in the accompanying I30 evidence archive.

Therefore the complete **12 V -> 5 V -> 3.3 V -> ESP32 EN sequence remains unverified by SPICE**. U151's internal compensation remains uncorrelated and its acquired vendor library encrypted. Automotive surge survival and the historical five-minute Rev A failure are not ruled out by these millisecond U121 experiments. This work does not grant fabrication clearance or change physical qualification requirements.

The I29 finding also remains: loading the correct XSPICE libraries allowed the unmodified LM5164-Q1 vendor model to load, but those vendor-model experiments were numerically unusable/incomplete. An original model-loading error was not evidence that all SPICE approaches were impossible.

## Replay without CI

Install Python 3.10+, NumPy 2.x and ngspice with matching XSPICE libraries. From this directory:

```sh
python -m pip install 'numpy>=2,<3'
python replay_converter.py --ngspice /path/to/ngspice --output /new/output/directory
```

Add `--code-model-dir /directory/containing/analog.cm` for a relocated ngspice installation without its default code-model paths. The code-model path must contain no spaces for this ngspice command. `--case cot_nominal_v2` selects one case. Existing output directories are rejected. Aborted/partial waveforms are never accepted just because ngspice emitted measurements or returned normally. Wrong-feedback and EN-off cases have explicit expected behavior rather than being counted as nominal 5 V passes.

The standalone portable entry point was rerun for the nominal case: 8 ms completed, 1,249,195 samples, 4.997420669412825 V mean output. The accompanying `GR86_RevB_I30_SPICE.zip` contains the detailed report, engine logs, input decks, full result JSON, decimated representative waveforms, plot, replay verification and rejected attempts. Full-resolution waveforms are regenerated by the replay; the archive does not pretend decimated data are full resolution.

## Primary model references

- TI LM5164-Q1 datasheet: https://www.ti.com/lit/ds/symlink/lm5164-q1.pdf
- TI LM63615-Q1 model/product page: https://www.ti.com/product/LM63615-Q1
- ngspice behavioral/XSPICE support: https://ngspice.sourceforge.io/xspice.html
- ngspice compatibility and encrypted-model limitations: https://ngspice.sourceforge.io/modelparams.html
- Coilcraft MSS1246T series: https://www.coilcraft.com/en-us/products/power/shielded-inductors/molded-inductor/mss/mss1246t/
