"""Scientific cache keys include the complete immutable registration context."""
from experiments.submission_refresh.core import identity
FIT_FIELDS=('benchmark','panel','kind','gamma','parameters','source_fingerprint','protocol_sha256','anchor_sha256','W0_sha256','input_registration_sha256','environment_fingerprint')

def fit_key(value):return identity({name:value[name] for name in FIT_FIELDS})
