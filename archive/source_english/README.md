# English source replacements, version 1

Each commit-named directory is an English replacement of a historical scientific source snapshot. Scientific formulas, numerical records, configurations, seeds, and identities are retained. Comments, generated prose, and documentation are translated where required. It is a source archive for inspection, not a current runtime dependency.

`TRANSFORMATION_MANIFEST.json` maps every original file to its replacement and records both SHA-256 values, including unchanged objects. The original scientific `SOURCE_MANIFEST.json` files also remain byte-exact at `../source/<original commit>/SOURCE_MANIFEST.json`. Their hashes describe original bytes and must not be interpreted as hashes of translated files. The copies inside these English directories likewise retain the original scientific manifest's identity.

Original bytes are preserved in project Git history and the verified external backup `refresh-20261110_055258Z/archive-originals`. Current rebuilds read committed scalar records and the retained identity manifests, without consulting old Git objects or an old checkout. Data and restricted publisher content remain outside these source archives.
