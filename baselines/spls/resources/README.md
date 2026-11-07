# SPLS / SLPS — no Section 3 PDF

Task 1, 2026-10-21. Hou, Nie, Jiao, Zhang, and Wu, *Information Processing & Management* 49(4):871–883, 2013. DOI `10.1016/j.ipm.2013.01.004`.

**No legal full text including Section 3 was obtained.** This folder has no PDF.

| Probe | HTTP | Section 3? |
| --- | --- | --- |
| Unpaywall v2 (email `ssc.recovery@hku.hk`) | 200 | `is_oa=false`, `oa_status=closed`, `oa_locations=[]` |
| OpenAlex | 200 | `is_oa=false`, `oa_url=null`, `any_repository_has_fulltext=false` |
| Semantic Scholar | 200 | `openAccessPdf.status=CLOSED` |
| arXiv export query (exact title) | 200 | `opensearch:totalResults=0` |
| chenpinghou.github.io years.html `[PDF]` | 200 | href is the Elsevier DOI |
| chenpinghou.github.io/code.html | 200 | GitHub pointer; no SLPS repo |
| `api.github.com/users/ChenpingHou/repos` | 200 | no SLPS/SPLS; `PublicationCode` is empty |
| Find@HKUL | 200 catalog shell | no authenticated PDF in this session |
| HKU Scholars Hub | 403 | no |
| ScienceDirect HTML | curl 403 (bot) | abstract only; paywall not bypassed |

`baselines/spls/spls.py` remains `NotImplementedError`. LSDA arXiv:1705.01206 and PSLSR/SLSR were not substituted.

Strict URL Task 1 (later 2026-10-21): still no local PDF. ScienceDirect 403 Cloudflare challenge. Status `BLOCKED_MISSING_FULL_METHOD`.
