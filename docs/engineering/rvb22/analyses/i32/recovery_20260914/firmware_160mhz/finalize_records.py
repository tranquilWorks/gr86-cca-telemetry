#!/usr/bin/env python3
"""Idempotently reconcile I32 records after the verified 160 MHz build."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REPO = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], cwd=HERE, check=True,
    capture_output=True, text=True).stdout.strip())


def load(relative: str) -> tuple[Path, dict]:
    path = REPO / relative
    return path, json.loads(path.read_text())


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n")


def update_rows(rows: list[dict]) -> None:
    for row in rows:
        if row["id"] == "I32-I":
            row["status"] = "CAD_AND_FIRMWARE_EFFECTIVITY_VERIFIED"
            row["disposition"] = (
                "Current native evidence binds 135 CAD inputs and the 177-part authored/filled CAD. "
                "All 32 firmware files remain byte-identical to adopted commit 4c3e543; a genuine "
                "Arduino-ESP32 3.3.6/NimBLE 2.3.6 target build records CPUFreq=160 and passes all "
                "28 preserved source/image/ELF release checks. Historical 240 MHz images remain quarantined."
            )
        if row["id"] == "I32-RCV-FW-01":
            row["status"] = "CLOSED_DIGITAL_TARGET_BUILD_VERIFIED"
            row["disposition"] = (
                "Closed by a genuine unchanged-source ESP32-S3 build at CPUFreq=160. The full FQBN, "
                "-DF_CPU=160000000L compiler log, source/dependency/image hashes, split and merged images, "
                "ELF/map and 28/28 release checks are preserved under recovery_20260914/firmware_160mhz/."
            )
            row["remaining_gate"] = (
                "No digital rebuild remains. Firmware was not flashed or executed on target; physical "
                "thermal, EMC, silicon, first-article and vehicle acceptance remain open."
            )


def main() -> None:
    image_manifest = json.loads((HERE / "IMAGE_MANIFEST.json").read_text())
    images = image_manifest["files"]
    elf_record = images.get("cca_telemetry.ino.elf") or image_manifest["original_artifacts"]["cca_telemetry.ino.elf"]
    result = json.loads((HERE / "RESULT.json").read_text())

    path, mismatch = load("docs/engineering/rvb22/analyses/i32/recovery_20260914/FIRMWARE_BUILD_MISMATCH.json")
    mismatch["status"] = "CLOSED_BY_160MHZ_TARGET_BUILD"
    mismatch["severity"] = "CLOSED_DIGITAL_GATE_PHYSICAL_THERMAL_CORRELATION_REMAINS"
    mismatch["new_target_compilation_run"] = {
        "performed": True,
        "evidence": "firmware_160mhz/RESULT.json",
        "cpu_frequency_MHz": 160,
        "compile_exit_code": result["compile_exit_code"],
        "candidate_firmware_matches_base_commit": result["candidate_firmware_matches_base_commit"],
        "release_checks_passed": result["release_checks_passed"],
        "release_check_count": result["release_check_count"],
        "application_image_sha256": images["cca_telemetry.ino.bin"]["sha256"],
        "merged_image_sha256": images["cca_telemetry.ino.merged.bin"]["sha256"],
        "elf_sha256": elf_record["sha256"],
        "flashed": False,
        "executed_on_target": False,
    }
    mismatch["closure_evidence"] = [
        "firmware_160mhz/RESULT.json",
        "firmware_160mhz/TOOLCHAIN_INVENTORY.json",
        "firmware_160mhz/COPIED_SOURCE_INVENTORY.json",
        "firmware_160mhz/IMAGE_MANIFEST.json",
        "firmware_160mhz/RELEASE_CHECK.json",
        "firmware_160mhz/logs/firmware-build-verbose.log",
    ]
    mismatch["required_closure_completed"] = True
    save(path, mismatch)

    path, findings = load("docs/engineering/rvb22/analyses/i32/FINDINGS_REGISTER.json")
    findings["status"] = "RECOVERY_VERIFIED_NO_ACTIONABLE_DIGITAL_CORRECTIONS"
    findings["known_actionable_digital_corrections_remaining"] = 0
    findings["meaning"] = (
        "The recovered I32 board remains source-bound and the 160 MHz target-build mismatch is digitally closed. "
        "Supplier, construction, first-article, vehicle and physical qualification gates remain open."
    )
    update_rows(findings["rows"])
    save(path, findings)

    path, review = load("docs/engineering/rvb22/FINAL_REVIEW_REGISTER.json")
    review["status"] = "RECOVERY_VERIFIED_NO_ACTIONABLE_DIGITAL_CORRECTIONS"
    review["summary"]["known_actionable_scoped_digital_corrections_remaining"] = 0
    update_rows(review["rows"])
    save(path, review)

    path, effectivity = load("docs/engineering/rvb22/current/SOURCE_EFFECTIVITY.json")
    effectivity["status"] = "I32_BOARD_DFM_CANDIDATE_FIRMWARE_160MHZ_BUILD_VERIFIED"
    effectivity["model_carry_forward"]["firmware"] = (
        "All 32 adopted source files are unchanged. A genuine Arduino-ESP32 3.3.6/NimBLE 2.3.6 build "
        "used CPUFreq=160 and passed 28/28 release checks; prior 240 MHz images remain historical only."
    )
    effectivity["firmware_release"] = {
        "status": "160MHZ_TARGET_BUILD_AND_BINARY_CHECKS_PASS",
        "finding": "../analyses/i32/recovery_20260914/FIRMWARE_BUILD_MISMATCH.json",
        "evidence": "../analyses/i32/recovery_20260914/firmware_160mhz/RESULT.json",
        "old_images": "Historical only; excluded from release use",
        "new_target_build_run": True,
        "candidate_source_files_unchanged": True,
        "release_checks_passed": 28,
        "release_check_count": 28,
        "application_image_sha256": images["cca_telemetry.ino.bin"]["sha256"],
        "merged_image_sha256": images["cca_telemetry.ino.merged.bin"]["sha256"],
        "flashed": False,
        "executed_on_target": False,
    }
    save(path, effectivity)

    path, runner = load("docs/engineering/rvb22/analyses/i32/recovery_20260914/RUNNER_REPAIR.json")
    runner["continuation"] = {
        "firmware_compilation_performed": True,
        "cpu_frequency_MHz": 160,
        "compile_exit_code": 0,
        "release_checks": "28/28 PASS",
        "evidence": "firmware_160mhz/RESULT.json",
        "native_CAD_execution_in_continuation": False,
        "native_CAD_reason": "KiCad/pcbnew unavailable in the resumed runtime; preserved KiCad 9.0.9 evidence and 13 postconditions remain authoritative.",
    }
    save(path, runner)


if __name__ == "__main__":
    main()
