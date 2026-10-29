
import csv
import json
import statistics
import time
from pathlib import Path

import numpy as np
from numba import njit


STRIDES = (1, 2, 4, 8, 16, 32, 64, 128)
WARMUP_RUNS = 5
MEASURED_RUNS = 5


@njit
def stride_reduction(data, stride):
    total = 0.0

    for i in range(0, data.size, stride):
        total += data[i]

    return total


def measure_stride(data, stride):
    start = time.perf_counter_ns()
    checksum = stride_reduction(data, stride)
    elapsed_ns = time.perf_counter_ns() - start

    elements_touched = (data.size + stride - 1) // stride
    ns_per_element = elapsed_ns / elements_touched

    return elapsed_ns, ns_per_element, checksum


def main():
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"

    with (results_dir / "salted_params.json").open(
        "r", encoding="utf-8"
    ) as file:
        params = json.load(file)

    buffer_elements = params["buffer_elements"]
    data = np.ones(buffer_elements, dtype=np.float64)

    output_path = results_dir / "stride_results.tsv"

    print("Milestone 1 - Compiled Stride Latency Benchmark")
    print("-" * 65)
    print(f"Student ID: {params['student_id']}")
    print(f"Buffer elements: {buffer_elements}")
    print(f"Buffer size: {data.nbytes / (1024 ** 2):.2f} MiB")
    print(f"Warmup runs: {WARMUP_RUNS}")
    print(f"Measured runs: {MEASURED_RUNS}")
    print()

    print("Compiling Numba kernel...")
    stride_reduction(data[:16], 1)
    print("Compilation complete.")
    print()

    rows = []

    for stride in STRIDES:
        for _ in range(WARMUP_RUNS):
            measure_stride(data, stride)

        elapsed_samples = []
        latency_samples = []
        checksum = None

        for _ in range(MEASURED_RUNS):
            elapsed_ns, ns_per_element, checksum = measure_stride(
                data, stride
            )
            elapsed_samples.append(elapsed_ns)
            latency_samples.append(ns_per_element)

        elements_touched = (buffer_elements + stride - 1) // stride
        median_elapsed_ns = statistics.median(elapsed_samples)
        median_latency_ns = statistics.median(latency_samples)
        expected_checksum = float(elements_touched)

        if not np.isclose(checksum, expected_checksum):
            raise RuntimeError(
                f"Checksum verification failed for stride {stride}"
            )

        rows.append({
            "stride": stride,
            "elements_touched": elements_touched,
            "median_elapsed_ns": int(median_elapsed_ns),
            "median_ns_per_element": round(median_latency_ns, 6),
            "checksum": checksum,
            "warmup_runs": WARMUP_RUNS,
            "measured_runs": MEASURED_RUNS,
        })

        print(
            f"Stride {stride:>3} | "
            f"Elements {elements_touched:>10,} | "
            f"Median {median_latency_ns:>12.3f} ns/element"
        )

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "stride",
                "elements_touched",
                "median_elapsed_ns",
                "median_ns_per_element",
                "checksum",
                "warmup_runs",
                "measured_runs",
            ],
            delimiter="\t",
        )
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("Checksum verification: PASSED")
    print("Generated: results/stride_results.tsv")


if __name__ == "__main__":
    main()
