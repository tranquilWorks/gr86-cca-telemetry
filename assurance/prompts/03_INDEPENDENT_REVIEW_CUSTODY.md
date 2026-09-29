# Independent review custody — coordinator only

```text
Prepare real independent first-pass reviews for the exact GR86 CCA snapshot.
This is custody/orchestration, not permission for the designer to impersonate
reviewers. Preserve the owner's local provider/model choice.

Generate a separate draft packet for each shared role using bridge.py packet.
Verify the assessment seal before and after packet preparation. Any custody
failure blocks use of that run and its derivative packets; preserve it unchanged.
Its initial scope is native design only; requirements_curation remains BLOCKED.
Do not edit that sealed packet. Build a separate curated derivative with a new
manifest/seal, retaining the assessment snapshot ID, original packet hash, exact
source hashes/locations and the shared review.schema.json. Add only approved
requirements and exact primary references needed for that role. Any extracted
excerpt must preserve its parent-document hash and locator. Required but
unapproved/missing sources must remain an explicit review limitation.

Exclude designer conversations, old reviews/redlines, readiness/closure claims,
generated acceptance results, analysis_input artifacts, Git history and mutation
keys. Inspect file contents, including embedded CAD text and metadata, not merely
filenames. Native design intent is necessary evidence; it is not acceptance
authority. Never redact or alter canonical CAD to hide a suspected defect.

Before launching anything, probe the actual local Codex/host capabilities. The
shared review-host command is a probe and currently does not establish a usable
provider/tool bridge. Qualify an approved boundary that permits only the curated
packet to be read and a unique report/scratch directory to be written. Test denied
access to canonical design, designer history, answer keys, unrelated filesystem,
credentials and supplier/hardware/write tools. Record canary results, session and
model identity, settings, tool inventory, mount/access rules and packet hash.
A read-only prompt, new chat, directory or file mode is insufficient. If the
boundary is not enforced, record BLOCKED; do not use an unrestricted session as
a qualified reviewer. Do not export credentials to make it work.

Launch six fresh sessions only after that qualification: requirements,
electrical, interfaces, layout, manufacturing and mechanical. Copy the matching
roles/*.md prompt into its isolated workspace; reviewers must not browse back
into this repository to read prompts. Give identical frozen acceptance sources
where responsibilities overlap, with no shared mutable conclusions. Missing
specialist tools/documents remain BLOCKED rather than silently substituted.

Collect each finalized findings report, actual session metadata and referenced
evidence, then hash/seal the submission before historical comparison. Validate
the shared review schema and snapshot binding. Shared import-review archives a
submission separately; it cannot authenticate isolation or approve dispositions.
Only after all submissions are fixed may the custodian reconcile historical
findings and contradictions. Do not repair the board.

GR86 curation: inspect native embedded text and all 33 envelope models before
adding any to a separate derivative packet. The draft contains 120 native design
files, not approved requirements or exact vendor models. Firmware and interface
documents may be necessary, but include only curated source-bound material, not
historical acceptance headlines. Packet construction does not close KiCad 9
compatibility, supplier process, physical thermal/fit or vehicle/unit gates.
```
