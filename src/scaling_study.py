
import csv
import json
import math
import multiprocessing as mp
import statistics
import time
from multiprocessing import shared_memory
from pathlib import Path

import numpy as np


PROCESS_COUNTS = (1, 2, 4, 8)
REPEATS = 3


def stencil_reference(a):
    result = np.zeros_like(a)
    result[1:-1, 1:-1] = (
        a[:-2, 1:-1]
        + a[2:, 1:-1]
        + a[1:-1, :-2]
        + a[1:-1, 2:]
        - 4.0 * a[1:-1, 1:-1]
    )
    return result


def worker(input_name, output_name, n, row_start, row_end):
    input_shm = shared_memory.SharedMemory(name=input_name)
    output_shm = shared_memory.SharedMemory(name=output_name)

    try:
        a = np.ndarray((n, n), dtype=np.float64, buffer=input_shm.buf)
        b = np.ndarray((n, n), dtype=np.float64, buffer=output_shm.buf)

        lo = max(1, row_start)
        hi = min(n - 1, row_end)

        if lo < hi:
            b[lo:hi, 1:-1] = (
                a[lo - 1:hi - 1, 1:-1]
                + a[lo + 1:hi + 1, 1:-1]
                + a[lo:hi, :-2]
                - 4.0 * a[lo:hi, 1:-1]
                + a[lo:hi, 2:]
            )
    finally:
        del a, b
        input_shm.close()
        output_shm.close()


def create_shared_array(n):
    size = n * n * np.dtype(np.float64).itemsize
    shm = shared_memory.SharedMemory(create=True, size=size)
    array = np.ndarray((n, n), dtype=np.float64, buffer=shm.buf)
    return shm, array


def execute_stencil(n, processes, seed):
    input_shm, a = create_shared_array(n)
    output_shm, b = create_shared_array(n)

    try:
        rng = np.random.default_rng(seed)
        a[:] = rng.random((n, n))
        b.fill(0.0)

        reference = stencil_reference(a)

        boundaries = np.linspace(
            0, n, processes + 1, dtype=int
        )

        jobs = [
            mp.Process(
                target=worker,
                args=(
                    input_shm.name,
                    output_shm.name,
                    n,
                    int(boundaries[i]),
                    int(boundaries[i + 1]),
                ),
            )
            for i in range(processes)
        ]

        start = time.perf_counter()

        for job in jobs:
            job.start()

        for job in jobs:
            job.join()

        elapsed = time.perf_counter() - start

        for job in jobs:
            if job.exitcode != 0:
                raise RuntimeError(
                    f"Worker failed with exit code {job.exitcode}"
                )

        max_error = float(np.max(np.abs(b - reference)))

        if not np.allclose(
            b, reference, rtol=1e-12, atol=1e-12
        ):
            raise RuntimeError(
                f"Numerical verification failed: {max_error}"
            )

        checksum = float(np.sum(b, dtype=np.float64))

        return elapsed, checksum, max_error

    finally:
        del a, b
        input_shm.close()
        output_shm.close()
        input_shm.unlink()
        output_shm.unlink()


def benchmark(n, processes, seed):
    times = []
    checksum = None
    max_error = None

    for repeat in range(REPEATS):
        elapsed, checksum, max_error = execute_stencil(
            n, processes, seed
        )

        times.append(elapsed)

        print(
            f"N={n:<5} | P={processes:<2} | "
            f"Run {repeat + 1}/{REPEATS} | "
            f"{elapsed:.6f} s"
        )

    return {
        "median_seconds": statistics.median(times),
        "runs": times,
        "checksum": checksum,
        "max_error": max_error,
    }


def effective_serial_fraction(p, speedup):
    if p == 1:
        return None

    return (
        (1.0 / speedup) - (1.0 / p)
    ) / (1.0 - (1.0 / p))


