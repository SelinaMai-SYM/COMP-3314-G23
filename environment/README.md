# Environment

The library does not read data files or hard-code absolute paths. These historical checks were run from the repository root (then named `v1`):

```bash
python3 -m pytest
```

`pyproject.toml` adds the repository root to `pythonpath`, so an editable installation was not required for those tests.

## Interpreter checked at that stage

The historical system interpreter was `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3`, version 3.13.3. Use a fresh environment and `requirements.lock.txt` for current validation.

The following installed versions were used for the historical tests:

| Package | Version |
| --- | --- |
| numpy | 2.4.2 |
| scipy | 1.17.1 |
| scikit-learn | 1.8.0 |
| pandas | 2.3.3 |
| matplotlib | 3.10.8 |
| PyYAML | 6.0.3 |
| pytest | 9.1.1 |

pytest 9.1.1 and optional cvxpy 1.9.3 (CLARABEL) were installed in the user environment with `python3 -m pip install --user`; they were not stored in this repository. Historical PyPI certificate verification failed and that installation used `--trusted-host pypi.org --trusted-host files.pythonhosted.org`. This describes the old setup, not the current installation instructions. Current installation must verify TLS using a valid CA bundle. cvxpy supplied independent convex checks in `tests/test_ssc.py`; missing cvxpy causes `pytest.importorskip` to skip those checks. The Equation (12) quadratic reference used scipy.optimize L-BFGS-B and did not require cvxpy.

The Anaconda scikit-learn binary was incompatible with the installed NumPy, so those tests did not use `/opt/anaconda3/bin/python`.

## Current HTTPS audit dependency

The pinned environment includes `certifi==2026.2.25`, the installed version checked on 2026-11-10. `scripts/submission_refresh/link_audit.py` uses its CA bundle for verified HTTPS requests. This explicit dependency is required by fresh environments; adding the pin does not substitute for the final isolated-environment and published-link checks. TLS verification remains enabled.

## Historical disk note

Approximately 9.2 GiB remained on the data volume then. Raw images and virtual environments were kept outside the repository. Current pinned dependencies are in `requirements.lock.txt`; this old disk estimate is not the current resource inventory.
