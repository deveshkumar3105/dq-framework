import logging

from engine.runner import run


def test_run_logs_check_progress(tmp_path, caplog):
    config_path = tmp_path / "orders.yaml"
    data_path = tmp_path / "orders.csv"

    config_path.write_text(
        """
table: orders
checks:
  - type: null_check
    column: order_id
  - type: uniqueness_check
    column: order_id
""".strip()
    )
    data_path.write_text("order_id\n1\n2\n3\n")

    with caplog.at_level(logging.INFO):
        run(str(config_path), str(data_path))

    assert "Starting data quality run" in caplog.text
    assert "Processing check null_check" in caplog.text
    assert "Processing check uniqueness_check" in caplog.text
    assert "Completed data quality run" in caplog.text
