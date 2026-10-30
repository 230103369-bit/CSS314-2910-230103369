import time
from multiprocessing import Process, Value, Lock


def contended_worker(shared_counter, lock, iterations):
    for _ in range(iterations):
        with lock:
            shared_counter.value += 1


def run_contended(p, total_increments=2_000_000):
    increments_per_worker = total_increments // p
    counter = Value("i", 0, lock=False)
    lock = Lock()

    processes = [
        Process(
            target=contended_worker,
            args=(counter, lock, increments_per_worker),
        )
        for _ in range(p)
    ]

    start = time.perf_counter()

    for process in processes:
        process.start()

    for process in processes:
        process.join()

    runtime = time.perf_counter() - start

    assert counter.value == total_increments
    assert all(process.exitcode == 0 for process in processes)

    return runtime


def main():
    runtimes = {}

    for p in (1, 2, 4):
        runtime = run_contended(p)
        runtimes[p] = runtime
        print(f"P={p} | Runtime={runtime:.3f}s", flush=True)

    t1 = runtimes[1]
    metrics = {}

    for p in (2, 4):
        tp = runtimes[p]
        speedup = t1 / tp
        e = ((p * tp / t1) - 1) / (p - 1)
        metrics[p] = e

        print(
            f"P={p} | Speedup={speedup:.3f}x | "
            f"Karp-Flatt e={e:.4f}"
        )

    print(f"Contention slowdown: T4/T1={runtimes[4]/t1:.3f}x")
    print(f"e(4) > e(2): {metrics[4] > metrics[2]}")
    print(f"T4 > T1: {runtimes[4] > t1}")


if __name__ == "__main__":
    main()
