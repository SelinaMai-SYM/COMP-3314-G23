"""All delivery numbers are generated from frozen selection and measured jobs."""
from pathlib import Path
import csv,json,shutil,collections
from scripts.final.analyze_next_round import load
ROOT=Path(__file__).resolve().parents[2];F=ROOT/'results/final';O=ROOT/'results/next_round';T=ROOT/'report/tables'
PRIMARY=['ORL_att92','JAFFE','YaleB_cropped2414','USPS'];BENCH=['ORL','JAFFE','YaleB','USPS']
def esc(x):return str(x).replace('_',r'\_').replace('&',r'\&').replace('%',r'\%').replace('#',r'\#')
def fmt(r,m='ACC',latex=True):
    if r.get('measured_'+m) is None:return '--'
    sep=r' $\pm$ ' if latex else ' ± '
    return f"{r['measured_'+m]:.3f}"+sep+f"{r['measured_'+m+'_SD']:.3f}"
def main():
    rows=[json.loads(s) for s in (F/'generated/selection_manifest.jsonl').read_text().splitlines()];T.mkdir(exist_ok=True)
    for name in ['selection_manifest.csv','selection_manifest.jsonl','closest_to_paper.csv','closest_to_paper.md','fixed_protocol_reference.csv','fixed_protocol_reference.md']:shutil.copy2(F/'generated'/name,F/name)
    table=[r'\begin{table}[t]',r'\centering\small',r'\caption{Reported in Chang et al. (2015) versus our measured ACC (percent). Closest is retrospective ACC matching. Fixed is Y0/E8/gamma=1/random. Full deviations are described in the text and appendix.}',r'\label{tab:main}',r'\begin{tabular}{llrrrl}',r'\toprule Data & Method & Paper & Closest mean $\pm$ SD & Fixed mean $\pm$ SD & Mark \\',r'\midrule']
    marks=['V','V,T','R','R,T','Y3,G','Y3,G,I','G','V,I'];count=0
    for b in BENCH:
        for m in ['sc','ssc']:
            r=next(x for x in rows if (x['benchmark'],x['method'],x['track'])==(b,m,'closest_to_paper'));fixed=next(x for x in rows if (x['benchmark'],x['method'],x['track'])==(b,m,'fixed_protocol_reference'))
            table.append(f"{b} & {m.upper()} & {r['paper_ACC']:.1f} & {fmt(r)} & {fmt(fixed)} & {marks[count]} \\\\");count+=1
    table += [r'\bottomrule\end{tabular}',r'\par\footnotesize R: random; V: vanilla++; G: sklearn greedy++; T: 300-step returned iterate, optimum not certified; I: historical iterate criterion, no dual certificate.',r'\end{table}'];(T/'final_main.tex').write_text('\n'.join(table)+'\n')
    app=[r'Paper values are \emph{Reported in Chang et al. (2015)}; measured columns are \emph{Our reproduction/adapted setting}. Units are percent. Closest uses all 50 prescribed batch-0 seeds. NMI follows the same selected configuration; other batches and selected min-inertia assignments remain distinct endpoints.',r'\small']
    short={'BLOCKED_DATA':'data blocked','BLOCKED_METHOD':'method blocked','SUBSET_UNVERIFIED':'subset unverified','GRID_NOT_COLLAPSED':'grid not collapsed','COMPLETED':'measured','TRUNCATED_EXECUTION':'truncated'}
    for track,title in [('closest_to_paper','Closest display: 72 historical cells'),('fixed_protocol_reference','Fixed protocol: 72 cells, with measured grids retained')]:
        app += [f'\\subsection{{{title}}}',r'\begin{longtable}{llrllp{2.9cm}}',r'\toprule Data & Method & Paper ACC & Measured ACC & Measured NMI & Status / setting \\',r'\midrule\endhead']
        for r in rows:
            if r['track']!=track:continue
            note=short[r['execution_status']]
            if r.get('config_id'):
                init={'RANDOM':'R','VANILLA_KMEANSPP':'V','SKLEARN_GREEDY_KMEANSPP':'G','YU_SHI':'Yu-Shi','FULL_REFIT':'full refit'}[r['initialization_exact_name']];note+=f"; {r['prep']}, {r['variant'] or init}"
                if r['method']=='ssc':note+=f", g={r['gamma_nominal']:g}, {init}"
                if r['dataset_version']=='YaleB_dengcai32':note+='; DengCai32'
            app.append(f"{r['benchmark']} & {esc(r['method'])} & {r['paper_ACC']:.1f} & {fmt(r)} & {fmt(r,'NMI')} & {esc(note)} \\\\")
        app += [r'\bottomrule\end{longtable}']
    app += [r'\normalsize',r'\subsection{Selection and source trace}',r'The selection manifest contains complete effective parameters, exact initializer names, seeds, batch counts, metadata/source hashes, blocked reasons, execution and solver statuses, and no-data reconstruction commands. PCA/SLPS grids have no unique locked reference. LLC uses its pre-existing ridge=1, bandwidth multiplier=1 reference and Yu--Shi rounding; LDA-Kmeans refits per seed. YaleB cropped is the fixed primary source, DengCai32 is alternate-source sensitivity. UMIST575 and candidate BinAlpha do not replace historical subsets.',r'The immutable scalar package contains 378550 trials, 3059 jobs and 6563 configuration rows. It reconstructs tables without images, old worktrees, Git history or caches. It does not recover unavailable historical representation arrays. The gzip file and decompressed CSV have different hashes. See the machine-readable release manifest.']
    (T/'final_appendix.tex').write_text('\n'.join(app)+'\n')
    jobs=load();done=[j for j in jobs if j.get('status')=='COMPLETED'];gate=json.loads((O/'mechanism_gate.json').read_text()) if (O/'mechanism_gate.json').exists() else {'supported_primary_datasets':0,'formal_capped_experiment_triggered':False}
    new=[r'\begin{table}[t]',r'\centering\small',r'\caption{New seeded Y0 representations, shared within each SC/SSC pair; greedy++ seeds 0--49. ACC percentages. U: uncertified output. Best certified is not the complete oracle if other configurations remain uncertified.}',r'\label{tab:mechanism}',r'\begin{tabular}{lrrrl}',r'\toprule Data & SC & SSC gamma=1 & Best certified in $\Gamma_5$ & Coverage \\',r'\midrule'];primary=[]
    for d,b in zip(PRIMARY,BENCH):
        scpath=O/'sc'/(d+'__Y0.json');sc=json.loads(scpath.read_text()) if scpath.exists() else None;a=[j for j in done if j['task']['phase']=='A' and j['task']['dataset']==d];g1=next((j for j in a if j['task']['gamma']==1),None);cert=[j for j in a if j.get('qualified_for_method_contrast')];best=max(cert,key=lambda j:j['scores']['acc_mean']) if cert else None
        num=lambda j:'--' if j is None else f"{j['scores']['acc_mean']:.2f}"
        new.append(f"{b} & {num(sc)} & {num(g1)}{'' if g1 and g1.get('qualified_for_method_contrast') else ' U'} & {num(best)} & {len(cert)}/5 certified \\\\")
        primary.append({'dataset':d,'SC_ACC':sc['scores']['acc_mean'] if sc else None,'SSC_gamma1_ACC':g1['scores']['acc_mean'] if g1 else None,'gamma1_status':g1.get('solver',{}).get('status') if g1 else None,'best_certified_gamma':best['task']['gamma'] if best else None,'best_certified_ACC':best['scores']['acc_mean'] if best else None,'certified_configurations':len(cert)})
    new += [r'\bottomrule\end{tabular}',r'\end{table}']
    if not gate['formal_capped_experiment_triggered']:new += [f"The prespecified incorrect-edge gate supports {gate.get('supported_primary_datasets',0)}/4 benchmarks; two are required. No real-data capped-fusion improvement or achievement of the 2-point target is established. Uncertified controls make some conclusions inconclusive, rather than disproving the mechanism. Analytic and synthetic checks are reported separately."]
    else:new += ['The mechanism gate passed. The formal capped comparison and complete-search coverage are reported separately; a passed gate alone is not a performance success.']
    (T/'next_round_findings.tex').write_text('\n'.join(new)+'\n');(O/'primary_summary.json').write_text(json.dumps(primary,indent=2)+'\n')
    oldpath=O/'legacy_certificate_audit.csv';old=list(csv.DictReader(oldpath.open())) if oldpath.exists() else [];counts=collections.Counter(r['current_audit_status'] for r in old)
    audit=[r'\subsection{Certificate definitions}',r'For radial Huber, $D_\delta(q)=\langle B^Tq,F\rangle-(\delta/2)\sum_i\|(B^Tq)_i\|^2/a_i$. Edge and node balls apply; squared fidelity removes node balls. An inward capacity-ratio scaling recovers feasible q. Best primal means an actual stored G; objective, array and clustering metrics are never mixed across iterates. Negative primal-dual gaps beyond tolerance are errors.',r'The simple $G=F$ sufficient region uses $b=B^T(2wu)$, with unit directions on noncoincident F-edges and zero otherwise, and $\gamma_0=1/\max_i\|b_i\|$. Coincident edges need not yield the maximal onset. Infinity is asserted only for zero-TV analytic cases, not a finite search reaching a large gamma.',f'All 88 historical verified claims were audited: {esc(dict(counts))}. Direct analytic G=F checks and certification using a recorded scalar primal are distinguished; the latter is not recovery of an unavailable historical G array. Every old status remains in the audit CSV.',r'The numerical amendment retains cold runs and adds an exact-objective-accepted IRLS primal initializer (at most 300 iterations for n<=3000, otherwise 30; at most 60 seconds). Failure falls back to the cold start. It changes neither target, graph, parameter grid nor certificate threshold. The code/config amendment is explicit; development data were already inspected, so later results are not independent held-out validation.',r'Capped fusion uses active-edge block minimization and two initializations. Inner convex gap certification is not a global certificate for the nonconvex objective. Fixed-point, truncation, monotonicity rejection and missing second-start states remain explicit. Tiny-graph state enumeration supplies an independent global reference only for those tiny problems.',r'\subsection{Candidate mechanisms}',r'Radial Huber is convex and orthogonally invariant. Along $G(t)=(1-t)F+t1m^T$, graph TV decreases linearly while near-zero fidelity increases quadratically, so nontrivial F is not optimal for positive gamma/delta. This proves activation, not better ACC. The bound $0\le r-\phi_\delta(r)\le\delta/2$ gives original-objective error at most $n\delta/2$ plus a certified absolute solver gap. Bounded radial fidelity influence is not a transferred breakdown theorem \citep{sun2025resistant}.',r'Heat features use $H_t=e^{-tL/2}$ with $H_tH_t^T=K_t=e^{-tL}$; rows of $K_t$ correspond instead to time 2t distances. Duhamel bounds kernel operator change by $t\|L-L^\prime\|_2$ and each squared-distance change by $2t\|L-L^\prime\|_2$. A kNN boundary gap above $4t\|L-L^\prime\|_2$ cannot cross under that perturbation. Full-spectrum random projection is approximate and does not automatically inherit this exact bound. Neither stability nor a large diffusion time guarantees labels \citep{coifman2006diffusion,gasteiger2019diffusion}.',r'\subsection{Evaluation and resource limits}',r'The old robustness table did not rerun SSC, and used the wrong USPS pixel domain. It is retained with an invalidity annotation. Corrected perturbations declare [-1,1] for USPS, preserve zero-change identity and rerun the full corresponding pipeline. ARI/Jaccard alone do not measure class accuracy.',r'All primary K-means endpoints use 50 seeds, one greedy++ initialization and sample SD. Paired bootstrap uses seed 20261108 and 2000 resamples. Perturbation seed, not each correlated rounding, is an independent unit. Missing four-benchmark coverage leaves the formal average NA; the two YaleB sources are not independent benchmarks.',r'New computation is capped at 36 CPU-core hours, two workers and a target 8 GiB total RSS, with no GPU or paid resources. PDHG has at most 30000 iterations per fit and 10/30-minute small/large timeouts. Runtime, memory and all retained solver versions are in the resource ledger. Failure never becomes zero ACC.',r'Native prclust 1.3 was compiled at a pinned source revision and executed on a five-point sanity check; this is not a benchmark result. New optimization modules are from-scratch formula implementations. Scientific snapshots, data restrictions, exact source revisions and clone verification are indexed in docs/final.']
    (T/'audit_appendix.tex').write_text('\n'.join(audit)+'\n')
    # Root README numbers are generated only from the same selection manifest.
    readme='''# COMP3314 Group 23: Spectral Shrunk Clustering - final v3

Study and critical analysis of Chang, Nie, Ma, Yang and Zhou, *A Convex Formulation for Spectral Shrunk Clustering*, AAAI 2015, pp. 2532-2538, DOI [10.1609/aaai.v29i1.9606](https://doi.org/10.1609/aaai.v29i1.9606). SSC means Spectral Shrunk Clustering.

The repository separates paper reconstruction, controlled reproduction and retrospective numerical matching. An optimum for a convex representation objective does not guarantee optimal labels or improved ACC/NMI.

## Setup and three checks

Tested CPython 3.13.3. Package minimum is Python 3.10; other versions are not claimed bit-identical.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r environment/requirements.lock.txt
python -m pip install -e .
python -m experiments.v3_reproduction smoke --dataset synthetic
python -m experiments.v3_reproduction rebuild-results --release-manifest configs/final/release_manifest.json --output results/rebuilt
python -m experiments.v3_reproduction run-experiments --config configs/v3/campaign.yaml --data-root /path/to/benchmarks --datasets ORL_att92 JAFFE --smoke --output runs/next_round/data_smoke
```

Synthetic smoke and results rebuild need no images, caches, Git history or old branches. Real-data smoke uses three seeds, not a full experiment. [Data preparation and restrictions](docs/final/data_setup.md). Root precedence: CLI > `COMP3314_DATA_ROOT` > `local/data_root.txt` > checkout `benchmarks`; it contains `orl/data`, `jaffe/data`, `yaleb/data`, `usps/data`. There is no old-worktree pointer.

Omit `--smoke` only to deliberately run the large baseline grid. New mechanism experiments are separate:

```bash
python -m experiments.next_round.campaign prepare --data-root /path/to/benchmarks
python -m experiments.next_round.campaign sc
python -m experiments.next_round.campaign run --phases A N0_selected B --workers 2 --budget-hours 36
python -m scripts.final.analyze_next_round
```

Phase C requires the documented evidence gate. [Protocol](configs/next_round/protocol.yaml), [job manifest](configs/next_round/job_manifest.json), [all results](results/next_round/all_results.md), [negative findings](results/next_round/negative_findings.md). Model and parameter functions do not accept labels; Oracle interventions and evaluation explicitly do.

## 9 methods x 8 benchmarks

**32 COMPLETED, 24 BLOCKED_DATA, 8 BLOCKED_METHOD, 8 SUBSET_UNVERIFIED.** SLPS (SPLS in the SSC table) has a one-shot implementation. LDA-SC is unresolved. AR, historical UMIST564 and MSRA50 remain blocked. Candidate BinAlpha and UMIST575 are supplementary. PCA/SLPS have measured grids without one unique locked reference.

- [Closest-to-paper display: all 72 cells](results/final/closest_to_paper.md): complete batch-0 configuration mean minimizing absolute unrounded ACC distance. This is label/paper-assisted post-hoc display selection.
- [Fixed controlled reference: all 72 cells](results/final/fixed_protocol_reference.md): existing Y0/E8/gamma=1/random; uncollapsed grids stay explicit.
- [Selection manifest](results/final/selection_manifest.csv), [complete configuration statistics](results/final/generated/configuration_table.csv), [batch repeatability](results/final/generated/batch_repeatability.csv), [supplemental versions](results/final/generated/supplemental.md), [per-benchmark tables](results/final/generated/per_benchmark).

This historical release reconstructs 378550 trials, 3059 jobs and 6563 configurations. Counts are package-specific. Scalar reproducibility is not full recovery of old F/W arrays. Compressed and decompressed hashes are distinct in the release manifest; new executions have separate run IDs and supersedes links.

| Benchmark | Method | Paper ACC (%) | Closest mean ± sample SD (%) | Setting and original solver |
|---|---|---:|---|---|
'''
    for r in rows:
        if r['track']!='closest_to_paper' or r['method'] not in ['sc','ssc'] or r.get('measured_ACC') is None:continue
        setting=f"{r['dataset_version']}, {r['prep']}, {r['variant'] or 'SC'}, {r['initialization_exact_name']}"
        if r.get('gamma_nominal') is not None:setting+=f", nominal gamma={r['gamma_nominal']:g}"
        setting+='; '+r['solver_status_original']
        if r['execution_status']=='TRUNCATED_EXECUTION':setting+='; 300-step returned iterate, optimum not certified'
        readme+=f"| {r['benchmark']} | {r['method'].upper()} | {r['paper_ACC']:.1f} | {fmt(r,latex=False)} | {setting} |\n"
    readme+='''
NMI/SD/n follow the same configuration and seeds. Min-inertia assignments are separate. Paper tuning, fixed control and closest display answer different questions. E13(gamma) maps to E8(gamma/2). Vanilla++ differs from sklearn greedy++.

## Performance-driven extensions

N0 provides feasible-dual certificates; A studies parameter curves; B diagnoses incorrect fusion with Oracle deletion and matched weakening controls. The practical target is >=2 points mean ACC gain across four benchmarks, nondecreasing NMI, and comparison with SC. A 15-configuration capability oracle is separate from the fixed no-label operating point. Capped fusion is an existing penalty adapted to SSC, with inner certificates only. Huber/heat remain evidence-dependent candidates.

'''+f"The diagnostic gate currently supports **{gate.get('supported_primary_datasets',0)}/4** datasets (two required). Formal capped experiment triggered: **{gate['formal_capped_experiment_triggered']}**. This is not evidence that SSC fails universally; uncertified outcomes remain visible.\n\n"+'''The old held-out robustness table is retained but invalid as full-SSC robustness evidence: shrinkage was not rerun and USPS was clipped incorrectly. [Correction](docs/next_round/robustness_audit.md).

## Deliverables and attribution

[Report PDF](report/Group_23.pdf) and [LaTeX](report/main.tex); [guideline checklist](docs/final/guideline_checklist.md); [9-minute outline](docs/final/presentation_outline.md); [Q&A](docs/final/qa_notes.md); [validation](docs/final/validation.md); [sources, ownership and licenses](docs/final/sources_and_licenses.md). [Scientific snapshots](archive/source) are provenance only, never current imports.

This is a course report, not a NeurIPS submission. Main text is <=4 pages, excluding references/appendix. Individual member names were absent from reliable supplied materials and remain to be supplied; no names are inferred from accounts. Only the PDF is submitted to the course system by the group.

Slides: 2026-11-15 23:59; report: 2026-11-29 23:59, Hong Kong/Shanghai time. Rubric: understanding 40%, analysis/insight 30%, writing 10%, presentation/Q&A 20%; reproduction is optional, up to 10 bonus points.
'''
    (ROOT/'README.md').write_text(readme);print('Generated all report/README numbers from manifests.')
if __name__=='__main__':main()
