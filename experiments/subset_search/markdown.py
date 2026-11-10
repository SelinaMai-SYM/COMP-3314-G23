"""Pure benchmark views shared by aggregation and the scalar-only rebuild."""
from __future__ import annotations
import json


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


def benchmark_markdown(benchmark, winners, paper, certified_status=None):
    """Render all four pool/endpoint slots without data or artifact access."""
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
