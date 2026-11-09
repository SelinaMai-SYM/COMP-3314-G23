"""Independent best-of-50 batches.

Batch 0 uses seeds 0..49 and is the primary batch. Later batches use
disjoint predetermined blocks ``50*b .. 50*b+49``. The mean and SD in the
repeatability summary are taken across selected trials, one per batch.
They are not the SD of the 50 runs inside a batch.
"""

from __future__ import annotations

from experiments.v2_kmeans_protocol.dataset_registry import DatasetEntry
from experiments.v2_kmeans_protocol.protocol_runner import run_repeatability


def run(entry: DatasetEntry, *, n_batches: int = 10, max_iter: int = 300) -> int:
    return run_repeatability(entry, n_batches=n_batches, max_iter=max_iter)


__all__ = ["run"]
