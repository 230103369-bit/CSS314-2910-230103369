
import csv
import ctypes
import json
import multiprocessing as mp
import statistics
import time
from pathlib import Path


PROCESS_COUNTS = (1, 2, 4, 8)
ITERATIONS = 5_000_000
REPEATS = 3
CACHE_LINE_BYTES = 128

MODES = (
    "unpadded",
    "padded_64",
    "privatized",
    "padded_128",
)


def get_spacing(mode):
    if mode == "padded_64":
        return 8
    if mode == "padded_128":
        return 16
    return 1


def worker(shared_array, index, iterations, mode, ready, start, done, errors):
    try:
        ready.release()
        start.wait()

        if mode == "privatized":
            local_counter = 0

            for _ in range(iterations):
                local_counter += 1

            shared_array[index] = local_counter
        else:
            for _ in range(iterations):
                shared_array[index] += 1

    except BaseException:
        errors.value = 1
        raise
    finally:
        done.release()


def allocate_aligned_array(process_count, spacing):
    array_size = (process_count - 1) * spacing + 1
    alignment_elements = CACHE_LINE_BYTES // ctypes.sizeof(ctypes.c_int64)

    raw_size = array_size + alignment_elements
    shared_array = mp.RawArray(ctypes.c_int64, raw_size)

    base_address = ctypes.addressof(shared_array)
    offset_bytes = (-base_address) % CACHE_LINE_BYTES
    offset_elements = offset_bytes // ctypes.sizeof(ctypes.c_int64)

    if (base_address + offset_elements * 8) % CACHE_LINE_BYTES != 0:
        raise RuntimeError("Memory alignment failed")

    return shared_array, offset_elements, array_size


def run_experiment(process_count, mode):
    spacing = get_spacing(mode)

    shared_array, offset, array_size = allocate_aligned_array(
        process_count,
        spacing,
    )

    ready = mp.Semaphore(0)
    start = mp.Event()
    done = mp.Semaphore(0)
    errors = mp.Value("i", 0)

    processes = []

    for worker_id in range(process_count):
        index = offset + worker_id * spacing

        process = mp.Process(
            target=worker,
            args=(
                shared_array,
                index,
                ITERATIONS,
                mode,
                ready,
                start,
                done,
                errors,
            ),
        )

        processes.append(process)

    setup_start = time.perf_counter()

    for process in processes:
        process.start()

    for _ in range(process_count):
        ready.acquire()

    setup_seconds = time.perf_counter() - setup_start

    compute_start = time.perf_counter()
    start.set()

    for _ in range(process_count):
        done.acquire()

    compute_seconds = time.perf_counter() - compute_start

    for process in processes:
        process.join()

    for process in processes:
        if process.exitcode != 0:
            raise RuntimeError(
                f"Worker failed with exit code {process.exitcode}"
            )

    if errors.value != 0:
        raise RuntimeError("Worker execution failed")

    total = 0
    addresses = []

    base_address = ctypes.addressof(shared_array)

    for worker_id in range(process_count):
        index = offset + worker_id * spacing
        total += shared_array[index]
        addresses.append(base_address + index * 8)

    expected = process_count * ITERATIONS

    if total != expected:
        raise RuntimeError(
            f"Counter mismatch: {total} != {expected}"
        )

    return {
        "compute_seconds": compute_seconds,
        "setup_seconds": setup_seconds,
        "total": total,
        "addresses": addresses,
        "spacing_bytes": spacing * 8,
        "aligned": addresses[0] % CACHE_LINE_BYTES == 0,
    }


def benchmark(process_count, mode):
    samples = []
    setup_samples = []
    last_result = None

    for repeat in range(REPEATS):
        result = run_experiment(process_count, mode)

        samples.append(result["compute_seconds"])
        setup_samples.append(result["setup_seconds"])
        last_result = result

        print(
            f"{mode:<13} | "
            f"P={process_count:<2} | "
            f"Run {repeat + 1}/{REPEATS} | "
            f"Compute {result['compute_seconds']:.6f} s | "
            f"Setup {result['setup_seconds']:.6f} s"
        )

    return {
        "median_seconds": statistics.median(samples),
        "median_setup_seconds": statistics.median(setup_samples),
        "samples": samples,
        "total": last_result["total"],
        "spacing_bytes": last_result["spacing_bytes"],
        "aligned": last_result["aligned"],
        "addresses": last_result["addresses"],
    }


def karp_flatt(process_count, speedup):
    if process_count == 1:
        return None

    return (
        (1.0 / speedup) - (1.0 / process_count)
    ) / (1.0 - (1.0 / process_count))


def main():
    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    with (results_dir / "salted_params.json").open(
        "r",
        encoding="utf-8",
    ) as file:
        params = json.load(file)

    print("Milestone 2 - False Sharing and Karp-Flatt")
    print("-" * 70)
    print(f"Student ID: {params['student_id']}")
    print(f"Iterations per worker: {ITERATIONS:,}")
    print(f"Process counts: {PROCESS_COUNTS}")
    print(f"Repeated measurements: {REPEATS}")
    print(f"Cache line alignment: {CACHE_LINE_BYTES} bytes")
    print("Timing: synchronized compute phase")
    print()

    rows = []
    baselines = {}

    for mode in MODES:
        print(f"Mode: {mode}")
        print("-" * 70)

        for process_count in PROCESS_COUNTS:
            result = benchmark(process_count, mode)

            median_time = result["median_seconds"]

            if process_count == 1:
                baselines[mode] = median_time

            speedup = baselines[mode] / median_time
            efficiency = speedup / process_count
            e_value = karp_flatt(process_count, speedup)

            addresses = result["addresses"]

            distinct_lines = len({
                address // CACHE_LINE_BYTES
                for address in addresses
            })

            rows.append({
                "student_id": params["student_id"],
                "mode": mode,
                "processes": process_count,
                "iterations_per_worker": ITERATIONS,
                "total_increments": result["total"],
                "spacing_bytes": result["spacing_bytes"],
                "distinct_cache_lines": distinct_lines,
                "aligned": result["aligned"],
                "median_seconds": round(median_time, 6),
                "median_setup_seconds": round(
                    result["median_setup_seconds"], 6
                ),
                "speedup": round(speedup, 6),
                "efficiency": round(efficiency, 6),
                "karp_flatt": (
                    round(e_value, 6)
                    if e_value is not None
                    else ""
                ),
                "run_1_seconds": round(result["samples"][0], 6),
                "run_2_seconds": round(result["samples"][1], 6),
                "run_3_seconds": round(result["samples"][2], 6),
            })

            print(
                f"Median: {median_time:.6f} s | "
                f"Speedup: {speedup:.3f}x | "
                f"Karp-Flatt: "
                f"{e_value if e_value is not None else 'N/A'}"
            )

            print(
                f"Spacing: {result['spacing_bytes']} bytes | "
                f"Distinct cache lines: {distinct_lines}/{process_count} | "
                f"Aligned: {result['aligned']}"
            )
            print()

    output_path = results_dir / "false_sharing_karp_flatt.tsv"

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=list(rows[0].keys()),
            delimiter="\t",
        )

        writer.writeheader()
        writer.writerows(rows)

    print("=" * 70)
    print("Counter verification: PASSED")
    print("Generated: results/false_sharing_karp_flatt.tsv")


if __name__ == "__main__":
    mp.freeze_support()
    main()
