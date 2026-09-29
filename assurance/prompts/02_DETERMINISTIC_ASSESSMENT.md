# Fresh GR86 deterministic assessment

```text
Follow assurance/README.md using the pinned external wheel and a new external
session directory. Run bridge.py doctor, prepare and audit; retain exit codes,
raw output, tool/version identity, source/config/code hashes and unperformed gates.
Inspect drift before --accept-source-drift; reconcile added native files explicitly.
Never reset or modify canonical files. Read the actual summary, findings, runtime
native result and bridge receipt; verify all evidence seals before/after use.

Expect BLOCKED for unsupported KiCad 9 PCB format with this 0.2.0 backend. Its
KiCad 10 version probe is not fresh ERC/DRC. Do not migrate or rewrite CAD, bypass
guards, run KiCad 10 exports on these sources, or treat historical KiCad 9 zeros
as fresh results. Missing native tools are a distinct blocker. Preserve all raw
states; only a separately qualified shared-framework compatibility update can
change native support. No engineering PASS follows from CLI/MCP transport PASS.

Run python3 -m unittest discover -s assurance/tests -v from the repo root.
For the existing procurement regressions, use their documented dependencies and
the existing procurement_completion tests. Inspect any further existing helper's
write paths before invoking it. Read-only validate_sources()/verify_cad() can
check archived captures and maintained-to-generated equivalence, but full build.py
verify writes a report and prepare/package mutate generated output: use a complete
disposable checkout only under a separately scoped verification task. A sparse
checkout cannot establish full manufacturing archive completeness.

Preserve historical native/firmware/SPICE/thermal/package results with exact
source hashes and scope. Do not report fresh compile, simulation, EMC/transient,
fit, thermal correlation, supplier acceptance or vehicle/unit results unless
actually executed under an authorized plan. Existing process limits and prior
failed/limited cases cannot be relaxed to obtain a clean run.

Empty approved mappings, unset JLC fields, mandatory Z1 applicability, primary
source gaps, reviewer isolation and held-out qualification remain separate gates.
Verify source hashes after every operation. If a late tool file changes a sealed
run, preserve that failed run and mark BLOCKED; do not delete/reseal it. Deliver a
source-bound findings/gate matrix and stop before repairs or external actions.
```
