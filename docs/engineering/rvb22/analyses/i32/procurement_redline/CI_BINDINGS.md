# Current I32 hosted verification bindings

The first engineering publication is commit `1ce3f9f9b8bdb68dc275334d22b63dd21d40e058`. Its exact source passed hosted native run [34916258259](https://github.com/tranquilWorks/gr86-cca-telemetry/actions/runs/34916258259), including native CAD, target firmware compilation, independent copper/export verification and the current I32 thermal screen.

That publication also exposed stale automated review assumptions predating I32: the 153-placement I28 handling inventory, old PCB source hashes, an obsolete R158 contact-notch expectation, and an I27 job that attempted to replay and publish historical authoring recipes. The C04 shell pipeline reported success despite a source-binding traceback; the successor now uses pipefail and requires its result file.

The follow-up changes only verification code, workflow bindings and this evidence index. Native CAD, models, BOM/CPL, manufacturing package, executed electrical/thermal results and the four protected handoff documents are unchanged.

- Native feedback verification retains all fourteen CAD-plus-firmware postconditions and binds PCB SHA256 `52ca35cf8cb4e2b4a27d053686ee3a85564f1e94dfdb7dcb4bca4083dd527312`.
- The product review retains all 39 existing negative-path/regression tests with current I32 expectations. It checks 177 exact fitted identities, the thirteen frozen substitutions, two local installations and unknown-MPN rejection. Existing numeric MSL evidence is reused only for the exact MPN; absent limits remain null and supplier-controlled. L121 manual/wave handling and U101 pedigree downgrade stay explicit.
- The unadopted historical C02 contact/cooling replay is replaced in active CI by the adopted I32 C05/W02/T03 thermal analysis at both 0.5 and 0.25 mm, retaining the six analytic network tests. No C02 hardware is adopted.
- C04 retains its twelve release-profile invariants and runs the same current I32 release/stress solver with exact source binding. No thermal or electrical threshold is relaxed.
- I27 retains the original 290-row ledger invariants and ground-return screening limits, then verifies current I32 source, every indexed file, the full waveform parts, fourteen aggregate gates and the regenerated manufacturing package. It cannot write to the branch or replay the historical authoring recipe.
- Original workflow bytes are archived under `history/pre_redline/ci/`. Historical analysis scripts and results remain intact.

`ci_verify.py` recomputes existing evidence checks and requires aggregate and package verification outputs to be byte-identical. It is evidence verification, not a new ngspice or hardware-test claim. Current hosted run outcomes are recorded on PR #46 and its commit checks; initial stale-workflow failures are retained in Actions for traceability.

The current root register is an eleven-row I32 supplement; the original 290-row ledger remains at its explicit historical path. Hosted checks validate both scopes separately. Root register/gate descriptions and affected I32 finding rows now reflect the current source, counts, margins and thermal conditions; their prior bytes are preserved under `history/pre_ci_binding/`. No original criterion, acceptance limit, native source or manufacturing artifact is changed by that documentation refresh.
