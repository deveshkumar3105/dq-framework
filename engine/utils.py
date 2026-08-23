def resolve_columns(data, columns_spec) -> list:
    """Resolve a config's 'columns' value into an actual list of column names.
    Supports an explicit list, or '*' to mean every column in the data."""
    if columns_spec == "*":
        return list(data.columns)
    if isinstance(columns_spec, list):
        return columns_spec
    raise ValueError(f"Invalid 'columns' value: {columns_spec!r}. Must be a list or '*'.")