def run(tables: dict, query: str) -> int:
    """Runs a SQL query against one or more Spark DataFrames.
    Convention: the query should return rows representing VIOLATIONS.
    Returns the count of violating rows (0 = pass)."""
    spark = None
    for name, df in tables.items():
        df.createOrReplaceTempView(name)
        if spark is None:
            spark = df.sparkSession

    result = spark.sql(query)
    return result.count()