import duckdb


def run(tables: dict, query: str) -> int:
    """Runs a SQL query against one or more pandas DataFrames using DuckDB.
    Convention: the query should return rows representing VIOLATIONS.
    Returns the count of violating rows (0 = pass)."""
    con = duckdb.connect()
    for name, df in tables.items():
        con.register(name, df)

    result = con.execute(query).fetchdf()
    con.close()
    return len(result)