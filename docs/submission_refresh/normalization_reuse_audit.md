# Normalization and repeated SC evidence: metadata-only audit

Audit completed at **2026-11-10T11:30:20+00:00**, after the cited G2 records were already present and marked COMPLETED. This is a retrospective overlap check, not a claim that reuse screening preceded G2 execution. Only saved JSON records, scalar trial values and content-reference descriptors were read. No matrix objects were opened, no fit/evaluator ran, and no new rounding trials or code edits were made.

`ARTIFACT_ROOT` below is the recoverable external `independent-data/scientific-artifacts/refresh-20261110` store. Matching recorded content references establish identity of the referenced objects; this audit did not independently reopen or hash their array files.

## Finding

The current bilinear cropped YaleB **Y2 matched SC is the same fixed normalized representation and same 50-seed SC evidence as G2 U/gamma=0**. Its X/y references match the current Y0 input; its final F reference exactly matches the saved U anchor, and its prediction reference, each paired ACC/NMI value, and each inertia match all 50 greedy seeds. Y0 matched SC likewise matches G2 F0/gamma=0. These repeated controls are not independent repeatability batches and must not be pooled as 100 trials or treated as independent replications.

Y3 is different: it normalizes the input rows as well as the embedding. Its X, A, F and prediction references differ from the Y0/U path, despite matching stored y bytes. Nearest/bicubic resize variants and DengCai32 also have different X/F references. None can replace this preregistered Y0-input U control merely because it shares a normalization label or has a more favorable score. Matching labels alone do not prove cross-source pixel or row identity.

## Exact comparisons

Every compared record has exactly seeds 0..49, greedy K-means++, one Lloyd start. Y0 is compared with G2 F0; all Y2/Y3 rows are compared with G2 U. “Identical pairs” means exact equality of the stored unit-interval ACC and NMI for each seed, not a fresh evaluation.

| Current subset candidate | G2 anchor | Same X ref | Same y ref | Same final F / anchor ref | Same prediction ref | Identical ACC/NMI pairs | Identical inertia |
|---|---|---|---|---|---|---:|---:|
| YaleB_cropped2414_Y0 | F0 | yes | yes | yes | yes | 50/50 | 50/50 |
| YaleB_cropped2414_Y2 | U | yes | yes | yes | yes | 50/50 | 50/50 |
| YaleB_cropped2414_Y3 | U | no | yes | no | no | 0/50 | 0/50 |
| YaleB_cropped2414_nearest_Y2 | U | no | yes | no | no | 0/50 | 0/50 |
| YaleB_cropped2414_nearest_Y3 | U | no | yes | no | no | 0/50 | 0/50 |
| YaleB_cropped2414_bicubic_Y2 | U | no | yes | no | no | 0/50 | 0/50 |
| YaleB_cropped2414_bicubic_Y3 | U | no | yes | no | no | 0/50 | 0/50 |
| YaleB_dengcai32_Y2 | U | no | yes | no | no | 0/50 | 0/50 |
| YaleB_dengcai32_Y3 | U | no | yes | no | no | 0/50 | 0/50 |

The stored Y2/U summaries are ACC **25.797017% +/- 0.709344** and NMI **32.594770% +/- 0.434998** (sample SD, n=50). The stored Y0/F0 summaries are ACC **21.781276% +/- 0.454097** and NMI **27.730870% +/- 0.584830**. These are summaries of the same matched records described above, not additional measurements.

## Object and protocol evidence

