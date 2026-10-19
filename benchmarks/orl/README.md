# ORL

Status: `approximate`

Source: figshare 5976027, `olivettifaces.mat` (AT&T Cambridge / Olivetti, 64×64). Chang et al., AAAI 2015, resize to 32×32.

Raw archive: `data/olivettifaces.mat` (gitignored). SHA-256 `b612fb967f2dc77c9c62d3e1266e0c73d5fca46a4b8906c18e454d41af987794`.

This is a 64×64 Olivetti matrix resized to 32×32, not a sample-level identity with a 92×112 ORL release. See `manifest.yaml`.

The AT&T 92×112 PGM zip is a separate version. `load_dataset("ORL")` does not load it. Use `load_dataset("ORL", version="att92")`, `version="att92_nearest"`, or `version="att92_bicubic"`. Files are under `data/att92/` and are gitignored. See `manifest_att92.yaml`.
