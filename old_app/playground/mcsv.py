import csv
from collections import defaultdict
from typing import Dict


def compute_balances_from_csv(path: str) -> Dict[str, float]:
    balances = defaultdict(float)

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            policy_id = row["policy_id"]
            amount = float(row["amount"])
            balances[policy_id] += amount

    return dict(balances)


def main() -> None:
    path = "playground/policy_logs.csv"
    balances = compute_balances_from_csv(path)
    for policy_id in sorted(balances):
        print(f"{policy_id}: {balances[policy_id]:.2f}")


if __name__ == "__main__":
    main()