| Object | Recorded SHA256 |
|---|---|
| Y0 X = Y2 X = graph input X | `1d6512afd8396f0e7dc38c5bc34e90d9e33e18e645349bb16a68eae337e19c1d` |
| Stored y across these records | `f091ef69d1de9d62cdbf79cb926ccae5c624f386681259dd56123764c45c76e7` |
| Y0 F = graph input F0 | `fcb84ae35d417fd0547f2b4d32c05d9d7f2897a371642868c74e89ff52c941f6` |
| Y2 F = graph input U = G2 U anchor | `e2180917e72a402dbc6c9d6a28052ef96b308e60a6d95cdf11eab6ee7a922578` |
| Y2 SC = G2 U predictions | `cecf2c4ac40594f22d2ebc774503afafbe02a034a0ca321cee0c07021b8c0773` |
| Y3 X (different) | `082e2164be009f7a4b1784c4d03bc92c3e68004d10f3dc0a7b19675fdf7c427d` |
| Y3 F (different) | `2002c19eccc46f19c5f7a3057d115753c8451c4247dcac608baa26231c6e308d` |

The Y0 spectral-info dictionary exactly matches the current graph input metadata: symmetric normalized Equation 4, k=5, union maximum, median positive directed-neighbor squared-distance bandwidth, smallest eigenspace, deterministic sign convention and the same recorded eigenvalues. Input A references match. Y2 applies its declared row normalization after that spectral step; the initial spectral-info `row_normalize=false` field does not erase the separately recorded Y2 factor. Its W is rebuilt on normalized F and differs from Y0 W.

The subset source records carry the unchanged protocol SHA `339bc600672ff04c7fdbb74e49ee596178ffa55b3df518cb8621cc131ed3ea28`, matching current `configs/subset_search/protocol.yaml`. The recorded environments match G2. The G2 construction uses the same k=5 spectral/graph path and 50 greedy seeds 0..49; at gamma=0 graph-arm weights do not change the SC objective. G2 U/W0 and U/Wa retain the same prediction reference and identical complete trial dictionaries; their `SC_graph_arm_alias` markers identify graph-arm aliases.

G2 reports ANALYTIC_G_EQUALS_F, certified=true, relative gap=0, edge/node violations=0 and zero recorded movement. Its saved returned-G reference (`b9ed0aac25b24f230486bcd642b2cf6502f19ce20829794413e5fdf4ca47fc60`) differs from its saved anchor reference. I did not decode arrays to attribute that serialization/reference difference. The exact shared anchor and prediction references, plus the 50 identical scalar pairs, establish the reporting overlap without inventing an array-level explanation or a new certificate.

## Source qualification

The subset Y0/Y2 records identify source commit `02534e713839554b1a5dadd7236980bf3c5a3f86`; Y3 identifies `e7bcd82b1c4b89d6efcc206f5eb07174d0aa6e4a`. G2 identifies `1702ffd9b2056bedfb3b2e8d5cfc46dc779ae42e` and graph-scientific fingerprint `2ed5b6fb520753cd8a339744ed4c787b6efa630ec77d554f1637a5d110eaccbb`. Their whole-source fingerprint scopes differ and are not equated.

| Shared implementation evidence | Status |
|---|---|
| `SSC_method/graph_construction.py` | matching recorded hashes |
| `SSC_method/spectral_embedding.py` | matching recorded hashes |
| `SSC_method/spectral_config.py` | matching recorded hashes |
| `experiments/subset_search/runner.py` | matching recorded hashes |
| `experiments/v2_kmeans_protocol/kmeans_trials.py` | subset hash not recorded; equality not established |
| `experiments/v2_kmeans_protocol/metrics.py` | subset hash not recorded; equality not established |

The absent subset v2-file hashes are a provenance omission, not proof of a code change. This audit records the exact saved output overlap and the available matching source hashes; it does not retrofit missing provenance or declare every historical/current execution cache interchangeable.

## Limits on reuse

- Reuse these matching current SC controls as the same fixed-input, fixed-seed evidence; retain their original purposes and execution costs. Do not present repeated executions as independent batches.
- Finite-iteration E8/E13 IRLS G outputs remain their original historical-style search results. They cannot replace certified PDHG G2/G3 targets. Nonzero-gamma reuse would require the same anchor, exact graph/weight mass, effective gamma/objective, all parameters and source/certificate context; matching preparation names or ACC/NMI is insufficient.
- Y3 and source/resize alternatives remain separate sensitivity configurations.
- Earlier historical Y2 records whose F was not saved remain distinct. No exact embedding identity is established for those records, and this current recoverable overlap must not be projected backward onto them.

