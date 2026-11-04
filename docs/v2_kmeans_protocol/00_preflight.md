# v2 preflight

The v2 worktree is `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v2`.
It was created from `origin/v1` at `e0ea8237d68f374047101d6d2ba5b76a68cbcb43` and the empty branch was pushed to `origin/v2` before any experiment code was added.

`DATA_ROOT` defaults to the sibling v1 worktree. Benchmark images stay there. The campaign refuses to write inside that directory and does not copy restricted images, credentials, or virtual environments.

The v1 branch and the v1 working directory are not modified by this campaign. Results are committed only on `v2`.
