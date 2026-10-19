# YaleB

Status: `approximate`

Source: Deng Cai's `YaleB_32x32.mat` (Georghiades, Belhumeur, and Kriegman, TPAMI 2001; cropped description Lee, Ho, and Kriegman, TPAMI 2005). Chang et al., AAAI 2015, state 2414 near-frontal images, 38 people, resized to 32×32.

Raw archive: `data/YaleB_32x32.mat` (gitignored). SHA-256 `3fbbda4eb781b9bb28025189677b6727706e114eb0215bbfd718f1f4fcb54b99`.

The live UCSD cropped PGM zip returned HTTP 404 on 2026-10-20. A Wayback capture of that zip is a separate version: `load_dataset("YaleB", version="cropped2414")`. `load_dataset("YaleB")` still returns this mat. See `manifest_cropped.yaml` and `docs/repair_round1_dataset_recovery.md`.
