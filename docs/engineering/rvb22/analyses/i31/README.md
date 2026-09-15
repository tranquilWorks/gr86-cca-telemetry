# I31 — tentative normal-power sign-off, with residual risks

## Disposition

**Tentative normal-power / first-article sign-off only.** The complete derivative power-chain model predicts that 12 V can start the protected input, 5 V stage, main 3.3 V stage and delayed ESP32 EN under the adopted release profile. A limited first-article build for controlled bench qualification is reasonable. This is **not** an all-corner electrical pass, automotive-survival certification or unrestricted vehicle/product release.

Two substantive residual risks remain: uncertain-controller startup overshoot and reverse discharge through U151 on power removal. They are not waived by this tentative disposition. The original 290-row register has not been rewritten to conceal them. No production PCB/BOM/firmware changes, physical tests, supplier approvals, orders, flashing or merges occurred in I31. No CI polling was used as a substitute for engineering.

Reviewed head: `2a60b17e086ba2ddf0fc663f1889748d02ded7f7`; PCB SHA-256 `a04f42b358fa65a332128115a7b648e1a2297531ecb47466ac24697de536a936`. The I29-to-I30 comparison contains only six analysis additions, no CAD/firmware changes. Native XML SHA-256 `3cc5122bbbc2653570be75a87885d7bc0189e3a511f1c3c515fcf69feddeeedf` came from the source-matched I28 archive. Twelve explicit part/configuration checks passed; this is inspection of existing native output, not a new KiCad run.

## Executed work

**132 transient computations completed**, including calibration, sensitivity and deliberately wrong-feedback experiments. This is not a claim of 132 product passes. Five failed setup/export/timeout attempts are preserved separately. Eleven integrity/replay regression tests passed. Standalone replay reproduced the nominal full waveform SHA and correctly retained the wrong-feedback overvoltage result.

- 16 upstream calibration runs and two corrected holdout fixtures.
- 18 full input/buck/buck/reset cascade runs.
- 64 U151 passive/reference/timing combinations with the central assumed controller.
- 18 experiments across nine uncertain controller coefficient sets.
- One completed hybrid with **TI's unchanged LM5164-Q1 switching model driving the U151 derivative**.
- Four extra risk probes and nine unadopted assembly sensitivities.

`lm63615_derivative.lib` is an original current-mode architecture approximation, not decrypted TI content. It includes finite current response, uncertain Type-II control, soft-start, delayed FPWM negative-current availability, current-command saturation, external RLC dynamics and signed input-power coupling. There is no ideal regulated 3.3 V source or artificial 3.6 V output clamp. L151 uses the published 77.1 milliohm maximum DCR at25C, plus a hot-copper sensitivity. Fitted C206470uF/R15882milliohm and R15310milliohm remain in the model.

The longer-interval U121 approximation is an empirical averaged surrogate fitted to the previous completed vendor-model load-step trace. Its effective reference `5/4.09` is a calibration parameter, **not** the manufacturer's actual1.2V reference. Calibration error is about14.4mV RMS; independent startup holdouts disagree by about52–56mV RMS, and the low-input settled surrogate overpredicts by36.8mV. It is not a high-accuracy COT replacement. U151's actual internal compensation remains unknown.

## Main results

| Experiment | Computed result | Scope |
|---|---|---|
| Full derivative cascade,12V raw,450mA released load | Main settles3.3602V; startup peak3.4990V;5V peak5.0759V | Nominal predicted functional pass |
| Sequencing | Main95% near41.38ms; EN release near61.33ms | Includes modeled32ms input reconnect and20ms supervisor delay |
| 9/14.4/18V raw | Central-model startup/regulation complete | Not all-temperature line regulation |
| Settled main load20→450→750→20→450mA | Main3.3101–3.4495V after63ms | Brief750mA stress, not sustained thermal release |
| 450mA throughout startup | Starts; peak3.4605V | Does not depend exclusively on20mA pre-reset load |
|6V crank, reverse-input recovery,24V OV/recovery | Disconnect/reset/restart computations complete | Not automotive pulse/SOA qualification |
|2us→1us maximum timestep | Nominal main peak changes about1.4uV | Numerical agreement, not physical accuracy |

The real-U121 hybrid completed5.8ms and2,489,236 samples without abort. Main peak3.4990V;5V peak5.0599V; final0.5ms5V average4.9774V. U121 switching-current peak1.2254A; U151's1.4491A is an **averaged**, not switching, current. Main is still relaxing at the endpoint (final0.5ms average3.4726V). The20ms reset delay cannot complete within5.8ms: **hybrid evidence corroborates early startup only**, while later settling/EN/workload use the longer derivative. TI library SHA `e11ddf6995163f98eda6205de6a7cb74c8a3982b7328467de8d806286e894b5d`; it is not redistributed.

## Findings retained, not passed

