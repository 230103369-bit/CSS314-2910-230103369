import math
import time
from multiprocessing import Pool


def heavy_math(n):
    return sum(math.sin(i) * math.cos(i) for i in range(1, n))


def run_experiment(workers, total_chunks=16, chunk_size=2_000_000):
    start = time.perf_counter()
    time.sleep(0.40)

    with Pool(processes=workers) as pool:
        pool.map(heavy_math, [chunk_size] * total_chunks)

    return time.perf_counter() - start


def main():
    runtimes = {}

    for workers in (1, 2, 4):
        runtime = run_experiment(workers)
        runtimes[workers] = runtime
        print(f"P={workers} | Runtime={runtime:.3f}s", flush=True)

    t1 = runtimes[1]
    metrics = {}

    for workers in (2, 4):
        tp = runtimes[workers]
        speedup = t1 / tp
        e = ((workers * tp / t1) - 1) / (workers - 1)
        metrics[workers] = e
        print(
            f"P={workers} | Speedup={speedup:.3f}x | "
            f"Karp-Flatt e={e:.4f}"
        )

    ratio = metrics[4] / metrics[2]

    print(f"e(4)/e(2)={ratio:.4f}")
    print(f"Rubric A: {'PASS' if 0.80 <= ratio <= 1.25 else 'NOT MET'}")


if __name__ == "__main__":
    main()
