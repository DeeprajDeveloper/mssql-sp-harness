"""Command implementations for analyze and generate."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from sql_sp_harness import __version__
from sql_sp_harness.console import supports_color
from sql_sp_harness.encoding import read_sql_bytes, read_sql_file
from sql_sp_harness.inventory import inventory_from_sql
from sql_sp_harness.run_log import RunLogger, combine_progress, resolve_log_path
from sql_sp_harness.transform import transform_sql


def package_version() -> str:
    try:
        from importlib.metadata import version

        return version("sql-sp-harness")
    except Exception:
        return __version__


def _timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def read_input(
    path: Optional[Path],
    encoding: Optional[str] = None,
    *,
    quiet: bool = False,
    logger: RunLogger | None = None,
) -> str:
    """Read a T-SQL stored procedure from a file or stdin."""
    if path is None or str(path) == "-":
        if logger:
            enc = encoding or "system default"
            logger.info(f"Reading SQL from stdin (encoding={enc})")
        if encoding:
            text, _ = read_sql_bytes(sys.stdin.buffer.read(), encoding)
        else:
            text = sys.stdin.read()
    else:
        if logger:
            logger.info(f"Reading input file: {path.resolve()}")
            if encoding:
                logger.info(f"Using forced encoding: {encoding}")
        text, detected = read_sql_file(path, encoding)
        if detected:
            msg = f"Input decoded as {detected} (common for SSMS Unicode exports)"
            if logger:
                logger.info(msg)
            elif not quiet:
                typer.echo(f"[{_timestamp()}] {msg}", err=True)
    if logger:
        logger.info(f"Read {len(text)} character(s) | {len(text.splitlines())} line(s)")
    return text


def write_output(path: Optional[Path], content: str) -> None:
    """Write output to a file or stdout."""
    if path is None or str(path) == "-":
        sys.stdout.write(content)
        return
    path.write_text(content, encoding="utf-8")


def run_analyze(
    input: Path,
    report: Optional[Path],
    plain: bool,
    full: bool,
    encoding: Optional[str],
    log: bool,
    log_file: Optional[Path],
) -> None:
    """Run inventory analysis and print or save the report."""
    log_path = resolve_log_path(input, log=log, log_file=log_file)
    logger = RunLogger(log_path) if log_path else None
    success = True
    try:
        if logger:
            logger.info("Command: analyze")
            logger.info(f"Input file: {input}")
            if report:
                logger.info(f"Report file: {report.resolve()}")
        sql = read_input(input, encoding, logger=logger)
        if logger:
            logger.info("Running inventory analysis (AST + text scan)")
        inv = inventory_from_sql(sql)
        if logger:
            logger.info(f"Is File Parsable: {inv.is_parsable}")
            logger.detail(
                f"Counts: INSERT={inv.insert} | UPDATE={inv.update} | DELETE={inv.delete} | "
                f"MERGE={inv.merge} | TRY/CATCH={inv.try_catch_blocks}| "
                f"IF={inv.if_count} | WHILE={inv.while_count} | "
                f"SET(@)={inv.set_variable} | SELECT@={inv.select_assign} | "
                f"Command fragments (partial)={inv.command_fragments}"
            )
            for err in inv.errors:
                logger.error(err)
            for warn in inv.warnings:
                logger.warning(warn)
            for kind, items in inv.details.items():
                logger.detail(f"{kind}: {len(items)} statement(s)")
                for item in items[:20]:
                    logger.detail(f"  {item}")
                if len(items) > 20:
                    logger.detail(f"  ... and {len(items) - 20} more")
        colorize = supports_color() and not plain and report is None
        text = inv.to_text(colorize=colorize, non_zero_only=not full)
        if report:
            report.write_text(text + "\n", encoding="utf-8")
            if logger:
                logger.info(f"Wrote analysis report to {report.resolve()}")
            typer.echo(f"[{_timestamp()}] Report written to {report}")
        else:
            typer.echo(f"[{_timestamp()}] {text}")
    except Exception as exc:
        success = False
        if logger:
            logger.error(str(exc))
        raise
    finally:
        if logger:
            logger.close(command="analyze", success=success)
            typer.echo(f"[{_timestamp()}] Log written to {log_path}", err=True)


def run_generate(
    input: Path,
    output: Optional[Path],
    trace_style: str,
    no_stub_dml: bool,
    block_markers: bool,
    keep_comments: bool,
    quiet: bool,
    encoding: Optional[str],
    log: bool,
    log_file: Optional[Path],
) -> None:
    """Transform a stored procedure into a debug harness script."""
    if trace_style not in ("raiserror", "print"):
        typer.echo(
            f"[{_timestamp()}] [ERROR] trace-style must be 'raiserror' or 'print'",
            err=True,
        )
        raise typer.Exit(1)

    log_path = resolve_log_path(input, log=log, log_file=log_file)
    logger = RunLogger(log_path) if log_path else None
    success = True
    try:
        if logger:
            logger.info("Command: generate")
            logger.info(f"Input: {input}")
            logger.info(
                f"trace_style={trace_style} | stub_dml={not no_stub_dml} | "
                f"block_markers={block_markers} | strip_comments={not keep_comments}"
            )

        sql = read_input(input, encoding, quiet=quiet, logger=logger)

        stderr_progress = None if quiet else lambda msg: typer.echo(
            f"[{_timestamp()}] {msg}", err=True
        )
        progress = combine_progress(
            logger.as_progress_callback() if logger else None,
            stderr_progress,
        )

        result = transform_sql(
            sql,
            trace_style=trace_style,
            stub_dml=not no_stub_dml,
            add_block_markers=block_markers,
            strip_comments=not keep_comments,
            on_progress=progress,
        )

        out_path = output
        if out_path is None and str(input) != "-":
            out_path = input.with_name(f"{input.stem}_debug{input.suffix}")

        if logger:
            logger.info(f"Writing harness SQL to {out_path}")
        write_output(out_path, result.sql)
        if logger:
            out_lines = len(result.sql.splitlines())
            logger.info(f"Wrote {out_lines} line(s) to output")
            logger.detail(
                f"Summary: DML stubbed={result.stats.dml_stubbed} | "
                f"Traces added={result.stats.traces_added} | "
                f"Warnings={len(result.stats.warnings)} | "
                f"Parse errors={len(result.parse_errors)}"
            )
            for warn in result.stats.warnings:
                logger.warning(warn)
            for err in result.parse_errors:
                logger.error(err)

        summary = (
            f"Done: {result.stats.dml_stubbed} DML stubbed | "
            f"{result.stats.traces_added} traces added | "
            f"Warnings={len(result.stats.warnings)} | "
            f"Parse errors={len(result.parse_errors)}."
        )
        if out_path and str(out_path) != "-":
            typer.echo(f"[{_timestamp()}] {summary} Written to {out_path}")
        else:
            typer.echo(f"[{_timestamp()}] {summary}")

        if result.parse_errors:
            success = False
            typer.echo(
                f"[{_timestamp()}] [ERROR] Parse warnings present — review banner in output.",
                err=True,
            )
            raise typer.Exit(2)
    except typer.Exit:
        raise
    except Exception as exc:
        success = False
        if logger:
            logger.error(str(exc))
        raise
    finally:
        if logger:
            logger.close(command="generate", success=success)
            typer.echo(f"[{_timestamp()}] Log written to {log_path}", err=True)
