# Python environment

Use Python 3.13 and the exact dependency versions in [requirements.lock.txt](requirements.lock.txt). From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
```

The lock includes NumPy, SciPy, scikit-learn, pandas, Matplotlib, Pillow, PyYAML, threadpoolctl, pytest, CVXPY and its convex-reference solvers. CVXPY is required for the independent small-problem checks. HTTPS tools use the pinned certifi CA bundle with certificate verification enabled.

The package targets float64 calculations. Experiment workers use one numerical-library thread each, with at most two workers and the shared resource allowance declared by the experiment configuration. Dataset and artifact directories are supplied explicitly and remain outside the checkout; see [reproducibility](../docs/reproducibility.md) and [data setup](../docs/data.md).
