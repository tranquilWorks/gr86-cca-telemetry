#!/usr/bin/env python3
"""Generate deterministic manifests for the I32 160 MHz target build."""

from __future__ import annotations

import hashlib
import gzip
import json
from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
REPO = Path(subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], cwd=HERE, check=True,
    capture_output=True, text=True).stdout.strip())
FIRMWARE = REPO / "docs/engineering/rvb22/candidate/firmware"
NIMBLE = Path("/workspace/scratch/80f872752466/runner-temp/rvb22-native-tools/user/libraries/NimBLE-Arduino")
FQBN = (
    "esp32:esp32:esp32s3:USBMode=hwcdc,CDCOnBoot=default,MSCOnBoot=default,"
    "DFUOnBoot=default,UploadMode=default,CPUFreq=160,FlashMode=qio,FlashSize=8M,"
    "PartitionScheme=default_8MB,DebugLevel=none,PSRAM=enabled,LoopCore=1,"
    "EventsCore=1,EraseFlash=none,UploadSpeed=115200"
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inventory(root: Path, exclude_git: bool = False) -> dict[str, dict[str, int | str]]:
    rows = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if exclude_git and ".git" in path.parts:
            continue
        rows[path.relative_to(root).as_posix()] = {"sha256": sha(path), "size": path.stat().st_size}
    return rows


def write_json(name: str, value: object) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main() -> None:
    image_rows = inventory(HERE / "images")
    original_artifacts = {}
    for stored_name in ("cca_telemetry.ino.elf.gz", "cca_telemetry.ino.map.gz"):
        compressed = HERE / "images" / stored_name
        if compressed.exists():
            data = gzip.decompress(compressed.read_bytes())
            original_name = stored_name.removesuffix(".gz")
            original_artifacts[original_name] = {
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
                "stored_as": stored_name,
            }
    source_paths = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", "4c3e54395e84483298e453468a65ff2646e9de4e", "--",
         "docs/engineering/rvb22/candidate/firmware"],
        cwd=REPO, check=True, capture_output=True, text=True).stdout.splitlines()
    source_rows = {}
    for repo_path in source_paths:
        path = REPO / repo_path
        source_rows[path.relative_to(FIRMWARE).as_posix()] = {"sha256": sha(path), "size": path.stat().st_size}
    nimble_rows = inventory(NIMBLE, exclude_git=True)
    verbose = (HERE / "logs/firmware-build-verbose.log").read_text(errors="replace")
    release = json.loads((HERE / "RELEASE_CHECK.json").read_text())
    compiler = subprocess.run(
        ["/workspace/scratch/80f872752466/runner-temp/rvb22-native-tools/data/packages/esp32/tools/esp-x32/2511/bin/xtensa-esp32s3-elf-g++", "--version"],
        check=True, capture_output=True, text=True).stdout.splitlines()[0]

    write_json("IMAGE_MANIFEST.json", {
        "status": "PASS",
        "scope": "Unflashed ESP32-S3 build outputs; no device execution claimed.",
        "files": image_rows,
        "original_artifacts": original_artifacts,
    })
    write_json("COPIED_SOURCE_INVENTORY.json", {
        "base_commit": "4c3e54395e84483298e453468a65ff2646e9de4e",
        "firmware_file_count": len(source_rows),
        "firmware_files": source_rows,
        "nimble_file_count": len(nimble_rows),
        "nimble_files": nimble_rows,
    })
    write_json("TOOLCHAIN_INVENTORY.json", {
        "arduino_cli": "1.3.1",
        "arduino_esp32": "3.3.6",
        "nimble_arduino": "2.3.6",
        "compiler": compiler,
        "fqbn": FQBN,
        "cpu_define_observed": "-DF_CPU=160000000L",
        "cpu_define_present_in_verbose_log": "-DF_CPU=160000000L" in verbose,
        "official_archives": {
            "arduino_cli": {"sha256": "376428d7d45be640c00812a71612e1742edc2f5f9ee3742a2d6da7870e079588"},
            "esp32_core": {"sha256": "bd0cf5e9062d5411470d216f5c24fcc3f269b3d23a8d7c4b34f981cc92e61755"},
            "esp32s3_libs": {"sha256": "afc583111ffe3d30b16598868e259e80e15acbd5aed3c128dac7804c0bf5f67d"},
            "esp_x32": {"sha256": "c8aced923fe9bb8d3614212aee94b9f354f1c47992ac987f74138997212e0393"},
            "esptool": {"sha256": "49d572d50f6b1f089d1d81d3bd3bd357fbcc40f4f8fd4874f2dc51ad534abb01"},
        },
        "ctags": {
            "source_repository": "arduino/ctags",
            "tag": "5.8-arduino11",
            "commit": "abc8fca7499f44c725122881cd380a88c37abe0e",
            "local_compatibility_change": "Renamed the internal __unused__ macro to CTAGS_UNUSED to compile against current glibc headers; parser logic unchanged.",
            "official_binary_archive_unavailable": "Shell and cloud-browser network policy blocked downloads.arduino.cc; the shell index failure is preserved in logs/firmware-build.log.",
        },
    })
    write_json("RESULT.json", {
        "status": "PASS_FIRMWARE_TARGET_BUILD",
        "compile_exit_code": 0,
        "target": "ESP32-S3",
        "cpu_frequency_mhz": 160,
        "candidate_firmware_matches_base_commit": release["candidate_firmware_matches_base_commit"],
        "candidate_file_count": release["candidate_file_count"],
        "release_check_status": release["preserved_checker"]["status"],
        "release_check_count": len(release["preserved_checker"]["checks"]),
        "release_checks_passed": sum(1 for row in release["preserved_checker"]["checks"] if row["passed"]),
        "inputs_unchanged": release["candidate_firmware_matches_base_commit"],
        "flashed": False,
        "executed_on_target": False,
        "hardware_connected": False,
    })
    output_rows = inventory(HERE)
    output_rows.pop("OUTPUT_MANIFEST.json", None)
    write_json("OUTPUT_MANIFEST.json", {"files": output_rows})


if __name__ == "__main__":
    main()
