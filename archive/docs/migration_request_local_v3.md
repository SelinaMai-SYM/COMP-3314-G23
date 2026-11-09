# Git migration approval request

Branch deletion awaits approval. No remote branch was deleted. The GitHub default branch was not changed. Existing `v3` history was not replaced and was not force-pushed.

## State at this request

| Item | Value |
| --- | --- |
| Workspace | `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v3` |
| Branch | `v3` |
| `v3` commit at the preflight audit | `5355ee04d0b052d0a61ad5bbc7c50520b4058361` |
| `v3` commit after the scientific push | `3c0cd6ca0bda454ff622c9c3c450541c92eb4cca` |
| Remote | `git@github.com:SelinaMai-SYM/COMP-3314-G23.git` |
| GitHub default branch | `v1` |
| Protected branches | `v1`, `v2`, and `v3` are all `protected: false` |
| Open pull requests | none |
| Tags | none |
| Other worktrees | `v1` `e0ea8237d68f374047101d6d2ba5b76a68cbcb43`, `v2` `c217836e7ca7bf5264399e8bb176522d7f721917` |
| Full-history bundle | `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/backups/comp3314-full-history-20261107_220551.bundle` |
| Bundle size | 47679744 bytes |
| Bundle SHA-256 | `a1bcd4891d3201348764941ee7d3c7f73c8fe99ded01382de0d8be239e980d3e` |
| `git bundle verify` | complete history |
| Runs snapshot | `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/backups/v3-runs-reproduction-20261107_220551.tar.gz` |
| Runs SHA-256 | `87bde56bca258c2790a26c4dd56aa9f33196e7afd09ed89ebd4a77e302e8ff1d` |
| Local-only PDF archive | `/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/backups/LOCAL_ONLY_private_pdfs-20261107_220551.tar.gz` |
| PDF archive SHA-256 | `2fc66acada68b01ca6e39715d212983b33ce84b5e05926471ad712db9852e1a1` |
| Independent candidate branch | `v3-independent-candidate` |
| Candidate commit | `95d599918627379b21f665b9b2754dd3852dc6dc` |
| Candidate parents | none (`git rev-parse HEAD^` failed; `git rev-list --count` was 1) |
| Candidate tree | `dc63a902f8bba2acb241e34029609fb4cc1e6b7a`, equal to the tree of `3c0cd6c` |
| Candidate push | new branch, not a force update of `v3` |

The PDF archive stays outside Git. It must not be committed.

## Branches proposed for deletion

None. A later approval would have to name each branch. This document does not authorize deletion of `v1`, `v2`, or `v3`.

## Default branch

Leave the default branch at `v1`. Changing it is a separate approval.

## Commands that were not run

```bash
git push origin --delete v1
git push origin --delete v2
git push --force origin v3
git push --force-with-lease origin v3
gh api -X PATCH repos/SelinaMai-SYM/COMP-3314-G23 -f default_branch=v3
```

## Orphan snapshot

The commands below were run in `/tmp/v3-independent-candidate`, not in the `v3` worktree. The push created a new branch. `v3` stayed at `3c0cd6ca0bda454ff622c9c3c450541c92eb4cca`. This follow-up note is a later commit on `v3`, so the candidate tree matches `3c0cd6c` and does not contain this paragraph.

```bash
SOURCE=$(git -C "/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v3" rev-parse HEAD)
rm -rf "/tmp/v3-independent-candidate"
git clone --branch v3 "/Users/grantwright/Desktop/COMP 3314/COMP 3314 GP/v3" /tmp/v3-independent-candidate
cd /tmp/v3-independent-candidate
git checkout --orphan v3-independent-candidate
git commit -m "Snapshot of v3 ${SOURCE} with no parents. Source hashes stay in docs/v3_final/source_provenance.csv."
test -z "$(git rev-parse --verify HEAD^)"
git push origin HEAD:v3-independent-candidate
```

If that push is rejected, leave the candidate unpushed. Do not force-push.
