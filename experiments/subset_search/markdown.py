"""Pure benchmark views shared by aggregation and the scalar-only rebuild."""
from __future__ import annotations
import json
from pathlib import Path


def _value(row, key, default='UNAVAILABLE'):
    value = row.get(key)
    return default if value is None or value == '' else value


def _cell(value):
    if isinstance(value, str) and value[:1] in ['[', '{']:
        try: value = json.loads(value)
        except ValueError: pass
    if isinstance(value, (list, dict)):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value).replace('\\', '\\\\').replace('|', '\\|').replace('\r', ' ').replace('\n', ' ')


def _number(value, signed=False):
    return 'NA' if value in [None, ''] else format(float(value), '+.3f' if signed else '.3f')


def _metric(row, name, paper=False):
    mean = row.get('paper_' + name if paper else name + '_mean')
    sd = row.get('paper_' + name + '_sd' if paper else name + '_sd')
    if mean in [None, '']: return 'NA'
    if not paper and row.get('endpoint') == 'native_best_of_50':
        return _number(mean) + ' (single assignment; SD NA)'
    return _number(mean) + ' +/- ' + _number(sd)


def _public_mode():
    manifest=Path(__file__).resolve().parents[2]/'configs/submission_refresh/evidence_manifest.json'
    return manifest.exists() and json.loads(manifest.read_text()).get('schema') in {
        'submission-scalar-evidence-public-v1','submission-scalar-evidence-public-v2'}


def _public_benchmark(benchmark,winners,paper,certified_status):
    selected=[row for row in winners if row['benchmark']==benchmark]
    keys={(row['pool'],row['endpoint']):row for row in selected}
    if len(keys)!=len(selected):raise ValueError('duplicate benchmark winner pool/endpoint')
    text=[f'# {benchmark}: SSC source and subset sensitivity','',
        'Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical membership. ACC/NMI and sample SD are percentages; differences and joint discrepancies are percentage points. Both metrics use one configuration and seed set. Native best-of-50 is one minimum-inertia assignment and has no across-run SD. Diagnostic parents do not compete in either eligible pool.','',
        '| Pool / endpoint | Source and settings | Paper ACC / NMI (mean ± SD) | Our ACC / NMI | Δ mean ACC / NMI; Δ SD (pp) | Dmax / Dmean (pp) | Scientific qualification |',
        '|---|---|---:|---:|---:|---:|---|']
    for pool in ['specification_compatible','adapted']:
        for endpoint in ['mean_sample_sd_50','native_best_of_50']:
            row=keys.pop((pool,endpoint),None)
            label=('Compatible' if pool=='specification_compatible' else 'Adapted')+' / '+('mean ± sample SD (50 seeds)' if endpoint=='mean_sample_sd_50' else 'native best of 50')
            if row is None:
                reference={f'paper_{m}':paper.get(m,{}).get('ssc',{}).get(benchmark,{}).get('mean') for m in ['acc','nmi']}
                reference.update({f'paper_{m}_sd':paper.get(m,{}).get('ssc',{}).get(benchmark,{}).get('sd') for m in ['acc','nmi']})
                values=[label,'Unavailable',' / '.join(_metric(reference,m,True).replace('+/-','±') for m in ['acc','nmi']),'NA / NA','NA / NA; NA / NA','NA / NA','No complete eligible configuration']
            else:
                source=[str(_value(row,'source_version','Source not identified'))]
                for key,title in [('n_samples','n'),('n_classes','classes'),('n_features','features'),('native_resolution','native resolution'),
                                  ('family','membership family'),('prep','normalization'),('variant','target'),
                                  ('gamma_nominal','gamma'),('gamma_effective','effective gamma'),('initialization','initialization')]:
                    if row.get(key) not in [None,'']:source.append(title+' '+str(row[key]))
                delta=' / '.join(_number(row.get('delta_'+m+'_pp'),True) for m in ['acc','nmi'])
                sd_delta='NA / NA' if endpoint=='native_best_of_50' else ' / '.join(_number(row.get('delta_'+m+'_sd_pp'),True) for m in ['acc','nmi'])
                qualifications=['Historical identity '+str(_value(row,'historical_identity','unverified')).replace('_',' ').lower(),
                                'Solver '+str(_value(row,'solver_status')).replace('_',' ').lower()]
                if pool=='adapted':qualifications.append('Source, resolution or method adaptation')
                if row.get('configuration_source_kind'):qualifications.append('Source kind '+str(row['configuration_source_kind']).replace('_',' ').lower())
                qualifications.append('Finite historical-style IRLS; no transferred numerical-audit certificate')
                values=[label,'; '.join(source),' / '.join(_metric(row,m,True).replace('+/-','±') for m in ['acc','nmi']),
                        ' / '.join(_metric(row,m).replace('+/-','±') for m in ['acc','nmi']),delta+'; '+sd_delta,
                        ' / '.join(_number(row.get(m)) for m in ['D_max','D_mean']),'; '.join(qualifications)]
            text.append('| '+' | '.join(map(_cell,values))+' |')
    if keys:raise ValueError('unexpected eligible pool/endpoint in benchmark winners')
    text+=['','All settings use k=5 and one-start Lloyd rounding with seeds 0–49. Historical-style IRLS uses at most 300 updates, tolerance 1e-6 and epsilon 1e-8. Exact sample/configuration identities and hashes are in `closest_matches.csv` and the public registry; unsuccessful and unevaluated settings remain in coverage.','',
           '## Certified-search qualification','',
           'Comparable certified subset-search coverage is unavailable, so no certified closest winner is selected. The numerical USPS continuation is a separate saved output; its certificate does not certify a finite-iteration IRLS output, including when current F/W references match.']
    statuses=[r for r in (certified_status or []) if r['benchmark']==benchmark]
    if statuses:
        text+=['','| Pool / endpoint | Historical complete configurations / canonical | Unique inputs | Certified closest |','|---|---:|---:|---|']
        for row in statuses:
            values=[row['pool'].replace('_',' ')+' / '+row['endpoint'].replace('_',' '),str(row['historical_complete_configurations'])+' / '+str(row['historical_complete_canonical_configurations']),row['historical_complete_unique_inputs'],'Unavailable']
            text.append('| '+' | '.join(map(_cell,values))+' |')
    text+=['','Machine-readable qualifications are in `certified_search_status.csv`; separate same-input numerical references and solver tables are in `../submission_refresh/`.','']
    return '\n'.join(text)


