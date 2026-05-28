"""Decode T-SQL script files from common SQL Server / SSMS encodings."""

from __future__ import annotations

from pathlib import Path

from sql_sp_harness.constants import UTF16_BE_BOM, UTF16_LE_BOM, UTF8_BOM


def decode_sql_bytes(data: bytes, encoding: str | None = None) -> tuple[str, str]:
    """Decode script bytes to str. Returns (text, encoding_used)."""
    if not data:
        return "", encoding or "utf-8"

    if encoding:
        return data.decode(encoding), encoding

    if data.startswith(UTF16_LE_BOM):
        return data.decode("utf-16-le"), "utf-16-le"
    if data.startswith(UTF16_BE_BOM):
        return data.decode("utf-16-be"), "utf-16-be"
    if data.startswith(UTF8_BOM):
        return data.decode("utf-8-sig"), "utf-8-sig"

    if _looks_like_utf16_le_without_bom(data):
        return data.decode("utf-16-le"), "utf-16-le"

    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    # Windows-1252: smart quotes, en-dash (0x96), etc. from SSMS on Windows.
    return data.decode("cp1252"), "cp1252"


def _looks_like_utf16_le_without_bom(data: bytes) -> bool:
    """Heuristic for BOM-less UTF-16 LE (null byte every other byte in ASCII header)."""
    if len(data) < 4 or len(data) % 2 != 0:
        return False
    sample = data[: min(200, len(data))]
    if sample[1] != 0:
        return False
    nulls = sum(1 for i in range(1, len(sample), 2) if sample[i] == 0)
    return nulls >= len(sample) // 4


def read_sql_file(path: Path, encoding: str | None = None) -> tuple[str, str | None]:
    """Read a .sql file; returns (text, detected_encoding or None if explicit)."""
    data = path.read_bytes()
    text, used = decode_sql_bytes(data, encoding)
    if encoding:
        return text, None
    return text, used if used != "utf-8" else None


def read_sql_bytes(data: bytes, encoding: str | None = None) -> tuple[str, str | None]:
    """Decode in-memory bytes (tests, stdin buffer)."""
    text, used = decode_sql_bytes(data, encoding)
    if encoding:
        return text, None
    return text, used if used != "utf-8" else None
