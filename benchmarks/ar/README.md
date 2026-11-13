# AR Face Database

Chang et al. report 840 faces of 120 people without identifying the selected
images or a resize size. The explicit LZUFE parent used here contains 1,680 rows,
120 identities and fourteen rows per identity. Seven-of-fourteen candidates are
reproducible membership hypotheses; they do not recover historical indices.
The strict `load_dataset("AR")` endpoint therefore raises `DatasetUnavailable`.

## Source and identity

The original database is attributed to Martinez and Benavente, *The AR Face
Database*, CVC Technical Report 24 (1998). The original release describes 126
people and more than 4,000 images, with access and redistribution conditions.
The [supporting references](resources/README.md) document the source definition.

For the explicit `lzuf_superset1680` version, place the
[LZUFE AR matrix](https://raw.githubusercontent.com/LZUFE-Machine-Learning/Datasets/main/AR.mat)
at `ar/data/private/lzuf_candidate_AR.mat` beneath the independent data root.
Its expected SHA-256 is
`4c8355c5afef6502d73b492a3c8d3565470bb5e11c8494e880710e630421f30b`.
The loader verifies this hash, shape `(1680,1024)`, 120 labels and fourteen rows
per identity. It retains stored row order and shifts original label codes to
0–119. A feature count of 1,024 is not proof of 32×32 image geometry.

```python
from pathlib import Path
from benchmarks import load_dataset

X, y, metadata = load_dataset(
    "AR", root=Path("local/data/ar/data"), version="lzuf_superset1680"
)
```

The full parent is a diagnostic input, not an equivalent 840-image reconstruction.
A separate third-party `ARDB_Full.zip` source has only 100 identities and different
file naming/spatial dimensions. It is not accepted as the paper's 120-identity
input. Its source identity remains documented in [the source manifest](manifest.yaml).

## Candidate membership

The [catalogue](../../configs/subset_search/candidate_catalogue.json) preserves
original zero-based row IDs, exact selected/excluded indices and class quotas.
The four fixed within-class position rules are first7 `0..6`, last7 `7..13`,
even7 `{0,2,4,6,8,10,12}` and odd7 `{1,3,5,7,9,11,13}`. Random candidates use one
recorded RandomState per subset seed, traversing identities canonically and
selecting seven rows without replacement independently within each identity.
Common-mask candidates use one seven-of-fourteen position mask across identities.
Position alignment does not establish sessions, illumination or expression.

Subset generation belongs to the declared experiment interfaces; the parent
loader does not silently select 840 rows. Changed membership receives a fresh
A/F/W/G construction. See [experimental protocol](../../docs/experimental_protocol.md)
and [data identity limitations](../../docs/limitations.md).

## Terms

The original AR release is for academic research, excludes commercial use and
prohibits redistribution; access uses the provider's application/password
procedure. A third-party upload's claimed license does not override those terms.
Images and matrices remain outside the public code tree. Credit Martinez and
Benavente and retain the original source conditions.
