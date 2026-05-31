"""Strip T-SQL line and block comments (string-aware)."""

from __future__ import annotations

from sql_sp_harness.run_log import LogCallback, emit_log, truncate_for_log

_MAX_DETAIL_LINES = 80


def strip_line_comment(line: str) -> str:
    """Remove trailing ``--`` comment from a line (string-aware, not full-line-only)."""
    out: list[str] = []
    i = 0
    in_string = False
    while i < len(line):
        character_value = line[i]
        if character_value == "'":
            if in_string and i + 1 < len(line) and line[i + 1] == "'":
                out.append("''")
                i += 2
                continue
            in_string = not in_string
            out.append(character_value)
            i += 1
            continue
        if not in_string and character_value == "-" and i + 1 < len(line) and line[i + 1] == "-":
            break
        out.append(character_value)
        i += 1
    return "".join(out)


def strip_block_comments_on_line(line: str, in_block_comment: bool) -> tuple[str, bool]:
    """
    Remove block/line comments from one line; return (text, still_inside_block).

    examples:
        "/* comment */ SELECT 1" -> "SELECT 1"
    """
    if in_block_comment:
        end = line.find("*/")
        if end == -1:
            return "", True
        line = line[end + 2 :]
        in_block_comment = False

    while True:
        start = line.find("/*")
        if start == -1:
            break
        end = line.find("*/", start + 2)
        if end == -1:
            return strip_line_comment(line[:start]), True
        line = line[:start] + line[end + 2 :]

    return strip_line_comment(line), in_block_comment


def strip_sql_comments(sql: str, *, on_detail: LogCallback | None = None) -> str:
    """Remove line and block comments from a script; drop lines that become empty."""
    had_trailing_newline = sql.endswith("\n")
    raw_lines = sql.splitlines()
    emit_log(on_detail, "strip_sql_comments", f"Comment strip: scanning {len(raw_lines)} line(s)")

    in_block_comment = False
    kept: list[str] = []
    removed_line_count = 0
    modified_line_count = 0
    detail_budget = _MAX_DETAIL_LINES

    for line_no, raw in enumerate(raw_lines, start=1):
        prev_in_block = in_block_comment
        effective, in_block_comment = strip_block_comments_on_line(raw, in_block_comment)
        stripped = effective.rstrip()
        changed = effective != raw or prev_in_block != in_block_comment

        if changed and detail_budget > 0:
            if prev_in_block and not stripped:
                emit_log(
                    on_detail,
                    "strip_sql_comments",
                    f"  line {line_no}: removed (inside block comment): "
                    f"{truncate_for_log(raw)}",
                )
            elif prev_in_block:
                emit_log(
                    on_detail,
                    "strip_sql_comments",
                    f"  line {line_no}: block comment ended, kept: "
                    f"{truncate_for_log(stripped)}",
                )
            elif in_block_comment and not prev_in_block:
                emit_log(
                    on_detail,
                    "strip_sql_comments",
                    f"  line {line_no}: block comment started, removed prefix: "
                    f"{truncate_for_log(raw)}",
                )
            else:
                emit_log(
                    on_detail,
                    "strip_sql_comments",
                    f"  line {line_no}: stripped comment(s): "
                    f"{truncate_for_log(raw)} -> {truncate_for_log(stripped)}",
                )
            detail_budget -= 1
            modified_line_count += 1

        if stripped:
            kept.append(stripped)
        elif raw.strip() or prev_in_block:
            removed_line_count += 1
            if detail_budget > 0 and not changed:
                emit_log(
                    on_detail,
                    "strip_sql_comments",
                    f"  line {line_no}: dropped empty line after strip: "
                    f"{truncate_for_log(raw)}",
                )
                detail_budget -= 1

    if modified_line_count > _MAX_DETAIL_LINES:
        emit_log(
            on_detail,
            "strip_sql_comments",
            f"  ... {modified_line_count - _MAX_DETAIL_LINES} more modified line(s) not listed",
        )
    emit_log(
        on_detail,
        "strip_sql_comments",
        f"Comment strip done: kept {len(kept)} line(s), removed {removed_line_count} empty line(s), "
        f"modified {modified_line_count} line(s)",
    )

    if not kept:
        return "\n" if had_trailing_newline else ""
    body = "\n".join(kept)
    return body + "\n" if had_trailing_newline else body
