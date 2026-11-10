# Verified CSV transport

Large scalar CSVs use deterministic gzip transport to stay within repository
file-size limits. Compression preserves every logical CSV byte, including row
order, source identities, settings, metric serialization and selected IDs. It
does not change the cohort, fitting, selection, winner lock or seed namespace.
The implementation is standard-library-only and can be loaded by the isolated
acceptance harness before project installation.

`experiments.submission_refresh.csv_transport` provides:

- `resolve_csv(path, required=False)`: return the sole plain `.csv` or gzip
  `.csv.gz` path; return `None` only when an optional input is absent. Both
  representations, invalid existing paths and missing required inputs fail.
- `open_csv(path, mode='rt', newline='')`: transparently read UTF-8 CSV text.
  It accepts only read modes and never falls back after a corrupt plain input.
- `copy_plain_csv(source, destination)`: validate and atomically materialize the
  exact uncompressed bytes. A corrupt source cannot replace the destination.
- `pack_large_csvs(directory, min_bytes=90*1024**2, names=None)`: validate all
  selected inputs, stage deterministic gzip with no timestamp or source filename,
  verify decompressed SHA/length/structure, then publish without overwriting an
  existing transport. Existing gzip files are verified and inventoried. `names`
  restricts work to safe basenames; it does not change CSV contents.

Packing returns records with relative `csv_path` and `transport_path`, status,
uncompressed SHA/byte length, compressed SHA/byte length when applicable, and
row/column counts. Empty bodies, malformed rows, invalid UTF-8, gzip corruption,
ambiguous representations and independently changed sources fail before staged
packing is published. Packing never interprets metric values. Hashes for existing
gzip files describe the verified bytes; authoritative release manifests still
provide the expected hashes against which readers validate them.

The current scalar release resolves gzip joint summaries and optional CSV inputs.
It stages and compresses a large configuration inventory before freezing its
manifest. That manifest records the actual transport path, compressed file hash
and size, and uncompressed hash. Rebuild verifies both hashes and materializes
ordinary CSV outputs in its separate output directory. The existing source-record
JSON gzip and raw-trial release formats are unchanged.

Finalization order is: pack selected optional CSV inputs; freeze the inventory
and manifest; rebuild and publish canonical derived views; then pack large derived
CSV views that are not manifest inputs. Do not repack a hash-locked input after
freezing it. Protected inputs must be recognized by both their actual compressed
paths and logical CSV names when publishing derived views. Before committing,
check actual generated file sizes, including gzip files; a placeholder-metric
estimate does not establish the compression ratio of real trials.

Focused transport/release regression fixtures are prepared. Their execution and
the final fresh-checkout acceptance remain separately recorded validation steps.
