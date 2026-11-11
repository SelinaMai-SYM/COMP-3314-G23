import numpy as np
from scipy import sparse
from experiments.extension_verification.diagnostics import stopping_tube_diagnostic
from method_extension.extension_verification.convex import Problem,solve


def test_inactive_tubes_share_an_existing_SSC_certificate_without_a_new_fit():
    H=np.array([[0.,0.],[4.,0.]]);W=sparse.csr_matrix([[0.,1.],[1.,0.]])
    fit=solve(Problem(H,W,.1),max_iter=10000,cpu_limit=10)
    row=stopping_tube_diagnostic(H,W,fit['G'],.1,.25,(fit['G'],fit['q']))
    assert row['ordinary_SSC_output']['all_edges_at_or_above_frozen_tolerances']
    assert row['ordinary_SSC_output']['E1_cross_certificate']
    assert row['strictly_inside_stopping_tube_count']==0
