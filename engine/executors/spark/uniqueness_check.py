def run(data, column: str) -> int:
    total = data.count()
    distinct = data.select(column).distinct().count()
    return total - distinct