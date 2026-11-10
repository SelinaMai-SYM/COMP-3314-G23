> Historical record translated into English on 2026-11-10. Statements describe the earlier stage; see [current findings](submission_refresh/research_findings.md) for subsequent corrections and results.

# Course requirement cross-check

The historical sources were text extracted from `3314 GP Guidelines.pages` and the NeurIPS 2026 template. They did not contain member names. At this stage Group 23 was inferred from the planned repository name `COMP-3314-G23` and still needed confirmation. This document does not invent grading weights.

## Requirements read from the materials

### Paper choice and analysis

- Select and study a machine-learning paper related to the course, preferably from ICML, ICLR, NeurIPS, AAAI, CVPR, ACL, JMLR, Machine Learning, TMLR, or IEEE TNNLS, TPAMI, TIP, TCSVT. Consult the instructor or teaching assistant when uncertain.
- Explain the problem, motivation, method, and main contributions, and connect them to course concepts.
- Discuss the experimental setup and results, identifying the evidence supporting the conclusions.
- Critically analyze assumptions, strengths, limitations, and possible improvements or extensions.
- The selected paper was Chang et al., AAAI 2015, *A Convex Formulation for Spectral Shrunk Clustering*. AAAI appeared in the guideline's AI/applied conference list.

### Written report

The guideline contained both of the following statements:

1. Deliverables described a Written Report of 3-4 pages, prepared in LaTeX. Suggested content included the problem and motivation, method and course connections, experiments, critical analysis, and the group's insights or extensions. Reproduction work should state its implementation scope, compare with the paper, discuss difficulties, and link the repository. Citations should distinguish the paper's figures/results from the group's own.
2. Report Submission stated that there were no hard requirements on template and page limit, suggested NeurIPS style, and then specified a maximum of four main-text pages excluding references and appendix. It required preprint mode, `\usepackage[preprint]{neurips_2026}`, member names and affiliations, PDF submission named `Group_xx`, and a public GitHub link when reproduction code was available. A separate code archive was unnecessary.

The historical reading treated the 3-4-page LaTeX description as suggested length and retained the adjacent four-main-page statement without inventing a deduction rule. The current submission follows the explicit four-main-page maximum. The NeurIPS template's nine-page conference limit is not the course limit.

Report deadline: 2026-11-29 23:59; opening time: 2026-10-13 00:00. The displayed due time was Sunday, 29 November 2026, 11:59 PM. The guideline placed the report after the slides to allow further refinement.

Names and affiliations were absent from the materials at this historical stage and needed confirmation. Names, email addresses, and grant numbers must not be invented.

### Optional reproduction credit

- Numerical results, figures, or experiments may be reproduced fully or partially. State the scope, comparison, discrepancies, and difficulties.
- A from-scratch implementation when official code is unavailable receives additional consideration. This project did not have official code.
- Submitted code should be public on GitHub with a README describing the paper, environment, commands, results, and the distinction between original and reused code.
- The guideline allowed up to 10 additional percentage points, assessed separately from the base score. This was not a weight within the base score.

### Presentation

- Nine minutes of presentation and three minutes of questions; all members participate.
- Cover the paper, course connections, evidence, critical analysis, and lessons. Reproduction details and comparisons should fit within the available time.
- Slides deadline: 2026-11-15 23:59; opening: 2026-10-13 00:00. Filename: `Group_xx`; changes after the deadline were not permitted.
- Slides were outside this historical implementation stage.

### Rubric text

The table headings were Component, Weight, Description. Numeric weights could not be extracted reliably and are omitted.

| Component | Description |
| --- | --- |
| Paper Understanding | Accuracy and depth in explaining the problem, methods, contributions, and connections to course topics |
| Critical Analysis & Insight | Thoughtful interpretation of the paper's evidence, evaluation of assumptions and limitations, and well-supported insights or proposed extensions |
| Written Report | Clarity, organization, coherence, and appropriate use of figures and citations |
| Presentation & Q&A | Clarity, structure, effective use of visuals, and quality of responses during Q&A |

The preceding `f`, `N`, and `Q` characters in the extracted strings were protobuf length bytes, not report text.

### Other dates and original links

- Groups contained 3-4 members; formation deadline: 2026-09-17 23:55, with random allocation afterward.
- Paper selection ran approximately 2026-09-23 through 2026-09-28 23:59, first come first served, without duplicate papers across groups.
- GPU facility: `https://ai.hku.hk/research/major-facilities?view=article&id=130&catid=24`
- Group selection: `https://moodle.hku.hk/mod/choicegroup/view.php?id=4279779`
- NeurIPS call: `https://neurips.cc/Conferences/2026/CallForPapers`
- Other original Moodle IDs were `4303930`, `4324469`, `4324470`, and `4324471`; their precise table/schedule/submission mappings require the Moodle pages.

## Status at the historical stage

| Requirement | Historical status |
| --- | --- |
| Selected AAAI 2015 SSC paper and checked formulas | `docs/ssc_mathematical_audit.md` written |
| From-scratch SSC without evaluation labels in fitting | Implemented in `SSC_method/` |
| Hungarian one-to-one ACC and geometric NMI | Shared `benchmarks/metrics/`, with small contingency-table tests |
| Reproduction deviations | `docs/reproduction_deviations.md` recorded method differences; no numerical experiments yet |
| Report, checklist, PDF | Not written; a later stage was responsible |
| Slides | Not made |
| Public GitHub and README results | Code README existed; publication and experiments were outside this stage |
| Member names and affiliations | Awaited confirmation |
| Rubric weights | Not reliably extracted; omitted |
