"""Hashes and cache keys for v3 measurements."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np


def sha256_array(array: np.ndarray) -> str:
    contiguous = np.ascontiguousarray(array)
    digest = hashlib.sha256()
    digest.update(str(contiguous.shape).encode())
    digest.update(str(contiguous.dtype).encode())
    digest.update(contiguous.tobytes())
    return digest.hexdigest()


def fingerprint_matrix(features: np.ndarray, labels: np.ndarray | None = None) -> dict[str, Any]:
    payload = {
        "x_sha256": sha256_array(np.asarray(features)),
        "x_shape": list(np.asarray(features).shape),
        "x_dtype": str(np.asarray(features).dtype),
    }
    if labels is not None:
        payload["y_sha256"] = sha256_array(np.asarray(labels))
        payload["y_shape"] = list(np.asarray(labels).shape)
    return payload


def cache_key(*, fingerprint: dict[str, Any], config: dict[str, Any], code_commit: str) -> str:
    """Provenance key. A new source commit cannot reuse another commit's cache."""
    body = {
        "fingerprint": fingerprint,
        "config": config,
        "code_commit": code_commit,
    }
    encoded = json.dumps(body, sort_keys=True, default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(item) for item in value]
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.floating):
        number = float(value)
        return number if np.isfinite(number) else None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return str(value)


def source_fingerprint(root=None) -> str:
    from pathlib import Path
    root=Path(root) if root is not None else Path(__file__).resolve().parents[2]
    digest=hashlib.sha256()
    for folder in ['SSC_method','benchmarks','baselines','method_extension','experiments','configs']:
        for path in sorted((root/folder).rglob('*')):
            if path.is_file() and path.suffix in {'.py','.yaml','.yml','.toml'} and 'data' not in path.parts and '__pycache__' not in path.parts:
                digest.update(str(path.relative_to(root)).encode());digest.update(path.read_bytes())
    return digest.hexdigest()


def environment_record() -> dict:
    import platform, importlib.metadata
    return {'python':platform.python_version(),'platform':platform.platform(),'packages':{name:importlib.metadata.version(name) for name in ['numpy','scipy','scikit-learn','pandas','PyYAML','Pillow']}}
