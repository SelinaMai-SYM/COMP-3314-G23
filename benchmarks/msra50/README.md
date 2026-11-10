# MSRA source versions

**Current status, 2026-11-10:** native **MSRA25_EBSA_16x16** has been obtained
and checksum-verified. It is an adapted-resolution reconstruction with 1,799
rows and twelve classes. The strict original `load_dataset("MSRA50")` endpoint
remains unavailable because historical source identity and the stated 32x32
input have not been recovered. The separate Fast-CD 32x32 lead returned a
public HTTP 429 response; that is an access restriction, not proof of permanent
deletion. See [source recovery](../../docs/submission_refresh/source_recovery.md).

## Native EBSA candidate

The pinned EBSA source contains 1,799 images and 256 native pixel features.
Its 16x16 resolution differs from the SSC paper's stated 32x32 preparation.
The loader keeps all rows, including thirteen extra exact duplicate rows, and
preserves source order. All duplicate groups have consistent labels. No resize
or deduplication is applied. The MATLAB-declared double variables are read with
`scipy.io.loadmat(mat_dtype=True)`, then pixel values 0-255 are divided by 255.

| Source file | Bytes | SHA256 |
|---|---:|---|
| EBSA `MSRA25.mat` at `c72bfbf13ac0e67db1a756eb26d56b7b996b64cb` | 387675 | `3c8681c40ebbed2f6dc2d2f30e7c5195e947467e8cf6797faa44753a190cd659` |

Retrieve the file into the independent data root:

```bash
python -m benchmarks.msra50.retrieve --data-root /path/to/benchmarks
```

Then load the explicit version:

```python
from pathlib import Path
from benchmarks import load_dataset
X, y, metadata = load_dataset("MSRA25_EBSA_16x16",
                             root=Path("/path/to/benchmarks/msra50/data"))
assert X.shape == (1799, 256)
```

`load_dataset("MSRA50", version="ebsa16", root=...)` is an equivalent explicit
interface. The [manifest](manifest_ebsa16.yaml) records the native range, class
counts, duplicate checks and reader convention. Redistribution rights have not
been established, so the raw file remains outside Git. Public availability
alone does not establish permission to redistribute it. Upsampling would not
recover missing native pixels or establish historical identity.

## Historical source investigation (2026-10-21)

Chang et al. state MSRA50 as 1,799 images, twelve classes, resized to 32x32,
without a URL or a source citation. The related Chang, Nie, Yang et al. paper,
*Improved Spectral Clustering via Embedded Label Propagation*
(arXiv:1411.6241), states the same 1,799/twelve counts and 1,024 features,
referring to “He et al. 2004.” Its cited *Face Recognition Using Laplacianfaces*
is IEEE TPAMI 27(3):328-340, published in 2005.

He, Yan, Hu and Zhang's ICCV 2003 *Learning a Locality Preserving Subspace for
Visual Recognition* and He, Yan, Hu, Niyogi and Zhang's TPAMI 2005 paper describe
an MSRA collection of twelve people, 64-80 frontal images per person in each
of two sessions, cropped to 32x32. Neither gives the 1,799 count or a download
URL. The arithmetic range 12 x 2 x (64-80) = 1,536-1,920 contains 1,799, but
that does not identify an actual file.

The hypothesis that the paper used a particular two-session MSRA crop remains
unverified. MSRA-B, MSRA10K, MSRA-TD500 and MSRA-CFW were not substituted.
Package indexes or mirrors such as PyPI/TUNA are not evidence of dataset
identity. Phase 1, repair_round1 and Round 2 ran no MSRA50 clustering jobs.
At those dates no 1,799-row matrix had been obtained; the historical status
was `BLOCKED_DATA_NOT_OBTAINED`, rather than `DOWNLOADED_UNVERIFIED`.

| Historical request | HTTP | Finding |
|---|---:|---|
| `http://www.cad.zju.edu.cn/home/dengcai/Data/data.html` | 200 | No MSRA50 or BinAlpha matrix |
| `http://www.cad.zju.edu.cn/home/dengcai/Data/FaceData.html` | 200 | Yale, ORL and Extended Yale B links only |
| `https://lear.inrialpes.fr/people/triggs/events/iccv03/cdrom/iccv03/0385_he.pdf` | 200 | ICCV 2003 text; no 1,799 count or data URL |
| `https://people.engr.tamu.edu/rgutier/web_courses/cpsc689_s07/he2005laplacianfaces.pdf` | 200 | Twelve people, 64-80 images per session |
| `https://arxiv.org/abs/1411.6241` | 200 | Related-paper count and He citation |
| `https://arxiv.org/pdf/1411.6241.pdf` | 404 | That unversioned PDF path failed on the recorded date |

Task 1 rechecked three Deng Cai pages (HTTP 200) without finding MSRA50.
A GitHub repository search for `MSRA50 mat` returned zero repositories.
The versioned related-paper PDF was saved as
`resources/Chang_Nie_Yang_Huang_2014_arxiv_1411.6241v1.pdf`, 463,461 bytes,
SHA256 `d3d00b0fa2eeff938d65800a3a7e4d1b08987de73932e9bd04de801e708badb2`.
`https://arxiv.org/pdf/1411.6241v1.pdf` returned 200. The UTS-hosted AAAI paper
and the related paper supplied literature counts rather than actual arrays.
No unrelated MSRA dataset was downloaded under the MSRA50 name.

See [Round 2 source records](../../docs/round2_source_of_truth.md),
[the historical manifest](manifest.yaml) and
[the current source inventory](../../results/subset_search/source_inventory.csv).
Run `python -m pytest benchmarks/msra50/test_msra50.py` to check that the strict
original endpoint still rejects a substitute.
