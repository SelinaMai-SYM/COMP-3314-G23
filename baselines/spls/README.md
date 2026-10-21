# SPLS / SLPS

**Package status:** `NOT_IMPLEMENTED`

Hou et al. call the method **SLPS** (Subspace Learning via Pattern Shrinking). Chang et al. write **SPLS**. Section 3 of Hou et al., IPM 2013 was **not** obtained on 2026-10-21. `fit_predict` raises `NotImplementedError`. No substitute shrinking, no SSC IRLS, no LSDA, no 2016 PSLSR/SLSR, no invented numbers.

Master index: [`baselines/README.md`](../README.md). URL log below.

## Original publication

| Role | Record | Provenance type |
| --- | --- | --- |
| Paper | Hou, Nie, Jiao, Zhang, and Wu, *Information Processing & Management* 49(4):871–883, 2013. DOI `10.1016/j.ipm.2013.01.004`, PII `S0306457313000095`. Title: “Learning a subspace for clustering via pattern shrinking.” | `VERIFIED ORIGINAL PUBLICATION` at **metadata / open abstract** level. Full text including Section 3: **not obtained**. |
| SSC citation | Chang et al., AAAI 2015, “SPLS (Hou et al. 2013)”. They call it the second-best clustering algorithm. | `VERIFIED ORIGINAL PUBLICATION` for the name and table |
| Author code | None found. Chenping Hou homepage `[PDF]` is the Elsevier DOI, not a hosted manuscript. | not `VERIFIED AUTHOR CODE` |
| This package | placeholder | `NOT_IMPLEMENTED` |

Open abstract (ScienceDirect, highlights; WebFetch 2026-10-20 and re-checked 2026-10-21): linear subspace; replace original points by **shrunk patterns**; inspired by Zhou, Bousquet, Lal, Weston, and Schölkopf (2003); parameter **α**; “how to derive the approximated solution in a quick way” is in **Section 3**, which is not in the open abstract. Experiments listed: Orl, Mnist, Coil20, Isolet, Newsgroup — not the SSC eight-dataset table.

## Original math (original equation numbers)

**Unknown.** Section 3 was not obtained. A citing recap in Gao et al., “Local Shrunk Discriminant Analysis (LSDA)”, arXiv:1705.01206, uses parameters **δ and β**, not Hou’s **α**, and does not reprint Hou’s solver. That recap is **not** treated as a verified transcription and was **not** implemented.

## Original algorithm mapped to paper sections

Cannot map. Section 3 is the missing solver.

## Our implementation mapped to real files

Import: `from baselines.spls import fit_predict`

| Piece | File | Function | Lines (verified 2026-10-21) |
| --- | --- | --- | --- |
| Placeholder | `baselines/spls/spls.py` | `fit_predict` | 10–45: `raise NotImplementedError` |
| Export | `baselines/spls/__init__.py` | `fit_predict` | — |
| Jobs | `experiments/methods.py` / `scripts/run_experiment.py` | SKIPPED | reason: NOT_IMPLEMENTED |

Arguments are accepted so the positional signature matches other baselines. They are not used.

## Fidelity audit

| Item | Status |
| --- | --- |
| Whole method | `NOT_IMPLEMENTED` |
| Substitute SSC / PCA / generic shrinking / LSDA / SLSR | **forbidden** |
| Result cells | **N/A — not reproduced** |

## SSC comparison protocol vs this baseline’s own paper settings

Chang et al. would have searched `{1e-6,…,1e6}` if they treated SPLS as a “comparison algorithm”. That is not a substitute for Hou et al.’s own grid, which lives in the unread Section 3 / experiments.

## Tests actually run

`baselines/spls/test_spls.py`: `test_spls_is_not_implemented` (line 24). Asserts `NotImplementedError` matching `NOT_IMPLEMENTED`.

## Experimental results

**Our Reproduction: none.** Do not invent numbers.

Paper ACC% quoted only: AR 49.2±1.4, JAFFE 79.5±2.1, ORL 74.2±1.8, UMIST 70.4±1.6, BinAlpha 48.5±1.9, MSRA50 60.3±1.3, YaleB 47.3±1.7, USPS 71.4±1.6.

SKIPPED Phase 1 jobs include `20261020_015220__TRACKA__SPLS__ORL__61b83b0e`, `20261020_015459__TRACKA__SPLS__JAFFE__e00b63ba`, `20261020_015757__TRACKB__SPLS__ORL__e934d2ba`, `20261020_015826__TRACKB__SPLS__JAFFE__3021ed53`, `20261020_015846__TRACKB__SPLS__YALEB__255aeed5`, `20261020_020246__TRACKA__SPLS__USPS__4f11644e`.

## Limitations

- No Section 3, no official code, no OA PDF.
- HKU Find@HKUL catalog search returned a Primo HTML shell (JS required); this session had **no authenticated ScienceDirect download**. Paywalls were not bypassed.
- Local CPython `urllib` fails TLS (`CERTIFICATE_VERIFY_FAILED`) on this machine; HTTP statuses below are from `curl` and from Cursor WebFetch/WebSearch, not from that broken client.

## Round 2 URL log (2026-10-21)

Access: `curl -L --max-time 15` unless noted. No paywall bypass. Section 3 PDF = no in every row.

