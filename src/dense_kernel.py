
import json
import statistics
import time
from pathlib import Path

import numpy as np
from numba import njit


RUNS = 3


@njit
def multiply_ijk(A, B):
    n = A.shape[0]
    C = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for j in range(n):
            total = 0.0
            for k in range(n):
                total += A[i, k] * B[k, j]
            C[i, j] = total

    return C


@njit
def multiply_ikj(A, B):
    n = A.shape[0]
    C = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        for k in range(n):
            a = A[i, k]
            for j in range(n):
                C[i, j] += a * B[k, j]

    return C


def benchmark(function, A, B):
    timings = []
    result = None

    for _ in range(RUNS):
        start = time.perf_counter_ns()
        result = function(A, B)
        elapsed = time.perf_counter_ns() - start
        timings.append(elapsed)

    return statistics.median(timings), result, timings


def main():
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"

    with (results_dir / "salted_params.json").open(
        "r", encoding="utf-8"
    ) as file:
        params = json.load(file)

    N = params["N"]
    M = N // 2
    seed = params["seed"]

    rng = np.random.default_rng(seed)

    A = rng.random((M, M), dtype=np.float64)
    B = rng.random((M, M), dtype=np.float64)

    print("Milestone 1 - Loop Interchange Benchmark")
    print("-" * 55)
    print(f"Student ID: {params['student_id']}")
    print(f"Salted N: {N}")
    print(f"Benchmark block M: {M}")
    print(f"Seed: {seed}")
    print(f"Measured runs: {RUNS}")
    print()
    print("Compiling kernels...")

    multiply_ijk(A[:2, :2], B[:2, :2])
    multiply_ikj(A[:2, :2], B[:2, :2])

    print("Compilation complete.")
    print()

    naive_ns, C_naive, naive_samples = benchmark(multiply_ijk, A, B)
    interchanged_ns, C_interchanged, interchanged_samples = benchmark(
        multiply_ikj, A, B
    )

    max_absolute_error = float(
        np.max(np.abs(C_naive - C_interchanged))
    )

    max_relative_error = float(
        np.max(
            np.abs(C_naive - C_interchanged)
            / np.maximum(np.abs(C_naive), 1e-15)
        )
    )

    verified = bool(
        np.allclose(
            C_naive,
            C_interchanged,
            rtol=1e-12,
            atol=1e-12,
        )
    )

    speedup = naive_ns / interchanged_ns

    result = {
        "student_id": params["student_id"],
        "salted_N": N,
        "block_M": M,
        "seed": seed,
        "runs": RUNS,
        "naive_ijk": {
            "samples_ns": naive_samples,
            "median_ns": naive_ns,
            "median_seconds": naive_ns / 1e9,
        },
        "interchanged_ikj": {
            "samples_ns": interchanged_samples,
            "median_ns": interchanged_ns,
            "median_seconds": interchanged_ns / 1e9,
        },
        "speedup": speedup,
        "max_absolute_error": max_absolute_error,
        "max_relative_error": max_relative_error,
        "numerical_verification": verified,
    }

    output_path = results_dir / "loop_interchange.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4)

    print(f"Naive i-j-k median: {naive_ns / 1e9:.6f} seconds")
    print(f"Interchanged i-k-j median: {interchanged_ns / 1e9:.6f} seconds")
    print(f"Speedup: {speedup:.3f}x")
    print(f"Max absolute error: {max_absolute_error:.12e}")
    print(f"Max relative error: {max_relative_error:.12e}")
    print(f"Numerical verification: {'PASSED' if verified else 'FAILED'}")
    print()
    print("Generated: results/loop_interchange.json")

    if not verified:
        raise RuntimeError("Matrix multiplication verification failed")


if __name__ == "__main__":
    main()
