def clamp(value: int, low: int, high: int) -> int:
    if value < low:
        return high
    if value > high:
        return high
    return value
