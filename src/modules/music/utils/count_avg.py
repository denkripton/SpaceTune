def count_avg(arr: list) -> float | int:
    if arr == []:
        return 0 
    return round(sum(arr) / len(arr), 1)
