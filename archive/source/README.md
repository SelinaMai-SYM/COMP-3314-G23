# Historical scientific source identities

The two byte-exact `SOURCE_MANIFEST.json` files identify the scientific source versions associated with the historical statistical release. Their hashes describe the original source bytes. They are provenance records rather than current import packages.

Current implementations are in the repository's source packages. Published table reconstruction uses committed scalar records and these lightweight manifests, without reading old Git objects. The complete original source snapshots and versioned English transformations are preserved with the recoverable scientific archive described in [reproducibility](../../docs/reproducibility.md). Source identity and numerical agreement are separate qualifications.
