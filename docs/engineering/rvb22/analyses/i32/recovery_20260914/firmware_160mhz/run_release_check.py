#!/usr/bin/env python3
"""Run the preserved firmware checker without modifying candidate source."""

from __future__ import annotations

import hashlib
import gzip
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


BASE_COMMIT = "4c3e54395e84483298e453468a65ff2646e9de4e"
PREFIX = Path("docs/engineering/rvb22/candidate/firmware")


def git_bytes(repo: Path, revision_path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{BASE_COMMIT}:{revision_path}"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout


def main() -> int:
    here = Path(__file__).resolve().parent
    repo = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=here,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    candidate = repo / PREFIX
    paths = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", BASE_COMMIT, "--", str(PREFIX)],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    comparisons = []
    for repo_path in paths:
        rel = Path(repo_path).relative_to(PREFIX)
        expected = git_bytes(repo, repo_path)
        actual = (candidate / rel).read_bytes()
        comparisons.append(
            {
                "path": rel.as_posix(),
                "sha256": hashlib.sha256(actual).hexdigest(),
                "matches_base_commit": actual == expected,
            }
        )
    source_match = bool(comparisons) and all(x["matches_base_commit"] for x in comparisons)
    if not source_match:
        raise SystemExit("Candidate firmware differs from adopted base commit")

    source_manifest = json.loads((candidate / "SOURCE_MANIFEST.json").read_text())
    with tempfile.TemporaryDirectory(prefix="i32-release-check-") as td:
        temp = Path(td)
        temp_candidate = temp / "candidate" / "firmware"
        shutil.copytree(candidate, temp_candidate, ignore=shutil.ignore_patterns("images", "build"))
        shutil.copytree(here / "images", temp_candidate / "images")
        compressed_elf = temp_candidate / "images" / "cca_telemetry.ino.elf.gz"
        elf = temp_candidate / "images" / "cca_telemetry.ino.elf"
        if not elf.exists() and compressed_elf.exists():
            elf.write_bytes(gzip.decompress(compressed_elf.read_bytes()))

        baseline = temp / "baseline"
        baseline.mkdir()
        baseline_rows = []
        for row in source_manifest["files"]:
            rel = Path(row["path"])
            repo_path = (PREFIX / rel).as_posix()
            data = git_bytes(repo, repo_path)
            target = baseline / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            baseline_rows.append({"path": rel.as_posix(), "sha256": hashlib.sha256(data).hexdigest()})
        (baseline / "firmware").mkdir(parents=True, exist_ok=True)
        (baseline / "firmware" / "CANDIDATE_MANIFEST.json").write_text(
            json.dumps({"files": baseline_rows}, indent=2) + "\n"
        )

        env = os.environ.copy()
        env["CCA_BASELINE_ROOT"] = str(baseline)
        proc = subprocess.run(
            ["python3", str(temp_candidate / "tests" / "check_release.py")],
            cwd=temp_candidate,
            env=env,
            capture_output=True,
            text=True,
        )
        checker = json.loads(proc.stdout)
        report = {
            "status": "PASS" if proc.returncode == 0 and checker.get("status") == "PASS" else "FAIL",
            "base_commit": BASE_COMMIT,
            "candidate_firmware_matches_base_commit": source_match,
            "candidate_file_count": len(comparisons),
            "candidate_files": comparisons,
            "preserved_checker": checker,
            "checker_stderr": proc.stderr,
        }
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
