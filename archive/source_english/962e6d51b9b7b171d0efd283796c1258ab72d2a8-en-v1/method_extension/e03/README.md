# E03 — where a local scale is used

Zelnik-Manor local scale is an existing affinity rule already implemented for diagnostics. It is not given a new method name here. The extension is the placement:

- E03-A uses it only to build the Laplacian on X, then builds W with the median rule and runs E8. F changes, so the paired spectral clustering changes too.
- E03-W keeps the control F and uses local scale only for W.
- E03-AW uses local scale for both, in that one configuration.

The three runs are recorded separately. They are not three extra research methods beyond E03, and they are not chosen by test ACC.
