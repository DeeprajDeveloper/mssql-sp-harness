"""Normalize SSMS-style deploy scripts for analysis and debug harness generation."""

from __future__ import annotations

import re

from sql_sp_harness.constants import (
    CREATE_PROC,
    CREATE_PROC_INLINE,
    AS_LINE,
    PROC_PARAM_WITH_DEFAULT,
    PROC_PARAM_PLAIN,
    AS_BEGIN_REST,
    IF_EXISTS,
    DROP_PROCEDURE,
    SET_ANSI_NULLS,
    SET_QUOTED_IDENTIFIER,
    STANDALONE_DROP_PROC,
)


def _split_param_list(text: str) -> list[str]:
    """Split a parameter list on commas (parenthesis-aware)."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in text:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "," and depth == 0:
            part = "".join(current).strip()
            if part:
                parts.append(part)
            current = []
            continue
        current.append(ch)
    tail = "".join(current).strip()
    if tail:
        parts.append(tail)
    return parts


def strip_deploy_preamble(sql: str) -> str:
    """Remove IF EXISTS/DROP PROCEDURE and SET ANSI_NULLS / QUOTED_IDENTIFIER setup."""
    had_trailing_newline = sql.endswith("\n")
    lines = sql.splitlines()
    kept: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if IF_EXISTS.match(line):
            i += 1
            while i < len(lines):
                if DROP_PROCEDURE.search(lines[i]):
                    i += 1
                    break
                i += 1
            continue
        if STANDALONE_DROP_PROC.match(line):
            i += 1
            continue
        if SET_ANSI_NULLS.match(line) or SET_QUOTED_IDENTIFIER.match(line):
            i += 1
            continue
        kept.append(line)
        i += 1
    if not kept:
        return "\n" if had_trailing_newline else ""
    body = "\n".join(kept)
    return body + "\n" if had_trailing_newline else body


def _parse_parameter_chunks(chunks: list[str]) -> list[tuple[str, str, str | None]]:
    """Return (@name, type_sql, default_expr|None) from comma-split param chunks."""
    params: list[tuple[str, str, str | None]] = []
    for chunk in chunks:
        text = chunk.strip().rstrip(",").strip()
        if not text or not text.startswith("@"):
            continue
        match = PROC_PARAM_WITH_DEFAULT.match(text)
        if match:
            params.append(
                (match.group(1), match.group(2).strip(), match.group(3).strip())
            )
            continue
        match = PROC_PARAM_PLAIN.match(text)
        if match:
            params.append((match.group(1), match.group(2).strip(), None))
    return params


def _declare_lines_for_params(
    proc_name: str,
    params: list[tuple[str, str, str | None]],
    indent: str,
) -> list[str]:
    header = (
        f"{indent}-- [DBG] Harness: was CREATE PROCEDURE {proc_name}; set parameter values below."
    )
    if not params:
        return [header, f"{indent}-- (no parameters)"]
    lines = [header]
    for name, type_sql, default in params:
        if default:
            lines.append(f"{indent}DECLARE {name} {type_sql} = {default};")
        else:
            lines.append(
                f"{indent}DECLARE {name} {type_sql} = NULL;  -- TODO: set test value"
            )
    return lines


def _split_create_tail(tail: str) -> tuple[str, bool]:
    """Split ``@params... AS [BEGIN]`` tail into param text and whether BEGIN follows."""
    match = re.search(r"\s+AS(?:\s+BEGIN)?\s*$", tail, re.IGNORECASE)
    if not match:
        return tail.strip(), False
    param_text = tail[: match.start()].strip()
    has_begin = "BEGIN" in match.group(0).upper()
    return param_text, has_begin


def convert_create_procedure_to_declares(sql: str) -> str:
    """Replace CREATE PROCEDURE header with DECLARE parameters (debug script, no CREATE)."""
    lines = sql.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        head = CREATE_PROC.match(line)
        if not head:
            out.append(line)
            i += 1
            continue

        proc_name = head.group(1)
        indent_match = re.match(r"^(\s*)", line)
        indent = indent_match.group(1) if indent_match else ""

        inline = CREATE_PROC_INLINE.match(line)
        param_chunks: list[str] = []
        as_has_begin = False

        body_suffix = ""
        if inline and inline.group(2).strip():
            tail = inline.group(2).strip()
            begin_rest = AS_BEGIN_REST.match(tail)
            if begin_rest:
                as_has_begin = True
                body_suffix = begin_rest.group(1).strip()
                param_text = ""
            else:
                param_text, as_has_begin = _split_create_tail(tail)
                if param_text:
                    param_chunks = _split_param_list(param_text)
            i += 1
        else:
            i += 1
            param_parts: list[str] = []
            while i < len(lines):
                if AS_LINE.match(lines[i]):
                    as_has_begin = bool(re.search(r"\bBEGIN\b", lines[i], re.IGNORECASE))
                    i += 1
                    break
                param_parts.append(lines[i].strip())
                i += 1
            param_chunks = _split_param_list(" ".join(param_parts))

        params = _parse_parameter_chunks(param_chunks)
        out.extend(_declare_lines_for_params(proc_name, params, indent))

        if as_has_begin:
            out.append(f"{indent}BEGIN")
            if body_suffix:
                out.append(f"{indent}{body_suffix}" if indent else body_suffix)
        elif i < len(lines) and lines[i].strip().upper() == "BEGIN":
            out.append(lines[i])
            i += 1
        continue

    return "\n".join(out)


def prepare_for_analysis(sql: str, *, strip_preamble: bool = True) -> str:
    if strip_preamble:
        sql = strip_deploy_preamble(sql)
    return sql


def prepare_for_transform(
    sql: str,
    *,
    strip_preamble: bool = True,
    inline_proc_params: bool = True,
) -> str:
    if strip_preamble:
        sql = strip_deploy_preamble(sql)
    if inline_proc_params:
        sql = convert_create_procedure_to_declares(sql)
    return sql
