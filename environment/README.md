# Python environment

The checked environment is CPython 3.13.3. From the repository root:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
python -m pip install --no-deps --no-build-isolation -e .
```

The lock file pins the direct scientific, plotting and reference-test dependencies. The Python package declares the runtime dependencies in `pyproject.toml`; the checked environment additionally includes pytest, CVXPY, CLARABEL and OSQP. TeX Live, BibTeX and Poppler are required only for rebuilding the report and diagram.
