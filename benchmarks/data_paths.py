"""One interpretation of external data paths for current and historical loaders."""
from pathlib import Path
import os

REPO_ROOT = Path(__file__).resolve().parents[1]


def resolve_data_root(explicit: str | Path | None = None) -> Path:
    pointer = REPO_ROOT / "local" / "data_root.txt"
    value = explicit or os.environ.get("COMP3314_DATA_ROOT")
    if not value and pointer.is_file():
        value = pointer.read_text().strip()
    root = Path(value).expanduser() if value else REPO_ROOT / "benchmarks"
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(
            f"Benchmark root {root} does not exist. Set --data-root or "
            "COMP3314_DATA_ROOT to a directory containing orl/data, jaffe/data, "
            "yaleb/data, usps/data. See docs/final/data_setup.md."
        )
    return root
