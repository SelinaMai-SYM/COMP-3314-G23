"""Generate the overview table from fixed, qualified paired result records."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = [
    ("R3_E7_CAVITY", "E7 graph"),
    ("R3_E1_V3_CAVITY", "E1_v3 tube"),
    ("R3_E5_V2_CAVITY", "E5_v2 guard"),
]


def selected_rows(root=ROOT):
    with (Path(root) / "results/extension_round3/macro_differences.csv").open() as f:
        rows = list(csv.DictReader(f))
    selected = []
    for method, label in METHODS:
        controls = ["QSSC", method.removesuffix("_CAVITY") + "_PILOT"]
        pair = []
        for control in controls:
            found = [r for r in rows if r["candidate"] == method
                     and r["control"] == control and r["panel"] == "native"
                     and float(r["rho"]) == .1 and float(r["tau_multiplier"]) == 1.]
            if len(found) != 1:
                raise ValueError("Expected one fixed primary contrast: " + method + "/" + control)
            pair.append(found[0])
        if pair[0]["cohort_mask"] != pair[1]["cohort_mask"]:
            raise ValueError("Overview controls have different paired cohort masks")
        selected.append((label, *pair))
    return selected


def markdown(root=ROOT):
    lines = ["| Method | Qualified cohorts | ΔACC / ΔNMI vs QSSC | ΔACC / ΔNMI vs plain pilot |",
             "|---|---:|---:|---:|"]
    for label, qssc, pilot in selected_rows(root):
        def effect(row):
            return " / ".join(f"{float(row[m + '_available_case_delta']):+.3f}" for m in ["acc", "nmi"])
        lines.append(f"| {label} | {qssc['paired_n']}/8 | {effect(qssc)} | {effect(pilot)} |")
    return "\n".join(lines) + "\n"


def latex(root=ROOT):
    lines = [r"\begin{table}[ht]", r"\centering\small",
             r"\caption{Native-rounding primary changes in percentage points on retrospectively selected cohorts. Both metrics and both controls use the same qualified cohort mask. Full eight-cohort means are unavailable for the tube and guard.}",
             r"\label{tab:edge-deletion}", r"\begin{tabular}{lrrr}\toprule",
             r"Method & Pairs & vs QSSC & vs plain pilot\\\midrule"]
    for label, qssc, pilot in selected_rows(root):
        def effect(row):
            return " / ".join(f"{float(row[m + '_available_case_delta']):+.3f}" for m in ["acc", "nmi"])
        lines.append(label.replace("_", r"\_") + f" & {qssc['paired_n']}/8 & {effect(qssc)} & {effect(pilot)}" + r"\\")
    lines += [r"\bottomrule\end{tabular}", r"\end{table}"]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()
    text = markdown()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    if args.report_output:
        args.report_output.parent.mkdir(parents=True, exist_ok=True)
        args.report_output.write_text(latex())
    if args.update_readme:
        path = ROOT / "README.md"
        original = path.read_text()
        start, end = "<!-- BEGIN GENERATED RESULTS -->", "<!-- END GENERATED RESULTS -->"
        before, remainder = original.split(start, 1)
        _, after = remainder.split(end, 1)
        path.write_text(before + start + "\n\n" + text + "\n" + end + after)
    if not args.output and not args.update_readme:
        print(text, end="")


if __name__ == "__main__":
    main()
