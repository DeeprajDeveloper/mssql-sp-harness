"""Tests for comment stripping."""

from pathlib import Path

from sql_sp_harness.comments import strip_sql_comments
from sql_sp_harness.transform import transform_sql

SAMPLES = Path(__file__).parents[1] / "samples"


def test_strip_line_comment_preserves_string_literals():
    sql = "SELECT N'-- not a comment' AS x -- real comment\n"
    assert strip_sql_comments(sql) == "SELECT N'-- not a comment' AS x\n"


def test_strip_block_comment():
    sql = "/* header */\nCREATE PROC dbo.p AS BEGIN\n  SELECT 1\nEND\n"
    assert "header" not in strip_sql_comments(sql)
    assert "CREATE PROC" in strip_sql_comments(sql)


def test_strip_multiline_block():
    sql = "/*\nline one\nline two\n*/\nSET @x = 1\n"
    assert strip_sql_comments(sql) == "SET @x = 1\n"


def test_transform_strips_revision_block_by_default():
    sql = (SAMPLES / "enterprise_complex_proc.sql").read_text(encoding="utf-8")
    result = transform_sql(sql)
    assert "Mod Date" not in result.sql
    assert "DEBUG HARNESS" in result.sql
    assert "[DBG-PREVIEW]" in result.sql


def test_transform_keep_comments():
    sql = (SAMPLES / "enterprise_complex_proc.sql").read_text(encoding="utf-8")
    result = transform_sql(sql, strip_comments=False)
    assert "Mod Date" in result.sql
