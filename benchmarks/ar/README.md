# AR

Status: `unavailable`

Chang et al., AAAI 2015, state 840 faces of 120 people. The AR Face Database (Martinez and Benavente, CVC Technical Report 24, 1998) requires a university-email request and a password. Those credentials were not obtained.

Attempted on 2026-10-20; no image archive was saved:

- `http://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` HTTP 503
- `https://www2.ece.ohio-state.edu/~aleix/ARdatabase.html` no origin status through the proxy
- `https://engineering.purdue.edu/~aleix/ARdatabase.html` HTTP 404
- NIST catalog `https://tsapps.nist.gov/BDbC/Search/Details/301` HTTP 200, catalog only

`load_dataset` raises `DatasetUnavailable`. No data files were fabricated. See `manifest.yaml`.
