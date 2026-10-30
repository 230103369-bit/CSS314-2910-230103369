import time
from multiprocessing import Pool


def private_worker(iterations):
    local_sum = 0
    for _ in range(iterations):
        local_sum += 1
    return local_sum


def run_privatized(p, total_increments=20_000_000):
    increments_per_worker = total_increments // p
    tasks = [increments_per_worker] * p

    start = time.perf_counter()

    with Pool(processes=p) as pool:
        results = pool.map(private_worker, tasks)

    total = sum(results)
    runtime = time.perf_counter() - start

    assert total == total_increments
    return runtime


def main():
    runtimes = {}

    for p in (1, 2, 4):
        runtime = run_privatized(p)
        runtimes[p] = runtime
        print(f"P={p} | Runtime={runtime:.3f}s", flush=True)

    t1 = runtimes[1]

    for p in (2, 4):
        tp = runtimes[p]
        speedup = t1 / tp
        e = ((p * tp / t1) - 1) / (p - 1)
        efficiency = speedup / p * 100

        print(
            f"P={p} | Speedup={speedup:.3f}x | "
            f"Karp-Flatt e={e:.4f} | "
            f"Efficiency={efficiency:.2f}%"
        )

        if p == 4:
            print(f"T4 < T1: {tp < t1}")
            print(f"E4 > 70%: {efficiency > 70}")
            print(f"e(4) < 0.05: {e < 0.05}")


if __name__ == "__main__":
    main()
