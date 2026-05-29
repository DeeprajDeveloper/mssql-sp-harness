"""Strip T-SQL line and block comments (string-aware)."""

from __future__ import annotations


def strip_line_comment(line: str) -> str:
    """Remove trailing ``--`` comment from a line (respects single-quoted strings)."""
    out: list[str] = []
    i = 0
    in_string = False
    while i < len(line):
        ch = line[i]
        if ch == "'":
            if in_string and i + 1 < len(line) and line[i + 1] == "'":
                out.append("''")
                i += 2
                continue
            in_string = not in_string
            out.append(ch)
            i += 1
            continue
        if not in_string and ch == "-" and i + 1 < len(line) and line[i + 1] == "-":
            break
        out.append(ch)
        i += 1
    return "".join(out)


def strip_block_comments_on_line(line: str, in_block_comment: bool) -> tuple[str, bool]:
    """Remove block/line comments from one line; return (text, still_inside_block)."""
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


def strip_sql_comments(sql: str) -> str:
    """Remove line and block comments from a script; drop lines that become empty."""
    had_trailing_newline = sql.endswith("\n")
    in_block_comment = False
    kept: list[str] = []
    for raw in sql.splitlines():
        effective, in_block_comment = strip_block_comments_on_line(raw, in_block_comment)
        stripped = effective.rstrip()
        if stripped:
            kept.append(stripped)
    if not kept:
        return "\n" if had_trailing_newline else ""
    body = "\n".join(kept)
    return body + "\n" if had_trailing_newline else body