**I31-PWR-01 — unknown-control startup margin.** A slow assumed controller reaches3.7353V (about3.50ms above3.6V). A low-ESR/high-reference case reaches3.6069V (about81us above3.6V). These are not proven silicon failures, but they are not passes. The64 central-controller corners peak at3.5945V; the remaining5.5mV before ripple/model/measurement allowances is insufficient for a robust all-corner claim. A separate DC source ceiling calculation is3.4183V including reference/divider and FB-leakage allowances, not a transient bound. Reducing C206 improved some startup cases while worsening load-release excursions; no unvalidated value change was adopted merely to improve a plot.

**I31-PWR-02 — reverse discharge.** The power-off model allows U151 VIN to fall0.584V below output. Generic body-diode current peaks31.1mA, with0.599mC charge and0.335mJ energy over the recorded interval. Small modeled energy does not waive TI's recommendation to prevent VIN falling more than0.3V below output. An unadopted output-to-input bypass (anode3V3 source,cathodeU151VIN) with assumed0.25V drop plus0.2ohm reduces the differential to0.2574V; a0.35V version does not meet the screen. A real diode's part/temperature/leakage/routing qualification is still required. No diode was added to production CAD.

**I31-PWR-03 — startup loading scope.** A constant750mA from power-on cycles and never releases EN in the approximate cascade.450mA startup and brief750mA steps after regulation succeed centrally. The450mA release allocation must not be reinterpreted as750mA guaranteed startup or hot continuous capacity.

## Gates before unrestricted use

Apply the retained input/harness contract and I26 qualification plan. Capture rails/current/EN during startup, allowed load transitions, crank and power removal. Main must never exceed3.6V including measurement uncertainty; a3.55V engineering headroom target is desirable. Retain3.443V steady-profile bound, active minimum3.0V and5V range4.75–5.25V. Require correct reset hold/release and no unintended resets. Resolve the reverse-discharge recommendation with verified behavior or an approved external bypass before unrestricted release. Same-footprint passive tuning or a diode assembly addition may suffice if needed; absence of a future PCB respin is not guaranteed.

Preserve160MHz,BLE+3dBm,noWiFi,<=120notifications/s,<=0.45A sustained,>=80% efficiency or established loss alternatives. I25/I26 thermal correlation remains mandatory:65C bulk air,U201 immediate air<=85C,stability<0.1C/min for30minutes,zero unintended resets.851 accessory local environment<=60C. This SPICE work does not explain or exclude RevA's five-minute failure.

Unmodeled or approximate: exact proprietary compensation, bootstrap/VCC dynamics, switching-edge parasitics, semiconductor thermal behavior, actual fault/hiccup states, saturation curves, MOSFET/TVS pulse SOA, quiescent current and exact discharge state machine. Capacitor retention, DCR/ESR, reference/timing and controller-family sweeps are explicit selections, not an exhaustive statistical manufacturer-corner campaign. The auxiliary44.1uF aggregate includes a reflected GPS-LDO approximation, not44.1uF literally connected to5V. Efficiency is an assumption, not an achieved result.

## Reproduction and full evidence

The two checked-in source files provide the exact nominal full derivative replay:

```sh
ngspice -b nominal_cascade.cir
```

Run from this directory. The recorded engine is ngspice39/Debian39.3+ds-1. Confirm the final saved time is0.12s, all values finite and no abort diagnostics; exit status alone is insufficient. Nominal deck SHA `21b780b0de48c5f5179759924514af041bea33b979d77cfed38fbc895828ff29`; model SHA `4f6a4e03df1ed2ffde2e171591b34728107e5ac444baba3c9c5afe4732a6ef90`; replay waveform SHA `4869168e6d7bf9f719eda9a3237988e096002080e98735ccaf75fcd7a7d9e8ad`.

The accompanying conversation artifact **GR86_RevB_I31_Tentative_Power_Signoff.zip** contains the complete report,132 case decks/results, failed attempts, source audit, waveform hashes, compact plots/traces, generic generators, validated replay/integrity scripts and871-member integrity manifest. Archive SHA-256 `740fe6b6ba41065643569e2d20c0a6af0fe544fb3a8e421d8490c89d245df21e`. Full-resolution traces are regenerated by replay; extrema came from the original full traces, not the compact plots. Neither vendor libraries nor engine binaries are redistributed. This repository entry is the compact core, not a claim that every archived log is committed here.

Primary sources:
- https://www.ti.com/lit/ds/symlink/lm63615-q1.pdf
- https://www.ti.com/product/TPS3808-Q1/part-details/TPS3808G33QDBVRQ1
- https://www.coilcraft.com/en-us/products/power/high-voltage-inductors/xgl/xgl5030/xgl5030-153/
- https://www.espressif.com/sites/default/files/documentation/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf
- https://www.ti.com/lit/zip/snvmbp2

Online TI parsed text identifiedRevJ while page screenshots identifiedRevI; the cited control/startup and reverse-discharge recommendations were consistent. No unobserved proprietary behavior is asserted.
