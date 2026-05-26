# Contributing

## First-time repo setup

```bash
cd sql-sp-harness
git init
git add .
git commit -m "Initial commit: sql-sp-harness 1.0.0"
git remote add origin git@github.com:DeeprajDeveloper/sql-sp-harness.git
git push -u origin master
```

## Release

1. Bump `version` in `pyproject.toml` and `src/sql_sp_harness/__init__.py`
2. `pytest` (requires `samples/*.sql` fixtures in the repo root)
3. `./scripts/publish-pypi.sh` then `./scripts/publish-pypi.sh upload`
4. Git tag `v1.x.x`

PyPI uploads use [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) or `TWINE_USERNAME` / `TWINE_PASSWORD` in the environment — never commit credentials.

## VS Code extension

The editor extension lives separately: [mssql-sp-debug-scripter](https://github.com/DeeprajDeveloper/mssql-sp-debug-scripter) (update it to depend on `sql-sp-harness` after rename).
