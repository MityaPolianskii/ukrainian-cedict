#!/usr/bin/env python3
"""Verify a complete checkout without changing either frozen release validator."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_status(root):
    status = read(root / "STATUS.json")
    progress = read(root / "progress.json")
    source = read(root / "source.json")
    overlay = root / progress["review_progress"]["qualified_overlay_path"]
    manifest = read(overlay / "manifest.json")
    review = progress["review_progress"]
    expected = {
        "original_records": manifest["corpusReviewedRecords"],
        "original_segments": manifest["corpusReviewedSegments"],
        "qualified_original_records": manifest["corpusEligibleRecords"],
        "held_original_records": manifest["corpusHeldRecords"],
        "separate_baseline_records": manifest["baselineReviewedRecords"],
        "qualified_baseline_records": manifest["baselineEligibleRecords"],
        "held_baseline_records": manifest["baselineHeldRecords"],
        "app_baseline_entries": review["runtime_qualified_entries"] + review["runtime_unmapped_entries"],
        "qualified_runtime_entries": review["runtime_qualified_entries"],
        "runtime_english_fallback_entries": review["runtime_unmapped_entries"],
        "human_validated_records": review["human_validated_records"],
    }
    require(status["coverage"] == expected, "Current status differs from source-bound overlay counts")
    require(status["pinned_source"]["release"] == source["source_release"]
            and status["pinned_source"]["entries"] == source["source_entries"], "Pinned source differs")
    require(status["source_dictionary_sha256"] == progress["data_sha256"]["dictionary.json"]
            == manifest["sourceDictionarySHA256"], "Source dictionary binding differs")
    require(status["overlay_manifest_sha256"] == hashlib.sha256((overlay / "manifest.json").read_bytes()).hexdigest(),
            "Current overlay binding differs")
    require(status["human_validation"] is False and status["linguistic_accuracy_certified"] is False,
            "Unsupported human or accuracy claim")
    require(status["upstream_observation"]["imported"] is False
            and status["upstream_observation"]["net_entry_difference"]
            == status["upstream_observation"]["entries"] - source["source_entries"], "Upstream scope differs")
    require(status["app_store_observation"]["publicly_available"] is True
            and status["original_draft_runtime_approved"] is False, "Delivery and draft scopes differ")
    return expected


def check_release(root):
    # The original validator deliberately accepts only an extracted publication,
    # with an exact inventory. Keep .git outside that boundary instead of relaxing it.
    checksums = {}
    for line in (root / "SHA256SUMS.txt").read_text().splitlines():
        digest, name = line.split("  ", 1)
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts and name not in checksums,
                "Unsafe or duplicate checksum path")
        require(len(digest) == 64 and all(c in "0123456789abcdef" for c in digest), "Invalid checksum")
        checksums[name] = digest
    actual = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if ".git" in relative.parts or "__pycache__" in relative.parts:
            continue
        require(not path.is_symlink(), "Symlink outside publication boundary: " + str(relative))
        if path.is_file() and relative.as_posix() != "SHA256SUMS.txt":
            actual.add(relative.as_posix())
    require(actual == set(checksums), "Publication inventory differs; use a complete checkout without extra output files")
    coverage = validate_status(root)
    with tempfile.TemporaryDirectory(prefix="ukrainian-cedict-check-") as directory:
        package = Path(directory)
        for name, digest in checksums.items():
            source = root / name
            require(hashlib.sha256(source.read_bytes()).hexdigest() == digest, "Checksum differs: " + name)
            target = package / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        shutil.copyfile(root / "SHA256SUMS.txt", package / "SHA256SUMS.txt")
        subprocess.run([sys.executable, "-B", str(package / "scripts/validate.py")], check=True)
        overlay = package / read(package / "progress.json")["review_progress"]["qualified_overlay_path"]
        subprocess.run([sys.executable, "-B", str(overlay / "validate.py"), str(overlay),
                        "--source", str(package / "dictionary.json")], check=True)
    print(json.dumps({"status": "passed", "frozen_draft_and_resolved_overlay": True,
                      "current_status_consistent": True, "coverage": coverage}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    arguments = parser.parse_args()
    check_release(arguments.root.resolve())