## Metadata record identities

- Graph input: `graph_inputs/YaleB_cropped2414/5d150a617d9e9b424666eb43aa9700d0c6caba7da08079a0136cc0890bfd5e4e/representation.json`; JSON SHA `83a2485e9097e4935631afd3341e1904915d73da21879c75f8bbe44d4ea6c6ab`.
- G2 U/W0/gamma0: `graph_records/YaleB_cropped2414/5d150a617d9e9b424666eb43aa9700d0c6caba7da08079a0136cc0890bfd5e4e/G2__U__W0__0.json`; JSON SHA `60c5b876e797198d0b08361eb7726d84e662cbebf96b12eec3bf6c1aa2e0c33f`.
- G2 F0/W0/gamma0: `graph_records/YaleB_cropped2414/5d150a617d9e9b424666eb43aa9700d0c6caba7da08079a0136cc0890bfd5e4e/G2__F0__W0__0.json`; JSON SHA `8407b799ee86e28acde39070de7d3457ec179eda4abebb83b3467e7bf2d00a7f`.

For each current subset row, paths are `subset/<candidate>/representation.json` and `subset/<candidate>/SC__SKLEARN_GREEDY_KMEANSPP.json` under ARTIFACT_ROOT.

| Candidate | Representation JSON SHA256 | Greedy SC JSON SHA256 |
|---|---|---|
| YaleB_cropped2414_Y0 | `5fbd798b3e4a4f3c5f781f8231b776e59bf047ee592d84727015861239682707` | `d86238c67d865099b71c1d35445c7174b26fb615593acdb89054e3c97ad0c5cd` |
| YaleB_cropped2414_Y2 | `41d3dd1f6628e6069d8d4b6fb7046c9b49e793237b9db1d8c5941a0ff9b18c3a` | `326c953b91b5dc2b26edc93af128c87773bf0f4c3efeafac78eb587b2a068b07` |
| YaleB_cropped2414_Y3 | `d02916b7a3282ae5fbed4f26670332bdcc30fddc0c049ce411c2369576241286` | `4974a49e84156861f5fdebed56cc35ae9836bf740ed79576fd9c79a04afd52cd` |
| YaleB_cropped2414_nearest_Y2 | `e14b02b3b6a1fffbe5c5a8dcf9579e4d5be72b18a50eee94d6867add5243d9e9` | `3604f31d64b48c4c0136118483be41efd439025c9ed321b189b8c150b660aadf` |
| YaleB_cropped2414_nearest_Y3 | `fbc2ca34d85074bcca3a84cda4dae85491f4352b44e6a67eb7ad948a3cc69e9a` | `9b81c0560a7a8a2665a210c6b8227ac7f337e90484b3f275f921ddb302b1c6bb` |
| YaleB_cropped2414_bicubic_Y2 | `84b8477fcc86bb9714d0da730acb933361bab2bfb0a07a602375d078179da56d` | `74b99fa6572558acce9eeadfc970e9cc695949a86de4e568144074d8b6195289` |
| YaleB_cropped2414_bicubic_Y3 | `a302134b7e3bfaa2f4d1017a0ad40640d0f675bbad4950a858c507362009bdd7` | `dde175fe083067ace052aa03a46d9f637323e76e9fc7a02740b27630a2398d8e` |
| YaleB_dengcai32_Y2 | `34f576c4927990463b4d06d5593c959f8b44cda4adcd941062cbe2e78c659b6d` | `21b9e1353951c96e77da18234a3d5b2894f3bdbbe3d193660e569e8c6150e8ca` |
| YaleB_dengcai32_Y3 | `61766c503b027a92d1c04a44e877386d15ad6689bab1f7592b7b128e8f557697` | `953633236a42610cbd7058e94435ede81fb425df9d6f207e79d6eef5900de3b2` |
