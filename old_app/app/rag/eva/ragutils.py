def intersection_count(a: list[str], b: list[str]) -> int:
    return len(set(a) & set(b))


def avg(values: list[float | None]) -> float | None:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)
