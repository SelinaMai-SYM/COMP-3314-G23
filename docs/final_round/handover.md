# 20-point handover

Written after the E1–E6 report rewrite. Hashes below are filled after the report commit. Pre-experiment HEAD was `cb870acd47f9a62726c0cdab9b3b03395cc5e1cc` and was not reset.

1. **Does shrinkage help at protocol γ = 1?** Not as a general fact. Paired ΔACC (G−F, E8, same 50 seeds): ORL random +0.0109, 95% CI [+0.0030, +0.0187]; JAFFE random −0.0009 (CI contains 0); YaleB random −0.0072, CI [−0.0097, −0.0048]; USPS random −0.0004 (CI contains 0). Only ORL is a small positive exception (~1.1 pp). YaleB is worse.

2. **Does k-means++ explain the published gap?** No, and it is Level C, not the paper method. ORL ++ ΔACC +0.0006 (CI contains 0). YaleB ++ remains negative (−0.0023, CI below 0). ++ lifts ORL F 0.562 → 0.783 and JAFFE 0.685 → 0.953, but JAFFE ++ exceeds published SSC 81.2%, and YaleB ++ reaches only 0.218 vs published SC 34.8%. Not a reproduction of the table.

3. **Does more optimization improve ACC?** No, not on the three E3 cases. Unconverged at 300; stop at 825 / 359 / 355; budget 2000 identical. Objective change 2.5e-5 / 1.3e-5 / 6e-6. ACC 0.57265 → 0.57135 (ORL, down), 0.17622 → 0.17614, 0.73687 → 0.73861 (USPS γ = 1000). After the step-size stop, residual 0.002 / 0.171 / 0.058 is not a global-opt certificate.

4. **Main-text page count.** Four pages. `pdfinfo` reports 5 pages total: title through Section 7 Conclusion on pages 1–4; acknowledgments start on page 4; references continue on page 5. No appendix.

5. **HEAD vs origin/v1 hashes.** Pre-experiment HEAD = origin/v1 = `cb870acd47f9a62726c0cdab9b3b03395cc5e1cc`. New local HEAD and `origin/v1` after this push: see the git commit recorded with this file (filled at push time). Never reset, never force-pushed, never pushed `main`.

6. **What is NOT reproduced.** AR (not downloaded); UMIST-564 (565 unique cropped files, not 564); MSRA50 (not found); BinAlpha as a paper identity (`CANDIDATE_BIN_ALPHA` only); SPLS (`NOT_IMPLEMENTED`); LDA-SC (`APPROXIMATE`, not on the faithful table). Published Table 1 SC/SSC on ORL, JAFFE, YaleB, and USPS is not matched by E8 γ = 1. Figure 1 / Figure 2 were not curve-matched. The project is not marked fully reproduced.

7. **Checklist in the compiled PDF?** No. `report/checklist.tex` remains on disk and is not `\input`. `pdftotext` has no “NeurIPS Paper Checklist”.

8. **Overfull hbox?** No. `main.log` has no Overfull and no Underfull.

9. **Title.** When Does Spectral Shrinkage Improve Clustering? A Reproduction and Failure Analysis of SSC.

10. **Main-table numbers (Our cells, n = 50, `strict_reproduction_matrix.csv`).** ORL SC 56.2 ± 4.2 / E8 57.3 ± 3.8; JAFFE SC 68.5 ± 11.2 / E8 68.4 ± 11.1; YaleB cropped SC 18.3 ± 1.3 / E8 17.6 ± 1.2; USPS SC 61.7 ± 8.1 / E8 61.7 ± 8.1. Paper columns are “Reported in Chang et al. (2015)”, historical only. Sources in `docs/final_round/report_evidence_map.md`.

11. **Group_23.pdf path.** `report/Group_23.pdf` (229264 bytes, SHA-256 `c33304078bc4a8144d4630406e6fd0f420b9b34790910247973f905b5ae99853`), byte-identical to `report/main.pdf`.

12. **Commit hash.** Filled after `git commit` on branch `v1`. Parent is `cb870ac`. Not an amend of that parent.

13. **Convexity vs clustering.** CONFIRMED on the n = 6 CVXPY check: E8 matches Eq. (8) at printed γ; E13 matches γ/2. Cite existing test, not a new proof. Convexity is only G given fixed F, W. E8 is not claimed to be the authors’ historical code.

14. **YaleB data versions.** Both 2414 × 1024, 38 classes, pixels [0, 1], same per-class counts. Best alignment (transpose) median L2 1.92; zero images coincide at 1e-8. K-means(F) ACC cropped 0.1834 vs Deng Cai 0.2016 under identical graph/seeds. Paper SC 34.8%. Bandwidth / symmetrization / row-norm / interpolation are B or C; max ACC was not adopted.

15. **USPS γ.** At γ = 1, ACC stays at SC (~0.617). At the preset grid point γ = 1000, ACC 0.7369; at γ = 1e6, ACC 0.3881. γ was not selected by ACC. Larger TV drop is not higher ACC (YaleB monotonically down).

16. **Authors / emails.** Group 23, HKU COMP3314 only. Names and emails require confirmation and were not invented. Authors were not contacted.

17. **Extension.** Existing mutual-kNN on JAFFE, n = 50: 68.4 ± 11.2 vs union E8 68.4 ± 11.1 (410 vs 655 edges; 20 vs 9 components). Negative/neutral. `method_extension/` algorithm was not changed. No new method.

18. **72-cell matrix.** Not rerun. Main-table numbers are the existing `runs/strict_paper/` n = 50 cells indexed by `results/strict_reproduction_matrix.csv`. New work is E1–E6 under `runs/final_round/` and `results/final_round/`. Embedding `.npy` files are gitignored.

19. **E6 audit.** 52 completed strict_paper cells: seeds exactly 0..49, sample SD ddof = 1, one F (and one G). The printed ± is K-means noise on one embedding, not 50 independent shrinkages. Pytest 16 passed.

20. **Git / remote.** Branch `v1` only. Remote `origin` = `git@github.com:SelinaMai-SYM/COMP-3314-G23.git` (SSH). Do not push `main`. Do not force-push. Do not rewrite history. After `git push -u origin HEAD`, local HEAD must equal `origin/v1`.
