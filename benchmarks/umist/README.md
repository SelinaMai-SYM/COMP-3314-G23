# UMIST

Status: `unavailable`

Chang et al., AAAI 2015, state 564 images of 20 individuals (Graham and Allinson, 1998). `load_dataset("UMIST")` still raises `DatasetUnavailable` because no saved archive has 564 images. Later the same day, Wayback copies of the old UMIST `face.tar.gz` (1012 unique PGM files) and `cropped.tar.gz` (575 images) were saved, plus a Figshare mat that is also 575 slices and not pixel-identical to the cropped tar. `version="precropped575"` loads the 575-image cropped tar. See `manifest_wayback.yaml`, `manifest_figshare_cropped.yaml`, and `docs/repair_round1_dataset_recovery.md`.

Attempted on 2026-10-20:

- `http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` HTTP 202
- `https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` HTTP 202, WAF HTML
- `https://www.sheffield.ac.uk/eee/research/iel/research/face` HTTP 404
- `http://images.ee.umist.ac.uk/danny/database.html` HTTP 502

`load_dataset()` with no version still raises `DatasetUnavailable`. The 575-image files are not treated as the 564-image set. See `manifest.yaml` for the earlier failed attempts.
