# I32 recovery checkpoint — 2026-09-14 UTC

## Continuation closure

The complete guarded overlay was subsequently applied to the named branch checkout. I32-RCV-FW-01 is closed digitally by a genuine unchanged-source 160 MHz ESP32-S3 build with full compiler/dependency/source/image evidence and 28/28 release checks passing under `analyses/i32/recovery_20260914/firmware_160mhz/`. Historical 240 MHz images remain quarantined. The build was not flashed or run on hardware; all supplier and physical qualification gates below remain in force.

## Publication boundary

This commit publishes a recovery checkpoint ONLY. It does not publish the recovered I32 CAD, the repaired runner, new firmware images, or a fabrication release. The design baseline inspected before this checkpoint was `4c3e54395e84483298e453468a65ff2646e9de4e` on `codex/rvb24-coordinated-closure`, PR46. Preserve any newer work. Do not restart I32 from the older 153-part board.

The interrupted ChatGPT session produced `GR86_RevB_I32_DFM_First_Article.zip` in the owner's Library. Its SHA256 is `9e1a68a927b164962c732f453e963485a6ab3221d3df42ac1b6361080975efc0`. The checked continuation is supplied as `GR86_RevB_I32_Checked_Recovery.zip`, containing a guarded repository overlay, full recovery report, revised findings/effectivity records and new verification evidence. The owner-facing conversation contains that bundle; no public download location is implied.

## Current source identity

- Authored 177-part PCB: `45a2a679d9893d51fa641e539af45bc6ec1324169ea5f2226ecdea0ae2464da7`.
- Native filled PCB: `249d7b584af71605ee160c1ff425fda16a11b3ba93458bb243a722214c66ab30`.
- Native schematic XML: `f2394512c684bbf5eedb75730429004d8b92e1b834973b5ff7db300a618f1908`.

No copper, schematic or firmware source was changed during recovery. The continuation repairs the runner and records a genuine release blocker below.

## Reopened digital gate: I32-RCV-FW-01

**A fresh 160 MHz target firmware build is required.** The packaged firmware's recorded compile command used `CPUFreq=240`. The latest hosted native artifact was independently downloaded and also records `CPUFreq=240` (run `34741994938`, artifact `10313361109`, archive SHA256 `ee6525c00773781869274aad58a6306250f7d0fca51cbf3a1494261ddd88dce1`). I25 and the supplied firmware build.sh require 160 MHz. Matching 32 source files did not establish compiler-option equality.

The checked overlay changes the runner default to 160 MHz and pins STEP inventory validation to the actual 177 fitted parts, with duplicate/missing/malformed/effectivity rejection tests. The exact runner used by the old successful native run was absent; the replacement is explicitly documented, not represented as historical recovery. Old firmware images are quarantined as historical evidence. No new ESP32 target compile occurred in this recovery.

Do not accept the original zero-open-digital-items claim. The supplied findings register, final review register and source-effectivity record reopen I32-RCV-FW-01. Close it only after a genuine pinned 160 MHz compilation, recorded options/dependencies/source/image hashes and binary release checks. Do not flash the old images or classify this rebuild as hardware-only qualification.

## Fresh verification

All 3,661 original package file hashes and ZIP CRC pass. All 314 baseline source files and five candidate Git subtree hashes plus three root blob hashes match the connected live baseline. Source audits verify 135 CAD inputs, 177 fitted parts, 32 unchanged firmware source files, 49 special vias, preserved rules/stackup and signal contracts.

All 186 recorded native output identities are accounted for: 185 were already present; the omitted model-export-only PCB was reconstructed deterministically from recorded model paths and matched its exact hash. All 13 saved-output structural postconditions pass the repaired validator. Ten validator regression tests and eight guarded-overlay application tests pass.

Eighty source routing pairs, 23 actual-filled-ground connections, 1,308 populated and 529 mated envelope checks, and 38 probe approaches were rerun without material disagreement or allocated interference. Five firmware host C++ tests pass, including genuine AddressSanitizer and UndefinedBehaviorSanitizer runs. None of this is an ESP32 build, hardware test, fresh KiCad execution or fresh SPICE campaign.

The actual current-runner preflight returns BLOCKED_RUNTIME: KiCad/pcbnew and the pinned Arduino toolchain are unavailable. Direct Git access separately failed DNS resolution with exit 128. Prior source-bound KiCad and 34 power/17 input-stress case evidence remains preserved, not relabeled as new execution. Failed optional-render and initially incomplete host-link attempts are retained.

## Next authorized execution

Read the checked bundle's START_HERE.md, RECOVERY_REPORT.md and PUBLICATION.json. Verify the bundle, reconcile the existing branch and apply its guarded overlay without overwriting newer work. Complete the actual 160 MHz target build and applicable native gates in the provisioned engineering environment, then publish the complete scoped changes using a non-force update to this existing branch.

Retain supplier, construction and physical qualification gates, the fixed 2.940859375 W heat budget, the original 112.8829809018675 C correlation trigger, the 160 MHz I25 workload, U201 immediate air <=85 C and Adafruit 851 local environment <=60 C. No merge, order, hardware operation, flashing, credential inspection or vehicle connection is authorized by this checkpoint.
