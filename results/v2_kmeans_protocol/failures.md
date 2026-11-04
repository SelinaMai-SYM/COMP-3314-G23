# Failures and blocked cells

- UMIST sheffield564 SC RANDOM_MEAN50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SC RANDOM_BEST_INERTIA50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SC KMEANSPP_MEAN50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SC KMEANSPP_BEST_INERTIA50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SSC RANDOM_MEAN50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SSC RANDOM_BEST_INERTIA50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SSC KMEANSPP_MEAN50: BLOCKED_EXACT_SUBSET (n_trials=)
- UMIST sheffield564 SSC KMEANSPP_BEST_INERTIA50: BLOCKED_EXACT_SUBSET (n_trials=)
- AR paper840 SC RANDOM_MEAN50: BLOCKED (n_trials=)
- AR paper840 SC RANDOM_BEST_INERTIA50: BLOCKED (n_trials=)
- AR paper840 SC KMEANSPP_MEAN50: BLOCKED (n_trials=)
- AR paper840 SC KMEANSPP_BEST_INERTIA50: BLOCKED (n_trials=)
- AR paper840 SSC RANDOM_MEAN50: BLOCKED (n_trials=)
- AR paper840 SSC RANDOM_BEST_INERTIA50: BLOCKED (n_trials=)
- AR paper840 SSC KMEANSPP_MEAN50: BLOCKED (n_trials=)
- AR paper840 SSC KMEANSPP_BEST_INERTIA50: BLOCKED (n_trials=)
- MSRA50 paper1799 SC RANDOM_MEAN50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SC RANDOM_BEST_INERTIA50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SC KMEANSPP_MEAN50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SC KMEANSPP_BEST_INERTIA50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SSC RANDOM_MEAN50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SSC RANDOM_BEST_INERTIA50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SSC KMEANSPP_MEAN50: BLOCKED_DATA (n_trials=)
- MSRA50 paper1799 SSC KMEANSPP_BEST_INERTIA50: BLOCKED_DATA (n_trials=)

## Not run

- UMIST `sheffield564`: BLOCKED_EXACT_SUBSET. The paper's 564-image subset was not verified. No images were dropped using cluster accuracy.
- AR `paper840`: BLOCKED. The 840/120 subset is blocked. License, labels, and preprocessing are not jointly verified. The third-party 100-identity archive is not called AR.
- MSRA50 `paper1799`: BLOCKED_DATA. No legitimate 1799-image, 12-class archive is on disk. Status BLOCKED_DATA.
