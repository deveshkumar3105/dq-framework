from pyspark.sql.functions import col

def run(data, column: str) -> int:
    return data.filter(col(column).isNull()).count()