# Source recovery and independent data registration

This audit was performed on 2026-11-10 before evaluating new candidate scores.
The strict original AR, UMIST, BinAlpha and MSRA50 loaders still raise an
unavailable-dataset exception. Explicit source and candidate IDs do not resolve
those historical identities.

## Available EBSA MSRA25 source

The [pinned public file](https://github.com/LZUFE-Machine-Learning/EBSA/blob/c72bfbf13ac0e67db1a756eb26d56b7b996b64cb/dataset/MSRA25.mat)
was retrieved and verified: 387,675 bytes, SHA256
`3c8681c40ebbed2f6dc2d2f30e7c5195e947467e8cf6797faa44753a190cd659`.
`scipy.io.loadmat(mat_dtype=True)` reads MATLAB's declared double variables.
The loader checks keys, shape 1,799 x 256, native resolution 16 x 16, finite
integer pixels from 0 to 255, and the twelve class counts
`[175,154,113,178,186,159,179,128,133,131,128,135]`.
There are 13 extra duplicate rows; all duplicate groups have consistent labels.
All 1,799 rows remain in source order. Pixels are divided by 255 and never
upsampled. The dataset ID is **MSRA25_EBSA_16x16**, an adapted-resolution
reconstruction whose identity as the 2015 paper's MSRA50 remains unverified.

The raw file is kept outside Git because redistribution rights have not been
established. Reproduce acquisition with:

```bash
python -m benchmarks.msra50.retrieve --data-root /path/to/benchmarks
```

The [manifest](../../benchmarks/msra50/manifest_ebsa16.yaml) and
[source inventory](../../results/subset_search/source_inventory.csv) preserve
resolution, file identity and historical status separately.

## Fast-CD 32 x 32 lead

We read the README and loader at
[`f13a4f6e08fc5677062dfbbb2b208e324109edd7`](https://github.com/moetayuko/Fast-CD/tree/f13a4f6e08fc5677062dfbbb2b208e324109edd7).
The current README still points to the same SharePoint archive. Its loader
expects `MSRA50_uni.mat`, while the repository tree contains no such matrix.
The public repository has no releases or issues containing a replacement link;
its README history contains one commit. The [Fast-CD paper](https://arxiv.org/pdf/2311.15214)
lists 1,799 samples, 1,024 features and 12 classes. Those counts alone cannot
establish sample identity.

The direct public archive returned HTTP 429 at 05:54:44 UTC with
`Retry-After: 300` and a plain-text 21-byte response. The response was not saved
as a MAT file. After 487.86 seconds, a single bounded retry returned HTTP 429 again at
06:02:52 UTC with the same Retry-After and response length. No additional
archive requests were made. The bounded retry record is stored in
[source evidence](source_evidence/http_attempts.json). No alternate URL variants,
authentication bypass, or author contact were used. A 429 establishes a current
access restriction, not permanent deletion. No Fast-CD clustering settings or
label-based sorting were imported into SSC.

## Independent parent files

The verified AR LZUFE source and three UMIST parent files were copied from the
old local checkout into the independent benchmark root, under each dataset's
`data/private/` directory. Source and destination hashes were compared before
loading. [Copy verification](../../results/subset_search/source_copy_verification.json)
records relative paths, hashes and lengths. Current parent loaders resolve
explicit roots, the shared environment variable and the shared local pointer;
they do not read another worktree.

The AR matrix has 1,680 rows, 120 identities and fourteen images per identity.
The source supplies no verified session interpretation for within-class index
positions. The 840-image rules are index-order hypotheses or fixed-seed random
candidate reconstructions.

LZUFE UMIST has 574 rows and 564 distinct pixel rows, with consistent identity
labels in all ten extra duplicate rows. First-occurrence deduplication preserves
source order and a complete inverse mapping. Wayback575 has 565 distinct pixel
rows; its one-omission family is a hypothesis about an unknown omission. The
Roweis and Figshare MAT files have the same SHA256 and are source aliases, not
independent releases. Crop and resolution variants remain distinct.

The unchanged BinAlpha seed0 manifest is replayed using one RandomState(0)
advanced over A-Z, choosing 30 of 39 examples per letter without replacement.
Selected indices are sorted within each letter. The generated candidate must
match the stored manifest exactly; mismatch raises an error.

## Frozen reconstruction inventory

The catalogue contains exact selected and excluded indices, quotas, source
hashes, processed feature/label hashes, aliases and canonical source row IDs.
The first occurrence of each exact duplicate has a recorded original-to-retained
mapping. Both raw parent rows and a derived Wayback565 parent are available for
stratified sensitivity draws; their different memberships remain visible.
No clustering score enters catalogue generation. Candidate source membership
changes require fresh A, F, W and G downstream.

Raw pinned README/loader and public API responses are preserved outside Git
in the independent-data `source-audits/fastcd-20261110` directory. The
[external evidence manifest](source_evidence/external_evidence_manifest.json)
records exact hashes and retrieval links. The active HTTP investigation used
under one minute of request time, plus a bounded public web search; it stayed
below the 30-minute active-investigation limit.

## Acquiring the two local parent leads on another machine

The recorded public LZUFE URLs returned HEAD 200 on 2026-11-10, with the same
file lengths as the verified local files. They are retrieval leads; SHA256
verification remains required because a mutable `main` URL can change.
The [HEAD records](source_evidence/parent_url_heads.json) retain those observations.
For an empty independent data root, create the directories and retrieve files:

```bash
mkdir -p /path/to/benchmarks/ar/data/private /path/to/benchmarks/umist/data/private
curl --fail --location https://raw.githubusercontent.com/LZUFE-Machine-Learning/Datasets/main/AR.mat --output /path/to/benchmarks/ar/data/private/lzuf_candidate_AR.mat
curl --fail --location https://raw.githubusercontent.com/LZUFE-Machine-Learning/Datasets/main/umist.mat --output /path/to/benchmarks/umist/data/private/lzuf_umist.mat
```

Use these commands only when the destination files are absent; retain an
existing verified source instead of downloading it again. AR must match
`4c8355c5afef6502d73b492a3c8d3565470bb5e11c8494e880710e630421f30b`
and UMIST must match
`b66a95533e77a90310bc6119c219bc96e6ad8e343e50e0db0f5e740402d50d92`.
The frozen sample manifests reject different source bytes. If a mutable URL no
longer matches, preserve that failed acquisition and use the archived verified
source or report the source restriction; do not relabel new bytes as the old
parent. These matrices remain outside Git.
