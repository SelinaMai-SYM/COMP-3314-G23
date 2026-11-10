"""Registry statuses for blocked and eligible versions."""

from experiments.v2_kmeans_protocol.dataset_registry import data_root, load_registry, probe_entry, refuse_write_under_data_root


def test_blocked_rows_are_explicit() -> None:
    rows = {(entry.benchmark, entry.version): entry for entry in load_registry()}
    assert rows[("AR", "paper840")].run_protocols is False
    assert rows[("MSRA50", "paper1799")].exact_dataset_status == "BLOCKED_DATA"
    assert rows[("UMIST", "precropped575")].exact_dataset_status == "NON_EXACT"
    assert rows[("BinAlpha", "CANDIDATE_BIN_ALPHA")].exact_dataset_status == "NON_EXACT"
    assert rows[("YaleB", "cropped2414")].benchmark_group == rows[("YaleB", "dengcai32")].benchmark_group
    assert rows[("YaleB", "cropped2414")].counts_as_independent_benchmark is False
    ar = probe_entry(rows[("AR", "paper840")])
    msra = probe_entry(rows[("MSRA50", "paper1799")])
    assert ar["experiment_status"] == "BLOCKED"
    assert msra["experiment_status"] == "BLOCKED_DATA"
    assert ar["n"] == "" and msra["n"] == ""


def test_data_root_is_not_writable_by_the_campaign(tmp_path) -> None:
    root = data_root()
    try:
        refuse_write_under_data_root(root / "benchmarks" / "orl" / "data" / "nope.npy")
    except RuntimeError as exc:
        assert "DATA_ROOT" in str(exc)
    else:
        raise AssertionError("write under DATA_ROOT was accepted")
    refuse_write_under_data_root(tmp_path / "ok.csv")
