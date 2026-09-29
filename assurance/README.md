# GR86 CCA PCB assurance

Findings-only integration for **GR86-REVB / I32-SOURCED-MANUFACTURING / JLCPCB**.
This reuses the external `pcb-design-assurance` 0.2.0 engine and the existing ACT
custody foundation. It adds one domain binding, source catalog, candidate review
routes and local prompts; it does not implement another engineering audit engine.
Read [ONBOARDING.md](ONBOARDING.md) and [DISCOVERY.md](DISCOVERY.md) first.

Source capture, installed CLI/MCP, sealed findings and six draft packet routes
work. **Fresh native assessment is BLOCKED by KiCad 9/10 incompatibility.**
Engineering criteria mapping and independent review qualification remain BLOCKED.
Do not equate successful software integration with board approval.

## Install the pinned framework locally

Use a separate Python 3.11–3.13 virtual environment outside this repository.
The owner's saved `PCB_DESIGN_ASSURANCE_HANDOFF.zip` contains
`pcb-design-assurance/dist/pcb_design_assurance-0.2.0-py3-none-any.whl` and the
framework source/evidence. The intended framework GitHub repository was unavailable at handoff;
do not install from an invented URL, a similarly named PyPI package, or an
unpinned editable checkout. Do not vendor framework source into this board repo.

Example for Linux/WSL, after extracting the handoff to a separate directory:

```bash
python3 -m venv /absolute/external/pcb-assurance-env
# Verify the wheel against framework.lock.json before installing it:
python3 - /absolute/extracted/pcb-design-assurance/dist/pcb_design_assurance-0.2.0-py3-none-any.whl <<'PY'
import hashlib,json,sys
from pathlib import Path
lock=json.loads(Path('assurance/framework.lock.json').read_text())
assert hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()==lock['wheel_sha256']
print('Pinned wheel hash verified')
PY
/absolute/external/pcb-assurance-env/bin/python -m pip install \
  /absolute/extracted/pcb-design-assurance/dist/pcb_design_assurance-0.2.0-py3-none-any.whl
```

The bridge verifies all 54 installed package files before it invokes the shared
engine. Optional MCP uses the framework's tested `mcp==1.30.0`; install it into
that same environment if needed. The framework requires **KiCad 10.0.6**, but this board is **KiCad 9.0.9**.
Installing KiCad 10 does not qualify the board format. Native checks remain
BLOCKED; never install, migrate, export or refill canonical CAD automatically. Preserve the user's
existing Codex provider/model and Qwen configuration.

## Use from this repository's root

Choose a new external session directory each time. Substitute actual absolute
paths; neither the session nor its output may be inside the canonical checkout.

```bash
python3 assurance/bridge.py doctor \
  --framework-python /absolute/external/pcb-assurance-env/bin/python

python3 assurance/bridge.py prepare \
  --out /absolute/external/gr86-session-001/inputs

python3 assurance/bridge.py audit \
  --workspace /absolute/external/gr86-session-001/inputs \
  --out /absolute/external/gr86-session-001/run \
  --framework-python /absolute/external/pcb-assurance-env/bin/python
```

`doctor` exits 3 after successful integration checks because engineering readiness
remains BLOCKED. `prepare` exits 0 for capture only. `audit` returns 1 for evaluated
FAIL, 2 for execution/custody errors, or 3 for incomplete assurance. Never interpret
shell success as engineering acceptance. Read `run/SUMMARY.md`, `findings.json`,
`summary.json`, raw `runtime/native/` evidence and the sibling `run.bridge.json`.

Do not reset a local branch to the discovery commit. If existing selected sources
changed, inspect the changes, reconcile applicability and use
`prepare --accept-source-drift --out NEW_PATH` to capture the actual current bytes.
That flag authorizes snapshot drift only; it never approves changed requirements.
New native files need explicit catalog reconciliation. Added/removed/tampered
capsule files, symlinks, source changes during capture/audit and changed framework
bytes are rejected. KiCad session/cache files are excluded from the native census.

`input-catalog.json` maps each copied file to its original path and discovery
hash. `obligations.json` routes fourteen GR86-specific review topics to existing
sources; it is not another requirements database. The generated `requirements.json`
is an explicitly unapproved projection, not copied numerical authority.
The empty BOM/CPL/runtime slots block unimplemented mappings. The raw existing
BOM, process and qualification records remain available as bound inputs.
The runtime primary-source authority catalog is also empty: MCP `get_sources`
returns no approved records until controlled source mapping is implemented.
The 219 captured input files remain individually bound in `capture.json` and the
artifact manifest; captured bytes alone do not establish source authority.

Approve and implement source mappings through a separate controlled change after
the requirements custodian reconciles sources and completeness. An approved
criterion needs the framework's real source/approval/hash records and appropriate
positive/negative/boundary tests. Do not change a generated capsule or remove its
seal to make it pass; revise the controlled integration and capture again.


## Independent review and feedback

