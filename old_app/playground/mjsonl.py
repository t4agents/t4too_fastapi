# How you scale beyond one machine

# Streaming: read continuously, update balances incrementally.
# Partitioning: split by policy_id (e.g., hash to shards) so each worker owns a subset.
# Map‑Reduce: map emits (policy_id, amount), reduce sums.
# External aggregation: if p is huge, spill partial sums to disk and merge.
# Interview‑safe one‑liner
import json
from collections import defaultdict
from typing import Dict


def compute_balances_from_jsonl(path: str) -> Dict[str, float]:
    balances = defaultdict(float)

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            log = json.loads(line)
            balances[log["policy_id"]] += float(log["amount"])

    return dict(balances)


def main() -> None:
    path = "playground/policy_logs.jsonl"
    balances = compute_balances_from_jsonl(path)
    for policy_id in sorted(balances):
        print(f"{policy_id}: {balances[policy_id]:.2f}")


if __name__ == "__main__":
    main()