def main():
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with (results_dir / "salted_params.json").open(
        "r", encoding="utf-8"
    ) as file:
        params = json.load(file)

    n = int(params["N"])
    seed = int(params["seed"])

    rows = []
    serial_fractions = []

    print("Milestone 3 - Scaling and Roofline")
    print("=" * 70)
    print(f"Student ID: {params['student_id']}")
    print(f"Salted N: {n}")
    print(f"Seed: {seed}")
    print()

    print("STRONG SCALING")
    print("-" * 70)

    strong_baseline = None

    for p in PROCESS_COUNTS:
        result = benchmark(n, p, seed)

        if p == 1:
            strong_baseline = result["median_seconds"]

        speedup = strong_baseline / result["median_seconds"]
        efficiency = 100.0 * speedup / p

        serial_fraction = effective_serial_fraction(
            p, speedup
        )

        if serial_fraction is not None:
            serial_fractions.append(serial_fraction)

        rows.append({
            "student_id": params["student_id"],
            "study": "strong",
            "processes": p,
            "dimension": n,
            "work_elements": (n - 2) ** 2,
            "median_seconds": result["median_seconds"],
            "speedup": speedup,
            "efficiency_percent": efficiency,
            "serial_fraction": (
                serial_fraction
                if serial_fraction is not None
                else ""
            ),
            "checksum": result["checksum"],
            "max_error": result["max_error"],
            "run_1_seconds": result["runs"][0],
            "run_2_seconds": result["runs"][1],
            "run_3_seconds": result["runs"][2],
        })

        print(
            f"Strong P={p}: "
            f"Speedup={speedup:.3f}x | "
            f"Efficiency={efficiency:.2f}% | "
            f"s={serial_fraction}"
        )
        print()

    print("WEAK SCALING")
    print("-" * 70)

    weak_baseline = None
    base_work = (n - 2) ** 2

    for p in PROCESS_COUNTS:
        scaled_n = math.ceil(n * math.sqrt(p))
        result = benchmark(scaled_n, p, seed)

        if p == 1:
            weak_baseline = result["median_seconds"]

        work = (scaled_n - 2) ** 2

        scaled_speedup = (
            p * base_work * weak_baseline
        ) / (work * result["median_seconds"])

        throughput = work / result["median_seconds"]

        rows.append({
            "student_id": params["student_id"],
            "study": "weak",
            "processes": p,
            "dimension": scaled_n,
            "work_elements": work,
            "median_seconds": result["median_seconds"],
            "speedup": scaled_speedup,
            "efficiency_percent": 100.0 * scaled_speedup,
            "serial_fraction": "",
            "checksum": result["checksum"],
            "max_error": result["max_error"],
            "run_1_seconds": result["runs"][0],
            "run_2_seconds": result["runs"][1],
            "run_3_seconds": result["runs"][2],
        })

        print(
            f"Weak P={p}: "
            f"Scaled speedup={scaled_speedup:.3f} | "
            f"Throughput={throughput:,.0f} cells/s"
        )
        print()

    output_tsv = results_dir / "scaling_metrics.tsv"

    with output_tsv.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    print("ROOFLINE ANALYSIS")
    print("-" * 70)

    flops_per_cell = 5
    bytes_per_cell = 6 * 8

    arithmetic_intensity = (
        flops_per_cell / bytes_per_cell
    )

    fitted_serial_fraction = (
        statistics.median(serial_fractions)
        if serial_fractions
        else None
    )

    valid_amdahl_estimate = (
        fitted_serial_fraction is not None
        and 0.0 < fitted_serial_fraction <= 1.0
    )

    asymptotic_speedup = (
        1.0 / fitted_serial_fraction
        if valid_amdahl_estimate
        else None
    )

    if fitted_serial_fraction is None:
        amdahl_interpretation = (
            "Insufficient measurements to estimate "
            "the effective serial fraction."
        )
    elif valid_amdahl_estimate:
        amdahl_interpretation = (
            "The estimated effective serial fraction "
            "is within the physical range of Amdahl's model."
        )
    else:
        amdahl_interpretation = (
            "The effective serial fraction is outside "
            "the physical range of Amdahl's model. "
            "Parallel overhead and measurement effects "
            "prevent a meaningful asymptotic speedup estimate."
        )

    roofline = {
        "student_id": params["student_id"],
        "kernel": "2D five-point stencil",
        "salted_dimension": n,
        "flops_per_interior_cell": flops_per_cell,
        "bytes_per_interior_cell_naive_model": bytes_per_cell,
        "arithmetic_intensity_flops_per_byte": arithmetic_intensity,
        "arithmetic_intensity_model": (
            "Five input loads and one output store, "
            "8 bytes per float64, ignoring cache reuse "
            "and temporary arrays."
        ),
        "effective_serial_fraction_estimate": fitted_serial_fraction,
        "amdahl_asymptotic_speedup_estimate": asymptotic_speedup,
        "amdahl_interpretation": amdahl_interpretation,
        "peak_memory_bandwidth_gb_s": None,
        "peak_compute_gflops": None,
        "roofline_ridge_point": None,
        "roofline_classification": "undetermined",
        "qualitative_expectation": (
            "Low arithmetic intensity suggests sensitivity "
            "to memory bandwidth. A definitive Roofline "
            "classification requires measured or documented "
            "memory bandwidth and compute ceilings."
        ),
        "timing_scope": (
            "Includes process startup, joins, "
            "and shared-memory attachment."
        ),
        "numerical_verification": "PASSED",
    }

    output_json = results_dir / "roofline_summary.json"

    with output_json.open(
        "w", encoding="utf-8"
    ) as file:
        json.dump(roofline, file, indent=2)

    print(
        f"Arithmetic intensity: "
        f"{arithmetic_intensity:.6f} FLOPs/byte"
    )
    print(
        f"Estimated serial fraction: "
        f"{fitted_serial_fraction}"
    )
    print(
        f"Amdahl asymptotic speedup: "
        f"{asymptotic_speedup}"
    )
    print(f"Amdahl interpretation: {amdahl_interpretation}")

    print()
    print("=" * 70)
    print("Numerical verification: PASSED")
    print("Generated: results/scaling_metrics.tsv")
    print("Generated: results/roofline_summary.json")


if __name__ == "__main__":
    mp.freeze_support()
    main()
