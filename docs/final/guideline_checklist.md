# COMP3314 guideline checklist

Source: the user-provided course guidelines PDF, read in full; detailed submission clause sets main text <=4 pages. Deadlines use Hong Kong/Shanghai time. DONE means an actual file/check exists; future attendance/submission is not falsely marked complete.

| Requirement | Status | Actual file, section, command or limitation |
|---|---|---|
| Problem, motivation, contributions | DONE | Report section 1 |
| Method and course concepts | DONE | Report section 2: Laplacian/eigenvectors, regularization, convexity versus K-means |
| Original experimental setup and evidence | DONE | Report section 3, attributed paper values, ACC/NMI contradiction |
| Assumptions, strengths, limitations, own insight | DONE | Report section 4 and appendices; N0 dual, mechanism gate and fidelity/fusion distinctions |
| Reproduction optional, partial allowed | DONE | Explicit partial coverage and dataset/method/subset blockers; no missing cell filled with zero |
| Main text <=4 pages | DONE | LaTeX `main_end` label is on page 3; final 11-page PDF compiled and every page visually checked |
| NeurIPS 2026 preprint template | DONE | `report/main.tex` retains `\\usepackage[preprint]{neurips_2026}`; not a conference submission; no checklist included |
| Real group-member names and affiliations | DONE | User-confirmed Han Jiale; Lu Sinan; Mahatharadol Vie; Mai Sheung Ying. Group 23, The University of Hong Kong |
| Filename Group_23.pdf and source | DONE | `report/Group_23.pdf`, `report/main.tex`, generated tables and bibliography; report_verification.json records final render/hash checks |
| Public GitHub link in report | DONE | Conclusion links the v3 branch |
| Public code/setup/run/results | DONE | Final candidate passed in a new venv and shallow checkout; GitHub v3 remote shallow clone passed synthetic/rebuild; see validation and verification JSON records |
| Own versus reused code and citations | DONE | `sources_and_licenses.md`, bibliography, module docstrings and source snapshots |
| Paper results versus our measurements | DONE | Explicit table labels, fixed versus closest tracks and adjacent setting/solver deviations |
| Reproduction scope, discrepancies and challenges | DONE | Main sections 3-5, complete 72-cell appendix, metadata/array limitations |
| Presentation 9 minutes + 3 minutes Q&A | DONE (outline) | `presentation_outline.md`, `qa_notes.md`; full deck not requested |
| All members participate | PENDING_EVENT | Speaker roles to be assigned to actual members; attendance cannot be verified in advance |
| Existing slides with old numbers | DONE / NO_EXISTING_DECK_FOUND | No PPTX/Keynote source found in the repository; outline points to generated current tables |
| Slides deadline | DONE | 2026-11-15 23:59, recorded in README/outline |
| Report deadline | DONE | 2026-11-29 23:59, recorded in README/outline |
| PDF-only course-system submission | NOT_PERFORMED_BY_THIS_TASK | Group uploads final PDF; this task publishes GitHub and retains source, not a course-system upload |
| Understanding 40%, analysis/insight 30%, writing 10%, presentation/Q&A 20% | DONE | Main report/outline balance study and criticism rather than replacing them with a leaderboard |
| Reproduction bonus up to 10 points | DONE | Clearly described as optional; no score or bonus award claimed |
| N0/N1/N2/new performance extension claims reflect actual tests | DONE | Actual records under `results/next_round`; untriggered/uncertified experiments are labelled, not predicted gains |
| Default branch v3 and only-v3 remote heads | DONE | Verified default=v3 and sole remote head v3; v1/v2/candidate deleted individually with exact leases after default verification. publication_status.json records each operation |
