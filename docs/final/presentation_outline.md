# Nine-minute presentation + three-minute Q&A

All real group members must attend presentation and Q&A. Members: Han Jiale, Lu Sinan, Mahatharadol Vie, Mai Sheung Ying (user-confirmed). Assign the roles below among the actual members. Slides are due 2026-11-15 23:59 Hong Kong time; report 2026-11-29 23:59.

| Time | Proposed speaker | Content | Visual/evidence | Intended takeaway |
|---|---|---|---|---|
| 0:00-1:00 | Han Jiale | Problem, motivation and paper contributions | X -> A -> spectral F -> W -> refined G -> K-means | SSC changes representation geometry after the first spectral step |
| 1:00-3:30 | Lu Sinan | Method and course links | Laplacian/eigenvectors; E8 fidelity + graph TV; E8/E13 factor two | Convexity belongs to fixed-F/W refinement, not final labels |
| 3:30-5:30 | Mahatharadol Vie | Original evidence and partial reproduction | Generated `report/tables/final_main.tex`; complete 72-cell link; YaleB ACC/NMI contradiction | Distinguish reported evidence, fixed control and retrospective closest matching |
| 5:30-8:00 | Mai Sheung Ying | Performance diagnosis and extension | New certificate/gamma curves; Oracle versus matched weakening; two-group capped example | Test the mechanism before promoting a method; inner optimality is not nonconvex global optimality |
| 8:00-9:00 | Han Jiale; all join Q&A | Team insight and limitations | Actual mechanism gate, negative findings, resource/identity limits | Explain how much changed, why, and where evidence remains insufficient |

Use the latest generated tables and `results/next_round/primary_summary.json`; do not copy old gamma=1 prose or old robustness numbers. Use the closest-table settings beside the values, particularly E13/gamma/initialization/truncation and YaleB's alternate source/Y3 changes. New controls use shared F/W and greedy++ seeds; they cannot be compared as if they were the historical random reference.

Describe the 2-point mean-ACC/nondecreasing-NMI target as a predeclared goal, not a promised result. If the wrong-edge gate is not met, present its measured negative/inconclusive result and the synthetic/theory boundary. Do not replace missing formal real-data capped experiments with the five-point native prclust check.

Suggested team roles: motivation/paper evidence; mathematical method/course links; reproduction/setup/results; critical analysis/extensions/Q&A coordination. Adjust to actual group size (3-4), keeping participation across the presentation and Q&A.

Speaker allocation above is a concrete editable proposal, not a claim of confirmed attendance. All four members participate in Q&A. Use the measured 0/4 locked gate, YaleB W length AUROC .380, capped initialization values 3 versus 8, and the distinction between stability and class quality; do not present the 2-point target as achieved.
