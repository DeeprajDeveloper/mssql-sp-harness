<p align="center">
  <img
    src="https://raw.githubusercontent.com/DeeprajDeveloper/sql-sp-harness/master/docs/BANNER.png"
    alt="sql-sp-harness"
    width="220"
  >
</p>

# sql-sp-harness

**T-SQL Stored Procedure Debug Harness** — turn SQL Server stored procedures into **safe, runnable debug scripts** you can execute on a pre-production database without writing to real tables.

> Not a live debugger. This tool generates a **static test harness** (DML previews + variable traces), not breakpoints or step-into debugging.
>
> Not affiliated with Microsoft. "SQL Server" and T-SQL are used descriptively only.

## What it does

| Command | Purpose |
|---------|---------|
| `analyze` | See what keyword elements that procedure contains along with counts — DML, TRY/CATCH, loops, SET, line-level detail |
| `generate` | Create a debug harness: real-table DML → `SELECT` previews, `PRINT` traces on variables |

Output includes a banner on the top of the procedure stating: **DEBUG HARNESS — DO NOT RUN ON PRODUCTION**.

## Install

```bash
pip install sql-sp-harness
```

Requires **Python 3.10+**.

Verify:

```bash
sql-sp-harness version
python -m sql_sp_harness version
```

## Quick start

```bash
sql-sp-harness analyze -i MyProc.sql
sql-sp-harness generate -i MyProc.sql -o MyProc_debug.sql
```

With traces in the Messages tab (default):

```bash
sql-sp-harness generate -i MyProc.sql -o MyProc_debug.sql --trace-style print
```

## Development

```bash
git clone https://github.com/DeeprajDeveloper/sql-sp-harness.git
cd sql-sp-harness
pip install -e ".[dev]"
pytest
```

Build for PyPI:

```bash
./scripts/publish-pypi.sh
./scripts/publish-pypi.sh upload
```

## Limitations

| Pattern | Behavior |
|---------|----------|
| Dynamic SQL | Not analyzed |
| Encrypted procedures | No source |
| Cursors | Not rewritten |
| DDL inside proc | Not stubbed |

Always review generated scripts before running on a shared server.

## License

MIT
