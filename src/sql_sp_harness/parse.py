"""Parse T-SQL scripts with sqlglot."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from sql_sp_harness.constants import GO_PATTERN
from sql_sp_harness.script_prepare import prepare_for_analysis
from sql_sp_harness.t_sql_scan import TsqlScanResult, scan_tsql

SQLGLOT_LOGGER = logging.getLogger("sqlglot")


@dataclass
class ParseResult:
    """Outcome of parsing a SQL script."""

    source: str
    trees: list[exp.Expression] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    scan: TsqlScanResult | None = None

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0 and len(self.trees) > 0


@contextmanager
def suppress_sqlglot_warnings():
    """Silence sqlglot's 'unsupported syntax' logger noise during parse.

    sqlglot logs a warning for each TRY/CATCH (and similar) fragment it stores as
    exp.Command. That is expected for enterprise T-SQL; sql-sp-harness uses text scan
    to supplement the AST. Set SP_DEBUG_VERBOSE=1 to leave warnings visible.
    """
    if os.environ.get("SP_DEBUG_VERBOSE"):
        yield
        return
    previous = SQLGLOT_LOGGER.level
    SQLGLOT_LOGGER.setLevel(logging.ERROR)
    try:
        yield
    finally:
        SQLGLOT_LOGGER.setLevel(previous)


def strip_go_batches(sql: str) -> str:
    """Remove GO batch separators (not valid T-SQL for sqlglot)."""
    lines = []
    for line in sql.splitlines():
        if GO_PATTERN.match(line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines)


def _valid_trees(trees: list[exp.Expression | None]) -> list[exp.Expression]:
    """sqlglot sometimes returns ``[None]`` for comment-only or empty input."""
    return [tree for tree in trees if tree is not None]


def scan_has_structure(scan: TsqlScanResult) -> bool:
    """True when text scan found analyzable procedure structure."""
    return bool(scan.dml_findings or scan.try_catch_findings)


def first_tree(result: ParseResult) -> exp.Expression | None:
    """Return the first usable sqlglot tree, if any."""
    for tree in result.trees:
        if tree is not None:
            return tree
    return None


def parse_sql(sql: str, *, strip_preamble: bool = True) -> ParseResult:
    """Parse T-SQL; collect trees and non-fatal warnings."""
    if strip_preamble:
        sql = prepare_for_analysis(sql)
    cleaned = strip_go_batches(sql)
    warnings: list[str] = []
    errors: list[str] = []
    trees: list[exp.Expression] = []

    scan = scan_tsql(cleaned)

    try:
        with suppress_sqlglot_warnings():
            trees = _valid_trees(list(sqlglot.parse(cleaned, read="tsql")))
    except ParseError as exc:
        errors.append(str(exc))
        if scan_has_structure(scan):
            warnings.append(
                "[ParseWarning] sqlglot could not build an AST; counts and details use text scan."
            )
        return ParseResult(
            source=cleaned, trees=[], errors=errors, warnings=warnings, scan=scan
        )

    if not trees:
        if scan_has_structure(scan):
            warnings.append(
                "[ParseWarning] sqlglot could not build an AST; counts and details use text scan."
            )
        else:
            errors.append("[ParseError] No statements parsed from input.")
        return ParseResult(
            source=cleaned, trees=[], errors=errors, warnings=warnings, scan=scan
        )

    if scan.try_catch_blocks or scan.update > len(list(trees[0].find_all(exp.Update))):
        warnings.append(
            "[ParseWarning] sqlglot may miss UPDATE/DML inside TRY/CATCH Command fragments; text scan supplements AST counts."
        )
    warnings.extend(scan.notes)
    return ParseResult(source=cleaned, trees=trees, errors=errors, warnings=warnings, scan=scan)


def parse_for_transform(sql: str, *, strip_preamble: bool = True) -> ParseResult:
    """Fast parse for transform: strip GO + text scan only (no sqlglot AST).

    Transform uses line-based rewriting, so a full AST parse is unnecessary and
    can be very slow on large enterprise procedures.
    """
    if strip_preamble:
        sql = prepare_for_analysis(sql)
    cleaned = strip_go_batches(sql)
    scan = scan_tsql(cleaned)
    warnings: list[str] = list(scan.notes)
    if scan.try_catch_blocks:
        warnings.append(
            "[ParseWarning] TRY/CATCH blocks detected; DML stubbing uses line scanning."
        )
    return ParseResult(source=cleaned, trees=[], errors=[], warnings=warnings, scan=scan)


def root_tree(result: ParseResult) -> exp.Expression | None:
    """Return the first sqlglot tree (alias for :func:`first_tree`)."""
    return first_tree(result)
