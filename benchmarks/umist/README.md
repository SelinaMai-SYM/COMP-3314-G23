# UMIST

Status: `unavailable`

Chang et al., AAAI 2015, state 564 images of 20 individuals (Graham and Allinson, 1998). Lincoln eprints returned an AWS WAF challenge; older homepages failed. No tar was saved.

Attempted on 2026-10-20:

- `http://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` HTTP 202
- `https://eprints.lincoln.ac.uk/id/eprint/16081/1/face.tar.gz` HTTP 202, WAF HTML
- `https://www.sheffield.ac.uk/eee/research/iel/research/face` HTTP 404
- `http://images.ee.umist.ac.uk/danny/database.html` HTTP 502

`load_dataset` raises `DatasetUnavailable`. A different cropped UMIST matrix was not substituted. See `manifest.yaml`.
