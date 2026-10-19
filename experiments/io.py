"""Run-directory writers. Status values are real transitions, not labels."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

VALID_STATUS = (
    "PLANNED",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "TIMEOUT",
    "INTERRUPTED",
    "SKIPPED",
)

ALLOWED_TRANSITIONS = {
    "PLANNED": {"RUNNING", "SKIPPED", "FAILED", "INTERRUPTED"},
    "RUNNING": {"COMPLETED", "FAILED", "TIMEOUT", "INTERRUPTED"},
    "COMPLETED": set(),
    "FAILED": set(),
    "TIMEOUT": set(),
    "INTERRUPTED": set(),
    "SKIPPED": set(),
}


def local_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def utc_now() -> str:
    from datetime import timezone

    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def config_hash(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, default=str, ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def make_run_id(track: str, method: str, dataset: str, hashed: str, when: datetime | None = None) -> str:
    stamp = (when or datetime.now().astimezone()).strftime("%Y%m%d_%H%M%S")
    track_s = _token(track)
    method_s = _token(method)
    dataset_s = _token(dataset)
    return f"{stamp}__{track_s}__{method_s}__{dataset_s}__{hashed}"


def _token(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in str(value).upper())
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "X"


class Tee:
    def __init__(self, *streams: Any) -> None:
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
            stream.flush()
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()

    def isatty(self) -> bool:
        return False


class RunWriter:
    def __init__(self, run_dir: Path) -> None:
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._status_path = self.run_dir / "status.json"
        self._stdout_path = self.run_dir / "stdout.log"
        self._stderr_path = self.run_dir / "stderr.log"
        self._stdout_file = None
        self._stderr_file = None
        self._old_stdout = None
        self._old_stderr = None

    def write_config(self, config: dict[str, Any]) -> None:
        path = self.run_dir / "config.yaml"
        with path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(config, handle, sort_keys=False, allow_unicode=True)

    def write_metadata(self, metadata: dict[str, Any]) -> None:
        _write_json(self.run_dir / "metadata.json", metadata)

    def write_environment(self, extra: dict[str, Any] | None = None) -> None:
        env = collect_environment()
        if extra:
            env.update(extra)
        _write_json(self.run_dir / "environment.json", env)

    def write_status(self, status: str, **fields: Any) -> dict[str, Any]:
        if status not in VALID_STATUS:
            raise ValueError(f"unknown status {status}")
        current = self.read_status()
        previous = current.get("status")
        if previous is None:
            current = {
                "status": status,
                "created_at": local_now(),
                "created_at_utc": utc_now(),
                "transitions": [],
            }
        else:
            allowed = ALLOWED_TRANSITIONS.get(previous, set())
            if status != previous and status not in allowed:
                raise RuntimeError(f"illegal status transition {previous} -> {status}")
        stamp = local_now()
        current["status"] = status
        current["updated_at"] = stamp
        current["updated_at_utc"] = utc_now()
        if status == "RUNNING":
            current["started_at"] = stamp
        if status in {"COMPLETED", "FAILED", "TIMEOUT", "INTERRUPTED", "SKIPPED"}:
            current["finished_at"] = stamp
        transition = {"status": status, "at": stamp, "at_utc": utc_now()}
        transition.update({k: v for k, v in fields.items() if v is not None})
        current.setdefault("transitions", []).append(transition)
        current.update({k: v for k, v in fields.items() if v is not None})
        _write_json(self._status_path, current)
        return current

    def read_status(self) -> dict[str, Any]:
        if not self._status_path.is_file():
            return {}
        with self._status_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def write_metrics(self, metrics: dict[str, Any]) -> None:
        _write_json(self.run_dir / "metrics.json", metrics)

    def write_objective_history(self, history: list[dict[str, Any]]) -> None:
        path = self.run_dir / "objective_history.csv"
        if not history:
            path.write_text("iteration\n", encoding="utf-8")
            return
        keys: list[str] = []
        for row in history:
            for key in row:
                if key not in keys:
                    keys.append(str(key))
        lines = [",".join(keys)]
        for row in history:
            lines.append(",".join(_csv_cell(row.get(key, "")) for key in keys))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def capture_stdio(self) -> None:
        self._stdout_file = self._stdout_path.open("a", encoding="utf-8")
        self._stderr_file = self._stderr_path.open("a", encoding="utf-8")
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        sys.stdout = Tee(self._old_stdout, self._stdout_file)
        sys.stderr = Tee(self._old_stderr, self._stderr_file)

    def release_stdio(self) -> None:
        if self._old_stdout is not None:
            sys.stdout = self._old_stdout
        if self._old_stderr is not None:
            sys.stderr = self._old_stderr
        for handle in (self._stdout_file, self._stderr_file):
            if handle is not None:
                handle.close()
        self._stdout_file = None
        self._stderr_file = None

    def append_exception(self, exc: BaseException) -> None:
        text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        with self._stderr_path.open("a", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()


def collect_environment() -> dict[str, Any]:
    versions = {"python": sys.version}
    for name in ("numpy", "scipy", "sklearn", "pandas", "matplotlib", "yaml"):
        try:
            mod = __import__(name if name != "sklearn" else "sklearn")
            versions[name] = getattr(mod, "__version__", "unknown")
        except Exception as exc:  # noqa: BLE001
            versions[name] = f"unavailable: {type(exc).__name__}"
    return {
        "python_executable": sys.executable,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count_os": os.cpu_count(),
        "hostname": platform.node(),
        "pid": os.getpid(),
        "cwd": str(Path.cwd()),
        "versions": versions,
        "env_thread_limits": {
            key: os.environ.get(key)
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "collected_at": local_now(),
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, indent=2, sort_keys=True, default=_json_default)
    path.write_text(serialized + "\n", encoding="utf-8")


def _json_default(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _csv_cell(value: Any) -> str:
    if value is None:
        return ""
    text = str(value)
    if "," in text or '"' in text or "\n" in text:
        return '"' + text.replace('"', '""') + '"'
    return text
