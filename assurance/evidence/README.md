# GR86 integration evidence

This is software integration/custody verification, not engineering approval.
`INTEGRATION.json` states exact scope, statuses and limits. `SOURCE_VERIFICATION.json`
binds 219 selected inputs to discovery bytes and records the existing read-only
procurement/source equivalence checks. Prior board evidence stays in its original
location and retains its historical effectivity.

- `custody-tests.log`: 24 tests, PASS; temporary synthetic repositories plus the
  real catalog discovery binding. No actual reviewer or hardware work.
- `procurement-tests.log`: seven existing procurement regressions, PASS.
- `source-verification.log`: existing `validate_sources()` and `verify_cad()`
  passed for 88 sourced part identities, 177 fitted references and 354 schematic/
  PCB procurement property records. Archived capture bytes were verified; stock
  was not queried. Maintained and sourced CAD physics matched.
- `INSTALLED_SMOKE.json` / `installed-01.log`: 12 CLI commands, 14 real MCP calls,
  six draft reviewer packets, expected negative cases; transport/custody PASS.
- `FINAL_INTEGRITY.json`: final verification of both assessment seals and all
  six packet seals, PASS. Packet creation is not execution of independent review.
- `installed-smoke-01.tar.gz`: complete original external capture/run/packet
  evidence, transcripts, negative probes and original immutable seals. Verify its
  SHA256 against `INTEGRATION.json`, extract outside this checkout, then use the
  pinned framework's `verify-evidence --run PATH` on the assessment/packet roots.
  Recorded absolute paths identify the original execution host; do not rewrite
  sealed records when relocating evidence. This archive contains public GR86
  source bytes, not framework source or ACT board data.

The actual shared engine returned overall BLOCKED, with 15 machine findings for
unsupported native operation/incomplete criteria. KiCad ran only `--version`:
no fresh ERC/DRC/parity/export/refill was performed. Historical KiCad 9 zero counts
are not substituted for fresh verification. Six independent reviews and physical,
vehicle, supplier and unit acceptance are NOT_RUN. The run's complete gate matrix
is preserved without replacing blocked/unperformed states by success.

The source checks invoked the existing procurement completion module read-only,
with `PYTHONDONTWRITEBYTECODE=1` and its installed `sexpdata` dependency:
`validate_sources()` then `verify_cad(sources)`. Inputs were SHA256-compared before
and after. Full `build.py verify` was not invoked: it writes reports and requires
additional complete archived outputs. Its prepare/package stages were not run.
Fresh firmware compile, SPICE/thermal reruns and package/native generation were
outside this integration. No evidence record claims those operations passed.

CI status is intentionally not predicted inside its own input commit. Consult
that exact commit's `PCB assurance integration / custody` check and the PR handoff.
The workflow runs the 24 software tests only; it does not fetch the unavailable
external framework repository, perform native checks or grant approval.
