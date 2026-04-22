import ijson  # type: ignore
from collections import defaultdict
from typing import Dict


def compute_balances_from_json_stream(path: str) -> Dict[str, float]:
    balances = defaultdict(float)

    # Expect a JSON array: [ {..}, {..}, ... ]
    with open(path, "rb") as f:
        for log in ijson.items(f, "item"):
            balances[log["policy_id"]] += float(log["amount"])

    return dict(balances)


def main() -> None:
    path = "playground/policy_logs.json"
    balances = compute_balances_from_json_stream(path)
    for policy_id in sorted(balances):
        print(f"{policy_id}: {balances[policy_id]:.2f}")


if __name__ == "__main__":
    main()
