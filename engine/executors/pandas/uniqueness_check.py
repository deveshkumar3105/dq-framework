def run(data, column: str) -> int:
    return int(data[column].duplicated().sum())