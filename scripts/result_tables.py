"""Generate the overview table from fixed, qualified paired result records."""
from __future__ import annotations

import argparse
import csv
from math import isclose
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
    lines = ["| Method | Qualified cohorts | Native ΔACC / ΔNMI vs QSSC | Native ΔACC / ΔNMI vs plain pilot |",
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



def _records(root, relative):
    with (Path(root) / relative).open() as stream:
        return list(csv.DictReader(stream))


def _one(rows, **fields):
    found = [row for row in rows if all(row.get(k) == str(v) for k, v in fields.items())]
    if len(found) != 1:
        raise ValueError(f"Expected one evidence row for {fields}, found {len(found)}")
    return found[0]


def fixed_table(root=ROOT):
    rows = _records(root, "results/v3_reproduction/all_configurations.csv")
    lines = ["| Dataset | Fixed SC ACC / NMI (%) | Fixed SSC ACC / NMI (%) |",
             "|---|---:|---:|"]
    for dataset, label in [("ORL_att92", "ORL"), ("JAFFE", "JAFFE"),
                           ("YaleB_cropped2414", "YaleB cropped2414"), ("USPS", "USPS")]:
        pair = []
        for method in ["sc", "ssc"]:
            fields = dict(dataset_id=dataset, method=method, prep="Y0", initialization="RANDOM")
            if method == "ssc":
                fields.update(variant="E8", config_name="E8|gamma=1e+00")
            else:
                fields.update(config_name="k5_median_delta2")
            row = _one(rows, **fields)
            pair.append(" / ".join(f"{100*float(row['batch0_selected_' + m]):.2f}" for m in ["acc", "nmi"]))
        lines.append(f"| {label} | {pair[0]} | {pair[1]} |")
    return "\n".join(lines) + "\n"


def _reconstruction_rows(root=ROOT):
    rows = _records(root, "results/subset_search/closest_matches.csv")
    selected = []
    for dataset in ["AR", "JAFFE", "ORL", "UMIST", "BinAlpha", "MSRA50", "YaleB", "USPS"]:
        row = _one(rows, benchmark=dataset,
                   pool="adapted" if dataset == "MSRA50" else "specification_compatible",
                   endpoint="mean_sample_sd_50")
        if int(row["n"]) != 50:
            raise ValueError("Incomplete reconstruction endpoint: " + dataset)
        gap = max(abs(float(row[m + "_mean"]) - float(row["paper_" + m]))
                  for m in ["acc", "nmi"])
        if not isclose(gap, float(row["D_max"]), rel_tol=0, abs_tol=1e-12):
            raise ValueError("Reconstruction discrepancy mismatch: " + dataset)
        selected.append(row)
    return selected


def reproduction_table(root=ROOT):
    lines = ["| Dataset | Paper ACC (%) | Paper NMI (%) | Reproduced ACC (%) | Reproduced NMI (%) | D_max (pp) |",
             "|---|---:|---:|---:|---:|---:|"]
    for row in _reconstruction_rows(root):
        label = "MSRA50\\*" if row["benchmark"] == "MSRA50" else row["benchmark"]
        values = [float(row[k]) for k in ["paper_acc", "paper_nmi", "acc_mean", "nmi_mean"]]
        gap = max(abs(values[2] - values[0]), abs(values[3] - values[1]))
        lines.append("| " + label + " | " + " | ".join(f"{v:.2f}" for v in [*values, gap]) + " |")
    return "\n".join(lines) + "\n"


def historical_markdown(root=ROOT):
    lines = ["# Reconstruction tables", "",
             "Generated from retained records by `python -m scripts.result_tables`. "
             "ACC/NMI are percentages; changes are percentage points.", "",
             "## Fixed diagnostic (presentation 4.2)", "",
             "E8 gamma=1, Y0, RANDOM, one minimum-SSE assignment from 50 starts "
             "in batch 0. A selected assignment has no across-start SD.", "", fixed_table(root),
             "## Joint mean matches (presentation 4.4)", "",
             "Complete 50-start configurations selected retrospectively within declared pools. "
             "Both metrics and sample SD belong to the same configuration. "
             "MSRA uses the adapted native-16 source. Historical membership remains unverified.", "",
             "| Dataset | Candidate | ACC ± SD (%) | NMI ± SD (%) | Equation / gamma / initializer | Solver |",
             "|---|---|---:|---:|---|---|"]
    for row in _reconstruction_rows(root):
        dataset = row["benchmark"]
        means = [f"{float(row[m+'_mean']):.2f} ± {float(row[m+'_sd']):.2f}" for m in ['acc','nmi']]
        lines.append(f"| {dataset} | {row['candidate_id']} | {means[0]} | {means[1]} | "
                     f"{row['variant']} / {float(row['gamma_nominal']):g} / {row['initialization']} | {row['solver_status']} |")
    lines += ["", "No selected historical output has an optimality-gap certificate. "
              "These finite IRLS fits are distinct from the separately fitted extension SSC references.", "",
              "## Initialization sensitivity (presentation 5.3)", "",
              "Original v3_reproduction fixed-configuration means over 50 seeds; "
              "later subset-search coordinates are not substituted.", "",
              "| Dataset | Method | RANDOM ACC (%) | Greedy++ ACC (%) | Change (pp) |",
              "|---|---|---:|---:|---:|"]
    rows = _records(root, "results/v3_reproduction/all_configurations.csv")
    for dataset, label in [("ORL_att92", "ORL"), ("JAFFE", "JAFFE")]:
        for method in ["sc", "ssc"]:
            fields=dict(dataset_id=dataset, method=method, prep="Y0",
                        config_name="E8|gamma=1e+00" if method=="ssc" else "k5_median_delta2")
            if method=="ssc":fields['variant']="E8"
            a,b=[100*float(_one(rows, **fields, initialization=i)['per_run_acc_mean'])
                 for i in ["RANDOM", "SKLEARN_GREEDY_KMEANSPP"]]
            lines.append(f"| {label} | {method.upper()} | {a:.3f} | {b:.3f} | {b-a:+.3f} |")

    lines += ["", "## Baseline diagnostic (presentation 4.3)", "",
              "Each cell is paper ACC/NMI → measured ACC/NMI (%). "
              "PCA uses d=40; SPLS uses d=50 and alpha=0.5. Fixed-objective rows "
              "use batch-0 native minimum-objective selection; LDA rows use the "
              "specified 50-run means. LDA→SC is the ridge adaptation, not recovered historical LDA-SC.", "",
              "| Baseline | ORL | JAFFE | YaleB cropped2414 | USPS |",
              "|---|---:|---:|---:|---:|"]
    import yaml
    paper = yaml.safe_load((Path(root)/'configs/v3/paper_reference.yaml').read_text())
    expanded = _records(root, 'results/submission_refresh/expanded_baseline_selection.csv')
    methods = [('kmeans','K-means','raw','RANDOM'), ('sc','SC','k5_median_delta2','RANDOM'),
               ('pca_kmeans','PCA→K-means','d40','RANDOM'), ('pca_sc','PCA→SC','d40','RANDOM'),
               ('lda_kmeans','LDA-Kmeans (mean)','k-1','FULL_REFIT'),
               ('lda_adapted_sc','Ridge LDA→SC (mean)',None,None),
               ('llc','LLC','ridge=1|mult=1','YU_SHI'), ('spls','SPLS','alpha=0.50|d=50','RANDOM')]
    for method,label,config,init in methods:
        cells=[]
        for dataset,display,K in [('ORL_att92','ORL',40),('JAFFE','JAFFE',10),('YaleB_cropped2414','YaleB',38),('USPS','USPS',10)]:
            paper_method={'pca_sc':'pca_spectral','lda_adapted_sc':'lda_spectral'}.get(method,method)
            original=[paper[m][paper_method][display]['mean'] for m in ['acc','nmi']]
            if method=='lda_adapted_sc':
                row=_one(expanded,dataset=dataset,method=method,endpoint='mean_sample_sd_50')
                measured=[float(row[m+'_mean']) for m in ['acc','nmi']]
            else:
                fields=dict(dataset_id=dataset,prep='Y0',method=method,initialization=init,
                            config_name=f'k-1={K-1}' if method=='lda_kmeans' else config)
                row=_one(rows,**fields)
                prefix='per_run_' if method=='lda_kmeans' else 'batch0_selected_'
                measured=[100*float(row[prefix+m+('_mean' if method=='lda_kmeans' else '')]) for m in ['acc','nmi']]
            cells.append('/'.join(f'{v:.2f}' for v in original)+' → '+'/'.join(f'{v:.2f}' for v in measured))
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    return "\n".join(lines) + "\n"


def development_markdown(root=ROOT):
    import json
    first = _one(_records(root, 'results/extension_verification/macro_summary.csv'),
                 method='E1', panel='angular', comparison='matched SSC')
    gates = json.loads((Path(root)/'results/extension_verification/diagnostics/gates.json').read_text())
    yale = gates['E2']['development_outcomes']['YaleB']
    later = _records(root, 'results/extension_round2/macro_summary.csv')
    lines = ['# Development evidence (presentation 6.1)', '',
             'These are distinct development comparisons with different objectives, inputs and qualified masks. '
             'They do not form a ranking. ACC/NMI differences are percentage points.', '',
             '| Method | Comparator / scope | Qualified cohorts | ΔACC / ΔNMI | Finding |',
             '|---|---|---:|---:|---|',
             f"| E1 | Matched unsquared SSC, angular panel | {first['qualified_datasets']}/8 | "
             f"{float(first['ACC_delta_pp']):+.3f} / {float(first['NMI_delta_pp']):+.3f} | Nearly unchanged |",
             f"| E2 development gate | Radial-neutralized ordinary SSC minus its selected ordinary SSC output, YaleB | Development only | "
             f"{yale['ACC']['delta_pp']:+.3f} / {yale['NMI']['delta_pp']:+.3f} | Neither development dataset passed; formal campaign not run |"]
    correct=[gates['E3']['development_outcomes'][name]['correct_fraction'] for name in ['ORL','YaleB']]
    lines.append(f"| E3 semantic gate | Two-view triplet audit on ORL / YaleB | Development only | Unavailable | "
                 f"Correct relations {100*correct[0]:.1f}% / {100*correct[1]:.1f}%; neither passed the 60% gate; formal campaign not run |")
    for method, note in [('E4','Partial-cohort loss'),('E5','Partial-cohort gain'),('E6','Singular-floor guard inactive at the reported primary point')]:
        r=_one(later, method=method, comparison='fresh movement-matched QSSC')
        lines.append(f"| {method} | Fresh movement-matched QSSC | {r['qualified_denominator']}/8 | "
                     f"{float(r['available_case_ACC_pp']):+.3f} / {float(r['available_case_NMI_pp']):+.3f} | {note} |")
    _,q,_=selected_rows(root)[0]
    lines.append(f"| E7 | QSSC, selected native panel | {q['paired_n']}/8 | "
                 f"{float(q['acc_available_case_delta']):+.3f} / {float(q['nmi_available_case_delta']):+.3f} | Complete small mixed effect |")
    lines += ['', 'E1 → E1_v2 → E1_v3 and E5 → E5_v2 identify changes in formulation, not repeated estimates of one method. '
              'The selected E1_v3/E5_v2 comparisons use the separate edge-deletion protocol.', '',
              'Sources: [unsquared macro records](../results/extension_verification/macro_summary.csv), '
              '[development gates](../results/extension_verification/diagnostics/gates.json), '
              '[quadratic macro records](../results/extension_round2/macro_summary.csv), and '
              '[selected macro records](../results/extension_round3/macro_differences.csv). '
              'Each release retains per-seed measurements and qualification alongside these summaries.']
    return '\n'.join(lines)+'\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report-output", type=Path)
    parser.add_argument("--historical-output", type=Path)
    parser.add_argument("--development-output", type=Path)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()
    text = markdown()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    if args.report_output:
        args.report_output.parent.mkdir(parents=True, exist_ok=True)
        args.report_output.write_text(latex())
    for path, content in [(args.historical_output, historical_markdown), (args.development_output, development_markdown)]:
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content())
    if args.update_readme:
        path = ROOT / "README.md"
        original = path.read_text()
        start, end = "<!-- BEGIN GENERATED RESULTS -->", "<!-- END GENERATED RESULTS -->"
        before, remainder = original.split(start, 1)
        _, after = remainder.split(end, 1)
        updated = before + start + "\n\n" + text + "\n" + end + after
        start, end = "<!-- BEGIN GENERATED REPRODUCTION -->", "<!-- END GENERATED REPRODUCTION -->"
        before, remainder = updated.split(start, 1)
        _, after = remainder.split(end, 1)
        path.write_text(before + start + "\n\n" + reproduction_table() + "\n" + end + after)
    if not args.output and not args.update_readme:
        print(text, end="")


if __name__ == "__main__":
    main()
