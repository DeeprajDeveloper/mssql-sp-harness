"""Tests for step-by-step run logging."""

from pathlib import Path

from sql_sp_harness.run_log import resolve_log_path
from sql_sp_harness.transform import transform_sql

SAMPLES = Path(__file__).parents[1] / "samples"


def test_resolve_log_path_explicit_file(tmp_path: Path):
    custom = tmp_path / "custom.log"
    assert resolve_log_path(SAMPLES / "my_proc.sql", log=False, log_file=custom) == custom


def test_resolve_log_path_default_stem():
    path = resolve_log_path(SAMPLES / "my_proc.sql", log=True, log_file=None)
    assert path == SAMPLES / "my_proc.log"


def test_generate_writes_log_file(tmp_path: Path):
    from sql_sp_harness.run_log import RunLogger

    sql = (SAMPLES / "simple_proc.sql").read_text(encoding="utf-8")
    log_path = tmp_path / "run.log"
    logger = RunLogger(log_path)
    transform_sql(sql, on_progress=logger.as_progress_callback())
    logger.info("done")
    text = log_path.read_text(encoding="utf-8")
    assert "Stripping comments" in text or "Keeping original comments" in text
    assert "Stubbing" in text or "Injecting SET" in text
