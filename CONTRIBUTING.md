# Contributing

## First-time repo setup

```bash
cd mssql-sp-harness
git init
git add .
git commit -m "Initial commit: mssql-sp-harness 1.1.0"
git remote add origin git@github.com:DeeprajDeveloper/mssql-sp-harness.git
git push -u origin main
```

## Release

1. Bump `version` in `pyproject.toml` and `src/mssql_sp_harness/__init__.py`
2. `pytest` (requires `samples/*.sql` fixtures in the repo root)
3. `./scripts/publish-pypi.sh` then `./scripts/publish-pypi.sh upload`
4. Git tag `v1.x.x`

PyPI uploads use [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) or `TWINE_USERNAME` / `TWINE_PASSWORD` in the environment — never commit credentials.

## Extension repo

VS Code extension lives separately: [mssql-sp-debug-scripter](https://github.com/DeeprajDeveloper/mssql-sp-debug-scripter).
