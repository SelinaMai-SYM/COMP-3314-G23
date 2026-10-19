# Repair round 1 validation

Date: 2026-10-20. Workspace: `v1/`. Interpreter: `/Library/Frameworks/Python.framework/Versions/3.13/bin/python3` (Python 3.13.3). These are commands that were actually run and their outcomes. Nothing below is a planned-but-unrun check.

## pytest

```text
cd "/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v1"
/Library/Frameworks/Python.framework/Versions/3.13/bin/python3 -m pytest -q --tb=no
```

Outcome: **66 passed in 3.59s**, exit 0. Includes `tests/test_repair_round1_math.py` and dataset version tests. Not the paper's 50-run benchmark.

## Checksums (files on disk vs recorded SHA-256)

Computed with `hashlib.sha256` on 2026-10-20. Raw archives are gitignored (`benchmarks/*/data/.gitignore` `*` and root `*.zip`).

| Path | SHA-256 | Bytes | Matches recorded manifest? |
| --- | --- | --- | --- |
| `benchmarks/orl/data/olivettifaces.mat` | `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794` | 4260520 | yes (`benchmarks/orl/manifest.yaml`) |
| `benchmarks/yaleb/data/YaleB_32x32.mat` | `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99` | 2214688 | yes (`benchmarks/yaleb/manifest.yaml`) |
| `benchmarks/usps/data/usps.bz2` | `3771e9dd6ba685185f89867b6e249233dd74652389f263963b3b741e994b034f` | 6579383 | yes |
| `benchmarks/usps/data/usps.t.bz2` | `a9c0164e797d60142a50604917f0baa604f326e9a689698763793fa5d12ffc4e` | 1831726 | yes |
| `benchmarks/jaffe/data/jaffe.zip` | `6da27f5954f969c6f65d782911834dd66827ec3580e79b95073eb6cb93de5c3b` | 12290558 | yes |
| `benchmarks/orl/data/att92/att_faces.zip` | `509d763bd2276aa054d260d7f1000e8be212738134f2f83d8ff13bc2adf1c8ec` | 3769022 | yes (`manifest_att92.yaml`) |
| `benchmarks/yaleb/data/cropped_wayback/CroppedYale_wayback_20220127.zip` | `8bbabf3836d077d60626c9ee3c54c2d2851a8d2c15c8b7e13b9bc162e86ea573` | 58493820 | yes (`manifest_cropped.yaml`) |

`git check-ignore -v` on the three zip paths reported `benchmarks/*/data/.gitignore:2:*`. JAFFE / att_faces / CroppedYale zips were **not** staged.

## LaTeX

```text
cd report
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Outcome: exit 0. `Output written on main.pdf (13 pages, 275273 bytes).` Style file `neurips_2026.sty` was not edited. Preamble keeps `\usepackage[preprint]{neurips_2026}`.

Then:

```text
cp -f main.pdf Group_23.pdf
cmp -s main.pdf Group_23.pdf && echo IDENTICAL
```

Outcome: `Group_23.pdf IDENTICAL to main.pdf` (275273 bytes, 2026-10-20 03:49 CST).

## PDF page check

```text
pdfinfo main.pdf
rg Overfull main.log
pdftotext -layout main.pdf -
```

`pdfinfo` outcome:

- Pages: **13**
- Page size: 612 x 792 pts (letter)
- File size: 275273 bytes
- Producer: pdfTeX-1.40.27
- CreationDate: Tue Oct 20 03:49:05 2026 CST

`rg Overfull main.log`: **no matches**.

`pdftotext -layout` headings:

- Page 1: title, Group 23, abstract / intro
- Page 2: Section 2 Background and SSC
- Page 3: Table 1 (repair-round-1 ACC/NMI)
- Page 4: contains `6   Conclusion`, `Acknowledgments and Disclosure of Funding`, and `References`
- Page 5: remaining bibliography, then Appendix A (Equation audit)
- Page 6: end of Appendix A and Appendix B Dataset files
- Pages 7–13: NeurIPS Paper Checklist

**Main text (title through conclusion, including abstract and the short acknowledgement) ends on page 4.** References begin on page 4. Appendix begins on page 5. This meets the four-page main-text cap. References, appendix, and checklist are excluded from that cap.

## Git (pre-push)

```text
git status -sb
git remote -v
```

Outcome immediately before the repair-round-1 closeout commit:

- Branch: `v1...origin/v1 [ahead 1]` (math checkpoint `a29efda`)
- Remote: `git@github.com:SelinaMai-SYM/COMP-3314-G23.git` (SSH fetch and push)
- Working tree: modified loaders/optimizer-adjacent files, untracked `configs/repair_round1/`, `runs/repair_round1/`, `results/repair_round1/`, repair docs, extra manifests

Push of the closeout commit is recorded in the git log after `git push -u origin v1`. This document does not invent a remote hash before that push returns.

## Honesty checks encoded in the PDF

- No 50-run claim on YaleB (`n=10`) or USPS (`n=3`).
- No novel theorem (checklist Theory = N/A).
- Course project, not a NeurIPS submission (`preprint` option; author footnote).
- ORL 76% is **not** claimed as reproduced (E8 53.3±3.2, n=50).
- Category C (row-norm, mutual kNN, K-means on F) is labelled diagnostic.
- SPLS cells remain N/A — not reproduced.
