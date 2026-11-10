# Exact-commit isolated acceptance

Report prerequisites are `make`, `bash`, `mktemp`, `pdflatex`, `bibtex`, `pdfinfo`, `pdftotext`, `pdftoppm` and `pdftocairo` on the controlled PATH. The shell, temporary-directory and Poppler conversion tools are also needed when the two-graph figure is rebuilt.

`scripts/submission_refresh/acceptance.py` is prepared for the final validation slot. It has not yet been run. Use the existing shared validation scheduler so its CPU is charged to the campaign and it occupies one of the two worker slots. Both the scheduler task and the runner are capped at 900 CPU seconds and 1800 wall seconds; a cap or command failure is a failed/incomplete check, never a pass. No publication action is implemented.

The runner requires explicit `--repository`, `--branch`, `--expected-commit`, `--data-root` and `--output` arguments. `--expected-commit` is a full commit SHA, not a branch name. It verifies the actual cloned HEAD before installing anything and verifies that the committed acceptance script matches the script being executed. The output must be new or empty and external to the source and data directories; failed evidence is retained. The source commit must therefore include the prepared runner before acceptance starts. `--real-candidate-replay` explicitly enables the additional real-parent candidate integration check; leave it unset if those private parents are unavailable, and retain the resulting NOT_REQUESTED status.

For the candidate, use the local repository as the clone source with the actual current candidate branch and its committed SHA:

```bash
python scripts/submission_refresh/acceptance.py \
  --repository "/absolute/path/to/committed candidate" \
  --branch CANDIDATE_BRANCH \
  --expected-commit FULL_COMMITTED_SHA \
  --data-root "/absolute/path/to/independent-data/benchmarks" \
  --output "/external/validation/candidate acceptance"
```

After the separate publication and branch-rename checks, use the real HTTPS repository, `--branch main`, and the exact final commit. An observed different tip causes failure; the runner never resets a clone to make it look like the expected tip:

```bash
python scripts/submission_refresh/acceptance.py \
  --repository https://github.com/SelinaMai-SYM/COMP-3314-G23.git \
  --branch main \
  --expected-commit FULL_PUBLISHED_SHA \
  --data-root "/absolute/path/to/independent-data/benchmarks" \
  --output "/external/validation/published acceptance"
```

These examples are argument templates, not a record of executed commands. In a scheduler `validation` task, use an argv list beginning with `{python}`, `{repo_root}/scripts/submission_refresh/acceptance.py`; `{data_root}` and a new subdirectory of `{validation_dir}` are supported by the existing wrapper. Set the task's `cpu_limit` to 900 and `wall_limit` to 1800, without starting another worker pool.

The runner creates a shallow single-branch clone using `--no-local`, a new virtual environment, and output paths containing spaces. For a local repository path, `--no-local` selects normal Git transport so `--depth 1` is honored; the runner then verifies the clone is shallow and has no object alternates. It clears inherited Python/data-root and pip target overrides, disables user-site imports, fixes BLAS/OpenMP threads at one and installs the pinned dependency file with TLS verification enabled. It installs only its own checkout with `--no-deps -e`, records a dependency freeze and checks imported project module locations. No local data pointer or source symlinks to an old checkout are accepted. The independent data path is supplied only to the later real-data smoke.

The inherited COMP3314_ARTIFACT_ROOT is removed too; no-data stages assert that both data and artifact overrides are absent. They cannot silently write source archives into the campaign's original shared store. Process monitoring and cleanup use an absolute system `ps` resolved from the controlled PATH and the same sanitized environment as the checked commands.

Inherited Git repository/object redirections are cleared: GIT_DIR, GIT_WORK_TREE, GIT_COMMON_DIR, GIT_INDEX_FILE, GIT_OBJECT_DIRECTORY, GIT_ALTERNATE_OBJECT_DIRECTORIES, GIT_SHALLOW_FILE and GIT_NAMESPACE. The runner also removes GIT_SSL_NO_VERIFY, GIT_CONFIG_COUNT, GIT_CONFIG_PARAMETERS and every inherited GIT_CONFIG_KEY_* / GIT_CONFIG_VALUE_* entry. `acceptance.json` distinguishes the clearing policy from the actual removed key names, including dynamic entries; it never records injected configuration values. The clone uses command-local `git -c http.sslVerify=true`. Valid GIT_SSL_CAINFO/GIT_SSL_CAPATH overrides remain available, and no global Git configuration is changed.

After installing the fresh environment, the runner reuses the actual pytest selection from `configs/submission_refresh/revalidation_v4_queue.json`, task `validation-focused-tests-v4`, changing only its JUnit output to `acceptance outputs/focused-regressions.xml`. This covers the submission-refresh and next-round directories plus the selected v3 and baseline regressions. Neither PYTHONPATH nor COMP3314_DATA_ROOT is set. The only allowed skip is the explicit candidate-data integration test requiring COMP3314_DATA_ROOT; missing CVXPY or skipped backend convex-reference tests fail acceptance. Actual testcase pass/failure/error/skip counts and reasons come from JUnit, including when pytest exits unsuccessfully; no previous pass count is assumed.

Further checks cover synthetic execution, historical scalar rebuilding, joint historical rebuilding, current subset rebuilding, current baseline/graph scalar rebuilding, deterministic published CSV parity and the eight subset Markdown tables. The real-data smoke loads ORL, JAFFE and all 1799 native 16-by-16 MSRA rows; three rounding seeds are an execution check, not a new reproduction endpoint. Missing final release manifests or authoritative tables fail acceptance rather than being skipped. If requested, the real-candidate replay runs `tests/submission_refresh/test_candidates.py` after these no-data stages and the real smoke, sets COMP3314_DATA_ROOT only inside that child Python process, records its actual JUnit counts and requires the integration test to execute without skips. This does not change the parent environment or any no-data command.

Report checks compile the preprint, check the four author identities and preserve the two-graph source. `references_start` follows the main `clearpage` and precedes the bibliography. Its compiled page minus one counts every main page, including pending floats flushed by that clearpage; this value must be at most four. `main_end` must fall within those pages, with valid source ordering of both labels, clearpage, bibliography and appendix. The parser accepts ordinary and hyperref label records with balanced nested braces and rejects missing/duplicate/nonnumeric labels. References remain excluded; the unique PDF-text appendix boundary is checked separately. Thus a body ending on page four with a main float on page five fails even when references start on page six. The runner also checks undefined references/citations and PDF text flags, compares regenerated table sources, and renders every PDF page. **Visual review, natural-English review, external/live links, sole remote head/default branch and publication remain separate checks.** The runner explicitly leaves visual review unapproved.

Before compiling, the runner verifies the committed `Group_23.pdf` still has its checkout inventory hash and extracts it with `pdftotext -layout` to `acceptance outputs/committed-report-text.txt`. It extracts regenerated text with the same command and requires case-sensitive equality after whitespace normalization, recording both text hashes. A stale committed PDF therefore fails even if current sources compile. Differences only in PDF binary metadata remain allowed; the root workflow still visually inspects every page of the committed final PDF.

`acceptance.json` records every argv/cwd/exit, command-log hash, observed commit, checks, CPU/wall cost and sampled process-tree memory. `source_inventory.json`, `tested-environment.txt`, installed package/module records, rebuild products, report text and page PNGs are preserved beside it. Command failures and timeouts retain evidence. A successful computational acceptance is tied to the recorded actual commit; a later documentation-only audit commit must be identified and reviewed separately.