Prepare a **draft** packet for each of the six roles:

```bash
python3 assurance/bridge.py packet --role mechanical \
  --run /absolute/external/gr86-session-001/run \
  --out /absolute/external/gr86-session-001/mechanical-packet \
  --framework-python /absolute/external/pcb-assurance-env/bin/python
```

The initial packet intentionally excludes generated maps/BOM conclusions,
observations, historic reviews and uncurated baseline narratives. It contains
native design only. A custodian must create and seal a **separate** reviewed packet
with approved requirements, exact primary documents, applicable source excerpts
and the framework review schema. Preserve each source hash/location and the
assessment snapshot ID. Do not silently edit the sealed generated packet.

Use the prompts under [prompts/](prompts/00_LOCAL_START.md). The design session
must not impersonate six reviewers. Before launching fresh sessions, qualify
packet-only read access, separate writable report/scratch areas and denied access
to canonical files, designer history, keys, supplier/hardware tools and credentials.
If that boundary is unavailable, stop independent review with BLOCKED; useful
deterministic findings may still be retained. No independent sessions ran here.

After sealed submissions, the custodian reconciles findings without discarding
contradictions. You approve dispositions. A separate repair task may then act on
accepted finding IDs only, followed by fresh affected-check and independent
re-verification. `import-review` in the shared CLI stores a schema/snapshot-bound
submission; it does not grant independence, approve a repair or close a gate.

## Optional local MCP

Create a repo-scoped configuration outside the checkout; this does not modify
global Codex settings or the framework's generic empty project registry:

```bash
python3 assurance/bridge.py mcp-config \
  --workspace /absolute/external/gr86-session-001/inputs \
  --run-root /absolute/external/gr86-session-001/mcp-runs \
  --out /absolute/external/gr86-session-001/mcp-config.json
```

The only project key is `gr86-revb-jlcpcb`. Run the server with the verified
environment's `pcb-assure-mcp` command and `PCB_ASSURE_MCP_CONFIG` set to that file.
For a Codex project MCP entry, use that command and environment variable; inspect
the installed local Codex help/config before adding it and preserve existing
providers and MCP entries. No credentials or new paid API route are required by
this integration. Restart/reconnect after each new capsule/config.

The nine tools are capabilities, doctor, validate_project, run_assessment,
get_report, get_findings, get_sources, get_requirements and get_supported_checks.
They expose no repair, approval, mutation, supplier or hardware operations.
CLI remains authoritative; MCP does not bypass the snapshot/coverage limitations.



Always run the installed framework's `verify-evidence --run PATH` before
consuming an assessment and after packet/MCP preparation. Native tools can leave
late session files: any added/changed file invalidates the seal. Preserve failed
runs without deleting files or resealing them. The GR86 smoke's seals passed;
its native backend stopped before design-tool execution, so this does not
qualify the shared framework's native lock lifecycle on other supported inputs.

## Verification

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s assurance/tests -v
PYTHONDONTWRITEBYTECODE=1 /absolute/external/pcb-assurance-env/bin/python \
  assurance/verify_installed.py --out /absolute/external/gr86-smoke-001
```

The first command runs 24 custody/configuration tests, including synthetic
negative cases and the catalog's discovery binding. The second needs the exact
installed framework and MCP dependency. For the recorded version-probe smoke,
KiCad 10.0.6 was on PATH; only `--version` ran. Its 12 CLI commands, 14 real MCP
calls, six draft packets and final seals passed. Expected native compatibility
BLOCKED is asserted; it is never relabeled as a native engineering PASS.
Independent sessions executed: zero. Retain new output directories per run.

The scoped CI workflow runs only software custody tests. Existing engineering
tests remain authoritative for their own scope. Seven existing procurement
regressions and the existing read-only source/CAD equivalence helpers passed
locally. Full package generation/verification, firmware compile, SPICE/thermal
reruns and fresh KiCad 9 ERC/DRC were not performed by this integration.
See [evidence/README.md](evidence/README.md) for exact evidence and boundaries.

`FOUNDATION_PROVENANCE.json` and `foundation-custody.patch` identify the reused
custody code and the limited GR86 specialization. Shared/entry code identity is
bound into every capture. After any integration/source/configuration change,
make a new capsule; old results do not acquire new applicability retroactively.

## Local workflow

Use prompts 00–02 for bootstrap, source reconciliation and deterministic work;
03 plus the six role prompts only after actual isolation is qualified; 04 for
findings/dispositions; 05 only in a separately authorized accepted-repair task;
06 for reverification; 07 for optional project-scoped MCP.

Current sourced native CAD is generated, not its owning editing location.
Preserve maintained candidate CAD, procurement sources, firmware and generated
package relationships. Read-only verification and capture do not authorize
repair, criteria relaxation, vendor upload, orders, flashing, hardware/vehicle
access, CAN transmission, merge, release or gate closure. No ACT repository or
portfolio-control changes accompany this GR86 handoff.
