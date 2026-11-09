"""Six summary figures. Missing measurements are omitted, not drawn as zero."""

from __future__ import annotations

import csv

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experiments.v2_kmeans_protocol.aggregate_results import RESULTS


def _read(name: str) -> list[dict[str, str]]:
    path = RESULTS / name
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _completed(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("experiment_status") == "COMPLETED" and row.get("acc_percent")]


def _label(row: dict[str, str]) -> str:
    return f"{row['benchmark']}:{row['dataset_version']}"


def _save(fig: plt.Figure, name: str) -> None:
    path = RESULTS / "figures" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _empty(name: str, message: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axis("off")
    ax.text(0.01, 0.5, message, fontsize=11)
    _save(fig, name)


def make_figures() -> list[str]:
    primary = _completed(_read("primary_2x4_matrix.csv"))
    ablation = [row for row in _read("sc_vs_ssc_ablation.csv") if row.get("experiment_status") == "COMPLETED"]
    gamma = _read("gamma_sensitivity.csv")
    figures = RESULTS / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    comparable = [
        row
        for row in ablation
        if row["protocol"] == "RANDOM_MEAN50"
        and row["comparison_class"] != "NOT_COMPARABLE"
        and row.get("our_ssc_acc_percent")
    ]
    if comparable:
        fig, ax = plt.subplots(figsize=(10, 4))
        labels = [_label(row) for row in comparable]
        x = range(len(labels))
        ax.bar([i - 0.15 for i in x], [float(row["our_ssc_acc_percent"]) for row in comparable], width=0.3, label="Our SSC P1")
        ax.bar([i + 0.15 for i in x], [float(row["paper_ssc_acc_percent"]) for row in comparable], width=0.3, label="Paper SSC")
        ax.set_xticks(list(x), labels, rotation=30, ha="right")
        ax.set_ylabel("ACC (%)")
        ax.set_title("Paper SSC versus our gamma=1 random mean")
        ax.legend()
        _save(fig, "paper_vs_reproduction.pdf")
    else:
        _empty("paper_vs_reproduction.pdf", "No comparable completed SSC P1 rows.")

    def _delta(protocol_a: str, protocol_b: str, representation: str) -> list[tuple[str, float]]:
        points = []
        keys = {(row["benchmark"], row["dataset_version"]) for row in primary}
        for benchmark, version in sorted(keys):
            left = next((row for row in primary if row["benchmark"] == benchmark and row["dataset_version"] == version and row["protocol"] == protocol_a and row["representation"] == representation), None)
            right = next((row for row in primary if row["benchmark"] == benchmark and row["dataset_version"] == version and row["protocol"] == protocol_b and row["representation"] == representation), None)
            if left and right:
                points.append((f"{benchmark}:{version}:{representation}", float(right["acc_percent"]) - float(left["acc_percent"])))
        return points

    random_vs = _delta("RANDOM_MEAN50", "KMEANSPP_MEAN50", "G") + _delta("RANDOM_MEAN50", "KMEANSPP_MEAN50", "F")
    if random_vs:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(range(len(random_vs)), [value for _label_text, value in random_vs])
        ax.set_xticks(range(len(random_vs)), [label for label, _value in random_vs], rotation=30, ha="right")
        ax.set_ylabel("ACC percentage points")
        ax.set_title("K-means++ mean minus random mean")
        ax.axhline(0.0, color="black", linewidth=0.8)
        _save(fig, "random_vs_kmeanspp.pdf")
    else:
        _empty("random_vs_kmeanspp.pdf", "No completed random and k-means++ means.")

    mean_vs = _delta("RANDOM_MEAN50", "RANDOM_BEST_INERTIA50", "G") + _delta("KMEANSPP_MEAN50", "KMEANSPP_BEST_INERTIA50", "G")
    if mean_vs:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(range(len(mean_vs)), [value for _label_text, value in mean_vs])
        ax.set_xticks(range(len(mean_vs)), [label for label, _value in mean_vs], rotation=30, ha="right")
        ax.set_ylabel("ACC percentage points")
        ax.set_title("Minimum-inertia selection minus the 50-run mean (SSC)")
        ax.axhline(0.0, color="black", linewidth=0.8)
        _save(fig, "mean_vs_best_inertia.pdf")
    else:
        _empty("mean_vs_best_inertia.pdf", "No completed mean and best-inertia pairs.")

    gains = [row for row in ablation if row.get("our_ssc_minus_sc_pp")]
    if gains:
        fig, ax = plt.subplots(figsize=(10, 4))
        labels = [f"{row['benchmark']}:{row['protocol']}" for row in gains]
        ax.bar(range(len(gains)), [float(row["our_ssc_minus_sc_pp"]) for row in gains])
        ax.set_xticks(range(len(gains)), labels, rotation=30, ha="right")
        ax.set_ylabel("ACC percentage points")
        ax.set_title("Our SSC minus SC under the same protocol")
        ax.axhline(0.0, color="black", linewidth=0.8)
        _save(fig, "sc_to_ssc_gain.pdf")
    else:
        _empty("sc_to_ssc_gain.pdf", "No completed SC/SSC pairs.")

    gamma_points = [
        row
        for row in gamma
        if row.get("result_label") == "PREDECLARED_GRID"
        and row.get("representation") == "G"
        and row.get("protocol") == "RANDOM_MEAN50"
        and row.get("experiment_status") == "COMPLETED"
    ]
    if gamma_points:
        fig, ax = plt.subplots(figsize=(8, 4))
        for key in sorted({_label(row) for row in gamma_points}):
            series = [row for row in gamma_points if _label(row) == key]
            series.sort(key=lambda row: float(row["gamma"]))
            ax.plot([float(row["gamma"]) for row in series], [float(row["acc_percent"]) for row in series], marker="o", label=key)
        ax.set_xscale("log")
        ax.set_xlabel("gamma")
        ax.set_ylabel("SSC P1 ACC (%)")
        ax.set_title("Prespecified gamma grid, not an oracle selection")
        ax.legend(fontsize=7)
        _save(fig, "gamma_sensitivity.pdf")
    else:
        _empty("gamma_sensitivity.pdf", "No completed gamma-grid rows.")

    scatter = [
        row
        for row in primary
        if row["protocol"] in {"RANDOM_MEAN50", "KMEANSPP_BEST_INERTIA50"} and row.get("nmi_percent")
    ]
    if scatter:
        fig, ax = plt.subplots(figsize=(6, 6))
        for method, marker in (("SC", "o"), ("SSC", "s")):
            subset = [row for row in scatter if row["method"] == method]
            ax.scatter(
                [float(row["acc_percent"]) for row in subset],
                [float(row["nmi_percent"]) for row in subset],
                marker=marker,
                label=method,
            )
        ax.set_xlabel("ACC (%)")
        ax.set_ylabel("NMI (%)")
        ax.set_title("ACC and NMI from the same protocol cell")
        ax.legend()
        _save(fig, "acc_nmi_tradeoffs.pdf")
    else:
        _empty("acc_nmi_tradeoffs.pdf", "No completed primary cells.")
    return sorted(path.name for path in figures.glob("*.pdf"))


__all__ = ["make_figures"]
