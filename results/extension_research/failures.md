# Statuses that are not a completed numeric cell

Counts by status:

- `BLOCKED`: 1
- `BLOCKED_DATA`: 1
- `COMPLETE_SINGLE_ASSIGNMENT`: 14
- `CONVERGED`: 309
- `FAILED`: 3
- `NONCONVERGED`: 164

NONCONVERGED rows still contain the ACC/NMI of the returned G. They are not missing cells and they are not zeros.

| Dataset | Version | Method | Gamma | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| MSRA50 |  |  |  | BLOCKED_DATA | No 1799x12 archive. Excluded, not run. |
| AR |  |  |  | BLOCKED | Not called paper AR and not named AR100_ZENODO. Official Martinez images were not obtained. The third-party Zenodo zip is 100 identities, not 120, has no single paper preprocessing rule, and is not a licensed official redistribution. |
| ORL | att92 | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| ORL | att92 | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| JAFFE | zenodo | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| JAFFE | zenodo | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| YaleB | cropped2414 | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| YaleB | cropped2414 | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| YaleB | dengcai32 | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| YaleB | dengcai32 | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| USPS | libsvm | e06 | 1000000.0 | FAILED | FAILED TimeoutError: fit exceeded 180s |
| USPS | libsvm | e08 | 1000000.0 | FAILED | FAILED TimeoutError: fit exceeded 180s |
| USPS | libsvm | e09 | 1000000.0 | FAILED | FAILED TimeoutError: fit exceeded 180s |
| USPS | libsvm | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| USPS | libsvm | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| BinAlpha | CANDIDATE_BIN_ALPHA | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| BinAlpha | CANDIDATE_BIN_ALPHA | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| UMIST | precropped575 | E07-inertia_best | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
| UMIST | precropped575 | E07-consensus | 1.0 | COMPLETE_SINGLE_ASSIGNMENT | One assignment. inertia_best minimizes K-means inertia over the random seeds. consensus aligns those runs to that assignment and takes a majority vote. ACC is not the rule. Sample sd is blank because there is one selected assignment. |
