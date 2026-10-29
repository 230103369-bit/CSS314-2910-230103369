
import sys
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import verify_outputs as verifier


def main():
    profile = json.loads((ROOT / "results/host_profile.json").read_text())
    salt = json.loads((ROOT / "results/salted_params.json").read_text())

    sid = str(salt["student_id"])
    h = int(hashlib.sha256(sid.encode()).hexdigest()[:8], 16)
    expected_n = 1024 + (h % 9) * 64

    assert salt["N"] == expected_n
    assert profile["logical_threads"] == profile["logical_cores"]
    assert profile["cache_line_bytes"] == 128

    reported_cache_line = subprocess.check_output(
        ["sysctl", "-n", "hw.cachelinesize"],
        text=True
    ).strip()

    assert int(reported_cache_line) == profile["cache_line_bytes"]

    print("[PASS] M0: SHA-256 salting")
    print("[PASS] M0: Apple M2 cache line verified")
    print("[INFO] Instructor-approved exception: 128-byte cache line")

    verifier.verify_milestone_1()
    verifier.verify_milestone_2()
    verifier.verify_milestone_3()

    report = {
        "student_id": sid,
        "salted_N": expected_n,
        "cache_line_bytes": profile["cache_line_bytes"],
        "instructor_approved_exception": "Apple M2 reports 128-byte cache lines",
        "milestone_0": "PASS with approved hardware exception",
        "milestone_1": "PASS",
        "milestone_2": "PASS",
        "milestone_3": "PASS",
        "official_receipt_generated": False
    }

    output = ROOT / "results/final_verification_report.json"
    output.write_text(json.dumps(report, indent=2) + "\n")

    print("=" * 60)
    print("[COMPLETE] M0-M3 checks passed with documented exception")
    print(f"Report: {output}")
    print("Official verification_receipt.sig was not generated")
    print("=" * 60)


if __name__ == "__main__":
    main()
