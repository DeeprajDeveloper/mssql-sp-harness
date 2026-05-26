"""CLI for mssql-sp-harness."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer

from mssql_sp_harness import __version__
from mssql_sp_harness.console import supports_color
from mssql_sp_harness.inventory import inventory_from_sql
from mssql_sp_harness.transform import transform_sql

APP_HELP = """
Turn MSSQL stored procedures into safe, runnable debug scripts.

\b
Commands:
  analyze    See what a procedure does (DML, TRY/CATCH, loops, variables)
  generate   Create a debug harness script safe to run on a dev database

\b
Quick start:
  mssql-sp-harness analyze -i MyProc.sql
  mssql-sp-harness generate -i MyProc.sql -o MyProc_debug.sql

\b
More help:
  mssql-sp-harness analyze --help
  mssql-sp-harness generate --help
"""

app = typer.Typer(
    name="mssql-sp-harness",
    help=APP_HELP,
    no_args_is_help=True,
    add_completion=False,
)


@app.command("version")
def cmd_version() -> None:
    """Print package version."""
    typer.echo(__version__)


def _version() -> str:
    try:
        from importlib.metadata import version

        return version("mssql-sp-harness")
    except Exception:
        return __version__


@app.callback()
def _root_callback(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        help="Show version and exit.",
        is_eager=True,
    ),
) -> None:
    """MSSQL stored procedure debug harness generator."""
    if version:
        typer.echo(f"mssql-sp-harness {_version()}")
        raise typer.Exit()


def _read_input(path: Optional[Path]) -> str:
    if path is None or str(path) == "-":
        return sys.stdin.read()
    return path.read_text(encoding="utf-8")


def _write_output(path: Optional[Path], content: str) -> None:
    if path is None or str(path) == "-":
        sys.stdout.write(content)
        return
    path.write_text(content, encoding="utf-8")


def _run_analyze(
    input: Path,
    report: Optional[Path],
    plain: bool,
    full: bool,
) -> None:
    sql = _read_input(input)
    inv = inventory_from_sql(sql)
    colorize = supports_color() and not plain and report is None
    text = inv.to_text(colorize=colorize, non_zero_only=not full)
    if report:
        report.write_text(text + "\n", encoding="utf-8")
        typer.echo(f"Report written to {report}")
    else:
        typer.echo(text)


@app.command("analyze")
def analyze_cmd(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Input .sql file (use - for stdin).",
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        "-r",
        help="Write plain-text report to file (no ANSI colors).",
    ),
    plain: bool = typer.Option(
        False,
        "--plain",
        help="Disable ANSI colors on terminal output.",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Show all sections, including zero counts.",
    ),
) -> None:
    """
    Analyze a stored procedure and show what it does.

    Summarizes DML against real tables, TRY/CATCH blocks, loops, SET statements,
    and other structural detail — useful before generating a debug harness.
    """
    _run_analyze(input, report, plain, full)


@app.command("inventory", hidden=True)
def inventory_cmd(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Input .sql file (use - for stdin).",
    ),
    report: Optional[Path] = typer.Option(
        None,
        "--report",
        "-r",
        help="Write plain-text report to file (no ANSI colors).",
    ),
    plain: bool = typer.Option(
        False,
        "--plain",
        help="Disable ANSI colors on terminal output.",
    ),
    full: bool = typer.Option(
        False,
        "--full",
        help="Show all sections, including zero counts.",
    ),
) -> None:
    """Deprecated alias for analyze."""
    _run_analyze(input, report, plain, full)


def _run_generate(
    input: Path,
    output: Optional[Path],
    trace_style: str,
    no_stub_dml: bool,
    block_markers: bool,
    quiet: bool,
) -> None:
    if trace_style not in ("raiserror", "print"):
        typer.echo("trace-style must be 'raiserror' or 'print'", err=True)
        raise typer.Exit(1)

    sql = _read_input(input)
    progress = None if quiet else lambda msg: typer.echo(msg, err=True)

    result = transform_sql(
        sql,
        trace_style=trace_style,
        stub_dml=not no_stub_dml,
        add_block_markers=block_markers,
        on_progress=progress,
    )

    out_path = output
    if out_path is None and str(input) != "-":
        out_path = input.with_name(f"{input.stem}_debug{input.suffix}")

    _write_output(out_path, result.sql)

    summary = (
        f"Done: {result.stats.dml_stubbed} DML stubbed, "
        f"{result.stats.traces_added} traces added."
    )
    if out_path and str(out_path) != "-":
        typer.echo(f"{summary} Written to {out_path}")
    else:
        typer.echo(summary)

    if result.parse_errors:
        typer.echo("Parse warnings present — review banner in output.", err=True)
        raise typer.Exit(2)


@app.command("generate")
def generate_cmd(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Input .sql file (use - for stdin).",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (default: <input>_debug.sql).",
    ),
    trace_style: str = typer.Option(
        "print",
        "--trace-style",
        help="Trace style: print (default) or raiserror (NOWAIT).",
    ),
    no_stub_dml: bool = typer.Option(
        False, "--no-stub-dml", help="Skip DML stubbing; only add traces."
    ),
    block_markers: bool = typer.Option(
        False,
        "--block-markers",
        help="Insert -- [DBG] Step N markers before IF/WHILE.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress progress messages on stderr.",
    ),
) -> None:
    """
    Generate a debug harness script from a stored procedure.

    Replaces writes to real tables with SELECT previews and adds PRINT traces on
    variables so you can run the script on a dev database without side effects.
    """
    _run_generate(input, output, trace_style, no_stub_dml, block_markers, quiet)


@app.command("transform", hidden=True)
def transform_cmd(
    input: Path = typer.Option(
        ...,
        "--input",
        "-i",
        help="Input .sql file (use - for stdin).",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path (default: <input>_debug.sql).",
    ),
    trace_style: str = typer.Option(
        "print",
        "--trace-style",
        help="Trace style: print (default) or raiserror (NOWAIT).",
    ),
    no_stub_dml: bool = typer.Option(
        False, "--no-stub-dml", help="Skip DML stubbing; only add traces."
    ),
    block_markers: bool = typer.Option(
        False,
        "--block-markers",
        help="Insert -- [DBG] Step N markers before IF/WHILE.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress progress messages on stderr.",
    ),
) -> None:
    """Deprecated alias for generate."""
    _run_generate(input, output, trace_style, no_stub_dml, block_markers, quiet)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
