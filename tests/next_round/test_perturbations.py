import numpy as np
from method_extension.v3_theory.x2_stability_graph.weights import perturb_images

def test_usps_domain_and_zero_identity():
    X=np.array([[-1.,-.5,0,.5,1.]])
    np.testing.assert_array_equal(perturb_images(X,0,1,domain=(-1,1)),X)
    changed=perturb_images(X,2,1,domain=(-1,1))
    assert changed[0,1]<0
    np.testing.assert_allclose(changed,np.clip(X+4/255,-1,1))
