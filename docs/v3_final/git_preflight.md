> Historical record from an earlier campaign. The findings, validation counts and publication state below retain their recorded scope. Current evidence and remaining work are tracked in the [submission-refresh findings](../submission_refresh/research_findings.md) and [handover](../submission_refresh/final_handover.md).

# Git preflight

Recorded before any branch deletion. No branch was deleted. `v3` was not reset.

| Item | Value |
| --- | --- |
| Worktree | `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v3` |
| HEAD | `5355ee04d0b052d0a61ad5bbc7c50520b4058361` |
| Branch | `v3`, tracking `origin/v3`, up to date at audit time |
| `git ls-remote origin refs/heads/v3` | `5355ee04d0b052d0a61ad5bbc7c50520b4058361` |
| Other worktrees | `v1` at `e0ea8237d68f374047101d6d2ba5b76a68cbcb43`, `v2` at `c217836e7ca7bf5264399e8bb176522d7f721917` |
| Remote | `git@github.com:SelinaMai-SYM/COMP-3314-G23.git` |
| GitHub default branch | `v1` (public API; `gh` was not authenticated) |
| Protected branches | `v1`, `v2`, `v3` all `protected: false` |
| Open pull requests | none |
| Tags | none |
| Dirty at audit | `docs/v3/resource_probe.json` modified; untracked `baselines/ssc_resources/` and `runs/v3_reproduction/` |

## Backups

Created before further scientific commits. `git bundle verify` reported a complete history.

| Path | Bytes | SHA-256 |
| --- | --- | --- |
| `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/backups/comp3314-full-history-20261107_220551.bundle` | 47679744 | `a1bcd4891d3201348764941ee7d3c7f73c8fe99ded01382de0d8be239e980d3e` |
| `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/backups/v3-runs-reproduction-20261107_220551.tar.gz` | 32744626 | `87bde56bca258c2790a26c4dd56aa9f33196e7afd09ed89ebd4a77e302e8ff1d` |
| `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/backups/LOCAL_ONLY_private_pdfs-20261107_220551.tar.gz` | 1634056 | `2fc66acada68b01ca6e39715d212983b33ce84b5e05926471ad712db9852e1a1` |

The PDF archive is a local backup of publisher files. It is not committed and must not be pushed.

Bundle refs: `v1`, `v2`, `v3`, and the corresponding remote-tracking refs. The bundle contains the complete history of those refs.
