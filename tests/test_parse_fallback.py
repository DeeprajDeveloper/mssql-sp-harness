"""Tests for sqlglot failure with text-scan fallback."""

from pathlib import Path

from sql_sp_harness.inventory import inventory_from_parse
from sql_sp_harness.parse import ParseResult, parse_sql, strip_go_batches
from sql_sp_harness.t_sql_scan import scan_tsql

SAMPLES = Path(__file__).parents[1] / "samples"


def test_analyze_without_ast_still_reports_dml():
    """Org scripts with preamble + sqlglot gaps should not show a fatal parse error."""
    sql = (SAMPLES / "enterprise_complex_proc.sql").read_text(encoding="utf-8")
    cleaned = strip_go_batches(sql)
    scan = scan_tsql(cleaned)
    result = ParseResult(
        source=cleaned,
        trees=[],
        errors=["[ParseError] Required keyword: 'this' missing for <class 'sqlglot.expressions.Create'>"],
        warnings=[],
        scan=scan,
    )
    inv = inventory_from_parse(result)
    assert inv.is_parsable
    assert inv.update >= 1
    assert not any("No trees parsed" in err for err in inv.errors)


def test_parse_sql_filters_none_trees():
    result = parse_sql("-- header only\n")
    assert result.trees == []
    assert result.scan is not None
