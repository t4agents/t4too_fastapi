import json
from collections import defaultdict
from typing import Dict


def compute_balances_from_json(path: str) -> Dict[str, float]:
    with open(path, "r", encoding="utf-8") as f:
        logs = json.load(f)

    balances = defaultdict(float)
    for log in logs:
        balances[log["policy_id"]] += float(log["amount"])

    return dict(balances)


def main() -> None:
    path = "playground/policy_logs.json"
    balances = compute_balances_from_json(path)
    for policy_id in sorted(balances):
        print(f"{policy_id}: {balances[policy_id]:.2f}")


if __name__ == "__main__":
    main()
