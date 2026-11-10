"""Availability of a separate certified search, without auditing or selecting G.

The locked subset campaign deliberately uses finite historical-style IRLS.
Its completed executions are coverage evidence, not primal-dual certificates.
Numerical audits on other saved outputs must not reclassify these outputs.
"""
from __future__ import annotations

ENDPOINTS=('mean_sample_sd_50','native_best_of_50')
UNAVAILABLE='UNAVAILABLE_NO_COMPARABLE_CERTIFIED_SEARCH_COVERAGE'
SCOPE=('No separate comparable certified subset-search track was executed. '
       'Historical-style completion is not certification. Numerical-audit '
       'certificates apply only to their own saved G and do not transfer to '
       'a historical-style G, even when F/W inputs match.')


def certified_search_status(complete_mean_rows,candidate_pools=None):
    """Describe every intended eligible pool, including zero-completion pools.

    Input rows must already have passed the complete 50-seed checks. This pure
    metadata view performs no certification, score ranking or winner selection.
    The two endpoints share their underlying complete 50-start configurations;
    a native endpoint still has one selected assignment and no across-run SD.
    """
    rows=list(complete_mean_rows);seen=set()
    pools={b:set(p) for b,p in (candidate_pools or {}).items()}
    for row in rows:
        if row.get('endpoint','mean_sample_sd_50')!='mean_sample_sd_50':
            raise ValueError('certified availability requires complete mean configuration rows')
        key=row['config_id']
        if key in seen:raise ValueError('duplicate complete configuration in certified availability')
        seen.add(key)
        if row['pool']!='diagnostic':pools.setdefault(row['benchmark'],set()).add(row['pool'])
    output=[]
    for benchmark,eligible in sorted(pools.items()):
        for pool in sorted(set(eligible)-{'diagnostic'}):
            group=[r for r in rows if r['benchmark']==benchmark and r['pool']==pool]
            canonical={(r.get('alias_of') or r['candidate_id'],r['variant'],float(r['gamma_nominal']),r['initialization']) for r in group}
            inputs={r.get('alias_of') or r['candidate_id'] for r in group}
            for endpoint in ENDPOINTS:
                output.append({'benchmark':benchmark,'pool':pool,'endpoint':endpoint,
                    'search_track':'historical_style_IRLS',
                    'historical_complete_configurations':len(group),
                    'historical_complete_canonical_configurations':len(canonical),
                    'historical_complete_unique_inputs':len(inputs),
                    'rounding_starts_per_complete_configuration':50,
                    'comparable_certified_search_configurations':0,
                    'certified_closest_config_id':None,'status':UNAVAILABLE,
                    'certificate_transfer_allowed':False,'scope':SCOPE})
    return output
