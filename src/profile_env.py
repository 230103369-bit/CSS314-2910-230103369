
import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

from salt import get_student_params


def sysctl_value(key):
    try:
        result = subprocess.run(
            ["sysctl", "-n", key],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def sysctl_integer(key):
    value = sysctl_value(key)

    if value is None:
        return None

    try:
        return int(value)
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", default="30103369")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    cpu_model = sysctl_value("machdep.cpu.brand_string")
    physical_cores = sysctl_integer("hw.physicalcpu")
    logical_cores = sysctl_integer("hw.logicalcpu")

    profile = {
        "cpu_model": cpu_model or platform.processor(),
        "microarchitecture": platform.machine(),
        "base_frequency_hz": sysctl_integer("hw.cpufrequency"),
        "physical_cores": physical_cores,
        "logical_cores": logical_cores or os.cpu_count(),
        "smt_enabled": (
            logical_cores > physical_cores
            if logical_cores is not None and physical_cores is not None
            else None
        ),
        "cache_line_bytes": sysctl_integer("hw.cachelinesize"),
        "l1_data_cache_bytes": sysctl_integer("hw.l1dcachesize"),
        "l2_cache_bytes": sysctl_integer("hw.l2cachesize"),
        "l3_cache_bytes": sysctl_integer("hw.l3cachesize"),
        "performance_core_cache": {
            "l1_data_bytes": sysctl_integer("hw.perflevel0.l1dcachesize"),
            "l1_instruction_bytes": sysctl_integer("hw.perflevel0.l1icachesize"),
            "l2_bytes": sysctl_integer("hw.perflevel0.l2cachesize"),
        },
        "efficiency_core_cache": {
            "l1_data_bytes": sysctl_integer("hw.perflevel1.l1dcachesize"),
            "l1_instruction_bytes": sysctl_integer("hw.perflevel1.l1icachesize"),
            "l2_bytes": sysctl_integer("hw.perflevel1.l2cachesize"),
        },
        "operating_system": platform.system(),
        "os_version": platform.mac_ver()[0],
        "kernel_version": platform.release(),
        "platform": platform.platform(),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "python_executable": sys.executable,
    }

    host_path = results_dir / "host_profile.json"

    with host_path.open("w", encoding="utf-8") as file:
        json.dump(profile, file, indent=4)

    salted_params = get_student_params(args.student_id)
    salted_path = results_dir / "salted_params.json"

    with salted_path.open("w", encoding="utf-8") as file:
        json.dump(salted_params, file, indent=4)

    print("Milestone 0 - Host Topology Profiling & Salting")
    print("-" * 55)
    print(f"Student ID: {args.student_id}")
    print(f"CPU Model: {profile['cpu_model']}")
    print(f"Architecture: {profile['microarchitecture']}")
    print(f"Base frequency: {profile['base_frequency_hz']}")
    print(f"Physical cores: {profile['physical_cores']}")
    print(f"Logical cores: {profile['logical_cores']}")
    print(f"SMT enabled: {profile['smt_enabled']}")
    print(f"Cache line: {profile['cache_line_bytes']} bytes")
    print(f"L1 Data cache: {profile['l1_data_cache_bytes']} bytes")
    print(f"L2 cache: {profile['l2_cache_bytes']} bytes")
    print(f"L3 cache: {profile['l3_cache_bytes']}")
    print(f"OS: {profile['operating_system']} {profile['os_version']}")
    print(f"Kernel: {profile['kernel_version']}")
    print(f"Python: {profile['python_implementation']} {profile['python_version']}")
    print()
    print(f"Matrix dimension N: {salted_params['N']}")
    print(f"Buffer elements: {salted_params['buffer_elements']}")
    print(f"Random seed: {salted_params['seed']}")
    print()
    print("Generated: results/host_profile.json")
    print("Generated: results/salted_params.json")


if __name__ == "__main__":
    main()
