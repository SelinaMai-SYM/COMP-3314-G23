# Scientific source identities

The two original scientific versions retain their exact `SOURCE_MANIFEST.json` files under their original commit names. These manifests identify original source bytes; translated files have different identities. Original bytes remain recoverable in Git history and the verified external bundle/backup. Current rebuilds use the committed manifests and scalar records and do not read old Git objects.

Versioned [English replacements](../source_english) preserve source, configuration, and dependency records for inspection. The [transformation manifest](../source_english/TRANSFORMATION_MANIFEST.json) maps every original file hash to its English replacement hash, including unchanged files. Source snapshots are provenance material, never current imports. Data and restricted full text are excluded; public availability does not establish a redistribution license.
