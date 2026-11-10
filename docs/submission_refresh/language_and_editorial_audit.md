# Language and editorial audit

The submission refresh requires English throughout the published working tree. This audit covers project-owned Markdown, comments, docstrings, generated strings, configuration notes, CSV/JSON records, compressed scalar records, figure text, notebooks if present, and text extracted from committed PDFs. Mathematical symbols, established identifiers, accented author names, and legal attribution are retained. A Unicode scan identifies contexts for review; it does not by itself establish that prose is English.

## Changes and preservation

The original scan found CJK prose in 73 tracked paths, including duplicated source archives. Current method and baseline notes, environment instructions, historical recovery and experiment documents, course-guideline notes, and the strict runner's generated prose were translated. Historical documents carry a banner directing readers to current findings; their historical statuses and claims remain dated rather than being rewritten to anticipate subsequent evidence. Current benchmark translations are recorded separately in `results/subset_search/benchmark_translation_manifest.json`.

`docs/submission_refresh/english_transformations.json` records original and replacement hashes for the central editorial pass. Original files are separately available in the verified external backup's `english-originals` tree and Git history. Restricted data and third-party legal notices were not rewritten. New translations retain numerical measurements, seed values, run identifiers, equations, source URLs, and the distinction between an earlier incomplete implementation and subsequent work.

The two historical scientific archives were verified against their original manifests before transformation. Their original `SOURCE_MANIFEST.json` bytes remain at their original commit-named paths. All 1,582 original/replacement objects have explicit hashes in `archive/source_english/TRANSFORMATION_MANIFEST.json`; 40 differ because of English translations. The original source bytes were copied to the external backup before migration. The versioned English trees contain scientific source and configuration records for inspection, while current entrypoints continue to use the existing modules. A translated byte is never labelled with its original source hash. Historical release rebuilding continues to use the exact retained original source-manifest hashes and committed scalar inputs, without reading old Git objects.

## Scan evidence

The working-tree scan decoded 13,159 text files, including current untracked delivery files and retained run records. No notebooks were present in that scanned set. It inspected the decompressed `all_trials.csv.gz` (105,307,720 bytes) and `job_metadata.jsonl.gz` (6,959,743 bytes); neither contained CJK prose. All 41 committed PDF files extracted successfully and had no CJK/Japanese/Korean text flags. Their figure titles and scientific labels are English. The updated final report still requires its separate compile, per-page rendering, and visual review after authoring.

The detailed path inventory is in `results/submission_refresh/language_inventory.json`, with its UTC timestamp. After the remaining historical recovery translation, the repeated scan found no CJK/Japanese/Korean prose or filename flags. All PDF text extractions again succeeded without such flags. This is an editorial snapshot; the publication audit checks the subsequently finalized report and live links separately.

## Editorial boundaries and remaining checks

Prose now explains concrete actions, evidence, and limitations. Old resource tables remain historical records, not recommendations to bypass restrictions or present-day availability claims. External papers retain their original attribution and legal notices. Personal path strings that document a historical investigation remain evidence rather than runtime dependencies; current commands use an explicit data root. Repository description, current main-branch links, final report rendering, and the final no-data/real-data checks are closed by the publication audit. No claim of English-only completion is made from the preliminary Unicode count alone.
