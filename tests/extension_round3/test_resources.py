"""Failed native work must remain charged to every target on one path."""
from experiments.extension_round3.run import native_path_cpu


def test_native_path_cap_includes_failed_segments_and_other_targets():
    task={'benchmark':'ORL','method':'TUBE_UNIFORM','tau_multiplier':1.}
    lookup={'first':dict(task,rho=.1),'second':dict(task,rho=.05),
            'third':dict(task,rho=.2),'other':dict(task,tau_multiplier=4.),
            'different':dict(task,method='QSSC')}
    state={'entries':[{'run_id':'r3-first-0','charged_cpu_seconds':1790.},
                      {'run_id':'r3-first-1','charged_cpu_seconds':3.},
                      {'run_id':'r3-second-0','charged_cpu_seconds':2.},
                      {'run_id':'r3-other-0','charged_cpu_seconds':500.},
                      {'run_id':'r3-different-0','charged_cpu_seconds':400.}],
           'active':{'r3-third-0':{'seconds':4.}}}
    assert native_path_cpu(state,lookup,task)==1799.
    # Only one second remains, even if the last committed path.json missed
    # the failed 1790-second worker. A new 600-second fit is inadmissible.
    assert 1800.-native_path_cpu(state,lookup,task)==1.
