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

Configure [Trusted Publishing](https://docs.pypi.org/trusted-publishers/) on **both** indexes:

| Index | Environment | Workflow file |
|-------|-------------|---------------|
| [PyPI](https://pypi.org/manage/account/publishing/) | `pypi` | `publish-pypi.yml` |
| [TestPyPI](https://test.pypi.org/manage/account/publishing/) | `testpypi` | `publish-pypi.yml` |

Create matching `pypi` and `testpypi` environments under GitHub **Settings → Environments**. PyPA recommends **required reviewers** on the `pypi` environment.

Manual dry-run: **Actions → Publish to PyPI → Run workflow** → choose `testpypi` or `pypi`.

Never commit PyPI credentials; use trusted publishing or local `TWINE_*` env vars only.

## Packaging notes

- Version lives only in `src/sql_sp_harness/__init__.py` (`dynamic` version in `pyproject.toml`)
- `MANIFEST.in` excludes tests and CI files from the source distribution
- Always run `twine check dist/*` before upload (CI does this automatically)
