
import hashlib
import json
from pathlib import Path


STUDENT_ID = "30103369"


def get_student_params(student_id: str):
    h = int(
        hashlib.sha256(student_id.encode("utf-8")).hexdigest()[:8],
        16,
    )

    N = 1024 + ((h % 9) * 64)
    buffer_elements = 16_777_216
    seed = h % 100_007

    return {
        "student_id": student_id,
        "N": N,
        "buffer_elements": buffer_elements,
        "seed": seed,
    }


def main():
    params = get_student_params(STUDENT_ID)

    root = Path(__file__).resolve().parent.parent
    results_dir = root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    output_path = results_dir / "salted_params.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(params, file, indent=4)

    print("Milestone 0 - Student ID Salting")
    print("-" * 45)
    print(f"Student ID: {params['student_id']}")
    print(f"Matrix dimension N: {params['N']}")
    print(f"Buffer elements: {params['buffer_elements']}")
    print(f"Random seed: {params['seed']}")
    print()
    print("Generated: results/salted_params.json")


if __name__ == "__main__":
    main()
