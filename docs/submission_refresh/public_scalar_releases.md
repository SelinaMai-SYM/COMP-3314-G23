# Public scalar releases and archival provenance

Public release adapters preserve scientific configuration IDs, source identities,
trial values, selected endpoints, failure outcomes and the frozen confirmation
seed block. Original records remain in a separately verified private archive.
Public payload hashes describe projected bytes and are never presented as hashes
of the original records.

The current source registry uses `public-scientific-source-records-v1`. Each key
is the original source-record identity; its entry contains
`original_record_sha256`, `public_record_sha256` and the whitelisted public
`record`. Code hashes, implementation/cache identities, dependency versions and
controller mappings remain available. Workstation paths, source bodies, commands,
dirty-state flags and thread-library filenames are excluded. The loader supports
both this registry and the earlier complete source-record registry. Actual source
identity uses the file/implementation hashes and archived source bytes; a commit
identifier alone does not assert byte identity of every observed source file.

`current_release.project_existing_release(output, manifest_path=None,
archive_receipt=...)` requires the verified archive/recovery receipt covering the
exact original source registry and release manifest. It creates versioned public
source/coverage/completion/resource/artifact envelopes and an original-to-public
hash receipt, then updates the release manifest atomically. It leaves original
files intact for explicit archival cleanup. Every completed, failed, timed-out
or unrun configuration remains represented; reason codes and numerical failure
diagnostics remain distinct from private tracebacks and scheduler bookkeeping.
Raw trials and configuration inventories are unchanged.

Confirmation provenance has two explicit steps. Immediately after confirmation,
before presentation canonicalization, call
`confirmation_public.prepare_seed_inventory_proof(artifact_root, output)`.
It verifies the exact original historical source hashes and seed-column
inventories, and records the full observed seed set privately at
`confirmation/seed_inventory_proof.v1.json`. Exact source-file bytes are copied
once per SHA-256 into `confirmation/historical_seed_sources/<sha>.bin`; their
original paths and formats occur only in the private preparation. The byte-link
descriptors use `relative_path`, `sha256`, `bytes` and `original_format`, rather
than impersonating scientific CAS objects. Include this preparation, the byte
copies and the
original namespace in the verified private archive.

After archive recovery is verified, call
`confirmation_public.project_confirmation_namespace(artifact_root, output,
archive_receipt=...)`, then project the current release. The version-3 public
namespace references a hash-locked public seed proof containing the complete
historical seed set, original inventory/namespace/preparation hashes, immutable
winner-lock hash and unchanged first-unused 50-seed block. It omits the private
raw-source path inventory. Resume verifies that proof without requiring removed
run directories or selecting a new block. Original namespace bytes are retained
privately under a filename containing their SHA-256.

The archive receipt is a public-safe descriptor with an opaque archive ID,
archive/recovery hashes and verified counts. It contains no machine paths or
commands. Fresh no-data rebuilds need only committed public release inputs;
recovering scientific matrices separately requires the matching archive and its
data access rights. The nine historical release inputs remain byte-identical;
they require no public-path transformation.
