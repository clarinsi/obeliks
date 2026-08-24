# Publishing obeliks to PyPI

This repo is a classic `setup.py`-based package. These steps build a
source distribution (sdist) and a wheel, then upload them to PyPI.

## Prerequisites

- Python 3.x and `pip`
- A [PyPI account](https://pypi.org/account/register/) (and optionally a
  separate [TestPyPI](https://test.pypi.org/account/register/) account)
- An API token from PyPI → *Account settings* → *API tokens*
  (scope: *whole account* or a project-scoped token for `obeliks`)

Install the build tooling (once):

```shell
pip install build twine
```

## 1. Bump the version

Update `version=` in `setup.py` before every release. PyPI refuses to
re-upload an already-published version number:

```python
setup(
    ...
    version="1.1.8",
    ...
)
```

Then commit and tag it:

```shell
git add setup.py
git commit -m "Bump version to 1.1.8"
git tag v1.1.8
git push origin master --tags
```

## 2. Build the distributions

```shell
python -m build
```

This creates `dist/obeliks-1.1.8.tar.gz` (sdist) and
`dist/obeliks-1.1.8-py3-none-any.whl` (wheel). The `package_data`
(`res/*.txt`) and the console script (`obeliks/obeliks`) are picked up
automatically from `setup.py`.

## 3. (Recommended) Test on TestPyPI first

Upload to TestPyPI:

```shell
twine upload --repository testpypi dist/*
```

Install from TestPyPI in a clean virtualenv and smoke-test:

```shell
pip install --index-url https://test.pypi.org/simple/ obeliks
obeliks "To je stavek."
python -c "import obeliks; print(obeliks.run('Pozdravljen, svet!', conllu=True))"
```

> Note: TestPyPI doesn't proxy dependencies, so if `lxml`/`regex` are
> missing, install them from PyPI first or use
> `--extra-index-url https://pypi.org/simple/`.

## 4. Upload to PyPI

```shell
twine upload dist/*
```

`twine` will ask for your username (`__token__`) and password (the
`pypi-...` token, including the `pypi-` prefix). You can also preconfigure
a token to avoid typing it each time:

```shell
# ~/.pypirc
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

## 5. Verify

```shell
pip install --upgrade obeliks   # ideally in a fresh virtualenv
obeliks -h
python -c "import obeliks; print(obeliks.run('Pozdravljen, svet!', conllu=True))"
```

Check the project page at <https://pypi.org/project/obeliks/> — the
README renders as the long description, and the sdist/wheel files should
be listed under *Download files*.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `File already exists` on upload | Version `1.1.7` is already on PyPI — bump the version (step 1) |
| `401/403 Invalid or non-existent authentication information` | Use username `__token__` and the full `pypi-...` token |
| Package installs but `res/*.txt` missing | Check the wheel contains them: `unzip -l dist/*.whl` (should list `obeliks/res/*.txt`) |
| Command `obeliks` not found | It comes from `scripts=["obeliks/obeliks"]`; it is only installed in the environment where you ran `pip install` |
| Want to delete a bad release | PyPI doesn't allow deleting releases; upload a new version instead |

## Notes

- The `.gitignore` already excludes `build/`, `dist/`, and `*.egg-info/`,
  so build artifacts won't be committed.
- There is no `pyproject.toml`; the legacy `setup.py` is fully
  supported, but you may optionally add a minimal one later to pin the
  build backend:
  ```toml
  [build-system]
  requires = ["setuptools>=61", "wheel"]
  build-backend = "setuptools.build_meta"
  ```
- Official reference: <https://packaging.python.org/en/latest/tutorials/packaging-projects/>