| URL | Asked | HTTP / status | Section 3 / PDF? |
| --- | --- | --- | --- |
| https://doi.org/10.1016/j.ipm.2013.01.004 | Canonical DOI | 200, redirect to linkinghub | No |
| https://www.sciencedirect.com/science/article/abs/pii/S0306457313000095 | Publisher abstract | curl 403 (bot); WebSearch/WebFetch: open abstract + “Purchase PDF” | Abstract only |
| https://www.sciencedirect.com/science/article/pii/S0306457313000095 | Full HTML | curl 403 | No |
| https://api.crossref.org/works/10.1016/j.ipm.2013.01.004 | Metadata | 200 JSON | Metadata only |
| https://api.openalex.org/works/https://doi.org/10.1016/j.ipm.2013.01.004 | OA locations | 200; `is_oa=false`, `oa_url=null`, `any_repository_has_fulltext=false` | No |
| https://api.unpaywall.org/v2/10.1016/j.ipm.2013.01.004 | OA | 200; `is_oa=false`, `oa_status=closed`, `has_repository_copy=false`, `oa_locations=[]` | No |
| https://api.semanticscholar.org/graph/v1/paper/DOI:10.1016/j.ipm.2013.01.004 | OA PDF | 200; `isOpenAccess=false`, `openAccessPdf.status=CLOSED` | No |
| https://export.arxiv.org/api/query?search_query=all:"Learning a subspace for clustering via pattern shrinking" | Preprint | 200; `opensearch:totalResults=0` | No preprint |
| https://dblp.org/rec/journals/ipm/HouNJZW13 | DBLP | 202 HTML | DOI only |
| https://chenpinghou.github.io/ | Author homepage | 200 | No PDF |
| https://raw.githubusercontent.com/ChenpingHou/ChenpingHou.github.io/main/years.html | Publications list | 200; 2013 IPM `[PDF]` href is `https://doi.org/10.1016/j.ipm.2013.01.004` | DOI only |
| https://chenpinghou.github.io/code.html | Author codes | 200 | No SLPS entry |
| https://api.github.com/users/ChenpingHou/repos | Author repos | 200; names listed, none SLPS/SPLS | No |
| https://orcid.org/0000-0002-9335-0469 | Chenping Hou ORCID | 200 | No PDF |
| https://iopen.nwpu.edu.cn/info/1329/1213.htm | Feiping Nie NWPU | 200 | 2013 IPM not among posted PDFs |
| http://ranger.uta.edu/~nie/ | Former UTA page | 404 (https redirect) | No |
| http://www.escience.cn/people/houchengping/ | Old homepage | 502 | No |
| https://faculty.nudt.edu.cn/ | NUDT faculty | curl TLS `SSL_ERROR_SYSCALL` | No |
| https://find.lib.hku.hk/discovery/search?query=any,contains,Learning%20a%20subspace%20for%20clustering%20via%20pattern%20shrinking&tab=Everything&search_scope=MyInst_and_CI&vid=852HKU_INST:HKU | HKU Find@HKUL | 200, redirect to Primo; “JavaScript must be enabled”; no authenticated PDF in this session | Catalog only |
| https://hub.hku.hk/simple-search?query=Learning+a+subspace+for+clustering+via+pattern+shrinking | HKU Scholars Hub | 403 | No |
| https://europepmc.org/search?query=Learning%20a%20subspace%20for%20clustering%20via%20pattern%20shrinking | Europe PMC | 403 | No |
| https://core.ac.uk/search?q=Learning%20a%20subspace%20for%20clustering%20via%20pattern%20shrinking%20Hou | CORE | 403 | No |
| https://citeseerx.ist.psu.edu/search?q=Learning+a+subspace+for+clustering+via+pattern+shrinking | CiteSeerX | 404 → archive.org | No OA PDF obtained |
| https://arxiv.org/pdf/1705.01206v1.pdf | LSDA citing recap | 200 PDF | Secondary; **not implemented** |
| https://github.com/jiaoboleetc/SLSR | 2016 PSLSR/SLSR | 200 | **Different method**; must not substitute |

Round 1 log: `docs/repair_round1_baseline_audit.md`. Decision unchanged.

## Task 1 URL log (2026-10-21, later the same day)

No paywall bypass. Section 3 PDF = no. Details: [`resources/README.md`](resources/README.md).

| URL | HTTP | Section 3 / PDF? |
| --- | --- | --- |
| Unpaywall v2 `?email=ssc.recovery@hku.hk` | 200 | `is_oa=false`, `oa_status=closed`, `oa_locations=[]` |
| OpenAlex same DOI | 200 | `oa_url=null`, `any_repository_has_fulltext=false` |
| Semantic Scholar same DOI | 200 | `CLOSED` |
| arXiv export exact title | 200 | `totalResults=0` |
| chenpinghou.github.io / years.html / code.html | 200 | `[PDF]` is Elsevier DOI; no SLPS on code page |
| `api.github.com/users/ChenpingHou/repos` | 200 | no SLPS; `PublicationCode` empty |
| Find@HKUL | 200 catalog | no authenticated PDF |
| hub.hku.hk | 403 | no |

`fit_predict` still raises `NotImplementedError`. Matrix status: `BLOCKED_MISSING_METHOD`. Code: `CODE_NOT_FOUND`.

## Reproduction commands

```text
python -m pytest baselines/spls -q
python -c "from baselines.spls import fit_predict; import numpy as np, pytest; pytest.raises(NotImplementedError, fit_predict, np.ones((4,2)), 2, 0)"
```