def benchmark_markdown(benchmark, winners, paper, certified_status=None,*,public=None):
    """Render all four pool/endpoint slots without data or artifact access."""
    if public is None:public=_public_mode()
    if public:return _public_benchmark(benchmark,winners,paper,certified_status)
    selected = [row for row in winners if row['benchmark'] == benchmark]
    keys = {(row['pool'], row['endpoint']): row for row in selected}
    if len(keys) != len(selected): raise ValueError('duplicate benchmark winner pool/endpoint')
    text = [f'# {benchmark}: closest evaluated SSC reconstructions', '',
        'Joint ACC/NMI matching is retrospective and uses labels and paper targets. A count-compatible candidate does not establish historical sample identity. Scores and sample SDs are percentages; signed differences and joint distances are percentage points. Both metrics and their SDs use the same configuration and seeds. Native best-of-50 selects one minimum-inertia assignment from the same 50 starts: its statistic n is 1 and it has no across-run SD. Diagnostic parents cannot compete in either eligible pool.', '',
        '| Pool / endpoint | Candidate | Paper ACC +/- SD | Our ACC +/- SD | Paper NMI +/- SD | Our NMI +/- SD | Delta ACC / NMI (pp) | Delta SD ACC / NMI (pp) | Dmax / Dmean (pp) | Samples / classes / statistic n |',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    shown = []
    for pool in ['specification_compatible', 'adapted']:
        for endpoint in ['mean_sample_sd_50', 'native_best_of_50']:
            row = keys.pop((pool, endpoint), None)
            if row is None:
                reference = {f'paper_{name}': paper.get(name, {}).get('ssc', {}).get(benchmark, {}).get('mean') for name in ['acc', 'nmi']}
                reference.update({f'paper_{name}_sd': paper.get(name, {}).get('ssc', {}).get(benchmark, {}).get('sd') for name in ['acc', 'nmi']})
                values = [pool + ' / ' + endpoint, 'UNAVAILABLE: no complete eligible configuration', _metric(reference, 'acc', True), 'NA', _metric(reference, 'nmi', True), 'NA', 'NA / NA', 'NA / NA', 'NA / NA', 'NA / NA / NA']
            else:
                shown.append(row)
                sd_delta = 'NA / NA' if endpoint == 'native_best_of_50' else ' / '.join(_number(row.get('delta_' + m + '_sd_pp'), True) for m in ['acc', 'nmi'])
                values = [pool + ' / ' + endpoint, row['candidate_id'], _metric(row, 'acc', True), _metric(row, 'acc'), _metric(row, 'nmi', True), _metric(row, 'nmi'),
                    ' / '.join(_number(row.get('delta_' + m + '_pp'), True) for m in ['acc', 'nmi']), sd_delta,
                    ' / '.join(_number(row.get(m)) for m in ['D_max', 'D_mean']),
                    ' / '.join(str(_value(row, key)) for key in ['n_samples', 'n_classes', 'n'])]
            text.append('| ' + ' | '.join(map(_cell, values)) + ' |')
    if keys: raise ValueError('unexpected eligible pool/endpoint in benchmark winners')
    text += ['', '| Pool / endpoint | Source and membership | Settings and deviations | Solver / execution | Identity and provenance |', '|---|---|---|---|---|']
    for row in shown:
        source = '; '.join(key + '=' + _cell(_value(row, key)) for key in ['source_version', 'parent_id', 'original_parent_id', 'source_url', 'membership_rule', 'n_features', 'family', 'alias_of'])
        settings = '; '.join(key + '=' + _cell(_value(row, key)) for key in ['prep', 'variant', 'gamma_nominal', 'gamma_effective', 'initialization', 'source_specification_deviations', 'paper_deviations', 'preparation_assumptions'])
        settings += '; k=5; Lloyd n_init=1; rounding seeds=0..49; historical-style IRLS max_iter=300, tol=1e-6, epsilon=1e-8'
        if row['endpoint'] == 'native_best_of_50': settings += '; selected_seed=' + str(_value(row, 'seed'))
        solver = '; '.join(key + '=' + _cell(_value(row, key)) for key in ['solver_status', 'configuration_source_kind', 'matched_sc_status'])
        provenance = '; '.join(key + '=' + _cell(_value(row, key)) for key in ['historical_identity', 'config_id', 'sample_manifest_sha256', 'F_sha256', 'G_sha256', 'scientific_source_fingerprint', 'source_record_id'])
        # Content values are escaped once by the table-cell writer.
        values = [row['pool'] + ' / ' + row['endpoint'], source, settings, solver, provenance]
        text.append('| ' + ' | '.join(_cell(value) if i == 0 else str(value) for i, value in enumerate(values)) + ' |')
    text += ['', 'Complete configurations, every failed/timeout/unrun point, and matched-SC coverage remain in the authoritative CSV records. These tables are generated from those records; no score is hand copied. Certification audits remain separate from the locked finite-iteration search outputs.', '',
        '## Separate certified-search availability', '',
        'The historical-style closest rows above are not certified optima. No comparable certified subset-search track was executed, so no certified closest winner is selected. The numerical USPS continuation is a separately saved output; its certificate cannot be transferred to an IRLS G, even where the recorded F/W inputs match.', '']
    status_rows=[r for r in (certified_status or []) if r['benchmark']==benchmark]
    if status_rows:
        text += ['| Pool / endpoint | Historical complete configurations (including aliases / canonical) | Unique complete inputs | Certified closest | Status |', '|---|---:|---:|---|---|']
        for row in status_rows:
            values=[row['pool']+' / '+row['endpoint'],str(row['historical_complete_configurations'])+' / '+str(row['historical_complete_canonical_configurations']),row['historical_complete_unique_inputs'],row.get('certified_closest_config_id') or 'UNAVAILABLE',row['status']]
            text.append('| '+' | '.join(map(_cell,values))+' |')
    else:text.append('The certified-search availability view has not been supplied; no certified winner or coverage count is inferred.')
    text += ['', 'Machine-readable availability is in `certified_search_status.csv`; same-input numerical-audit references remain in `../submission_refresh/usps_numerical_reference_input_identity.json` and the separate USPS audit/continuation tables.', '']
    return '\n'.join(text)
