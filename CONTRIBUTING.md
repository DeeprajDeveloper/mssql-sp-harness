# Contributing

## First-time repo setup

```bash
cd sql-sp-harness
git clone https://github.com/DeeprajDeveloper/sql-sp-harness.git
cd sql-sp-harness
pip install -e ".[dev]"
pytest
```

## Release

1. Bump `__version__` in `src/sql_sp_harness/__init__.py` (single source of truth; `pyproject.toml` reads it at build time)
2. Run `pytest` (requires `samples/*.sql` in the repo root)
3. Commit and push to `master` / `main` / `release` — CI publishes a **TestPyPI** build automatically
4. When ready for production, tag and push: `git tag v1.x.x && git push origin v1.x.x` — CI publishes to **PyPI**

Local publish (optional):

```bash
./scripts/publish-pypi.sh
./scripts/publish-pypi.sh upload
```

### GitHub Actions → PyPI / TestPyPI

[`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) follows the [PyPA GitHub Actions guide](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/):

| Step | What happens |
|------|----------------|
| PR / push | Tests (Python 3.10, 3.12, 3.13) |
| Branch push | `python -m build`, `twine check`, upload to **TestPyPI** (`skip-existing: true`) |
| Tag `v*` push | Same build artifacts → **PyPI** |

Configure [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) on **both** indexes (they are separate accounts/sites):

| Field | PyPI | TestPyPI |
|-------|------|----------|
| Add publisher at | [pypi.org/.../publishing](https://pypi.org/manage/account/publishing/) | [test.pypi.org/.../publishing](https://test.pypi.org/manage/account/publishing/) |
| Project name | `sql-sp-harness` | `sql-sp-harness` |
| Owner | `DeeprajDeveloper` | `DeeprajDeveloper` |
| Repository | `sql-sp-harness` | `sql-sp-harness` |
| Workflow filename | `publish-pypi.yml` | `publish-pypi.yml` |
| Environment name | `pypi` | `testpypi` |

Then create matching GitHub environments: repo **Settings → Environments** → add `pypi` and `testpypi` (names must match exactly). PyPA recommends **required reviewers** on `pypi` only.

Manual dry-run: **Actions → Publish to PyPI → Run workflow** → choose `testpypi` or `pypi`.

Never commit PyPI credentials; use trusted publishing or local `TWINE_*` env vars only.

#### Troubleshooting `invalid-publisher`

If **Publish to TestPyPI** fails with `valid token, but no corresponding publisher`, the workflow is fine — TestPyPI has no matching trusted publisher yet. Fix:

1. Sign in at [test.pypi.org](https://test.pypi.org/) (not pypi.org).
2. Open [Account → Publishing](https://test.pypi.org/manage/account/publishing/) → **Add a new pending publisher**.
3. Enter the table above; **Environment name** must be `testpypi` (not `pypi`).
4. Confirm the GitHub environment `testpypi` exists under repo Settings → Environments.
5. Re-run the workflow.

For production PyPI, repeat on [pypi.org](https://pypi.org/manage/account/publishing/) with environment `pypi`.

## Packaging notes

- Version lives only in `src/sql_sp_harness/__init__.py` (`dynamic` version in `pyproject.toml`)
- `MANIFEST.in` excludes tests and CI files from the source distribution
- Always run `twine check dist/*` before upload (CI does this automatically)
