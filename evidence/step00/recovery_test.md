# STEP 00 — Recovery Test

Audit mode: remote GitHub evidence audit  
Audited main HEAD: `350e5428afe8ec435f52f12189faf7ef0e9b4ea0`

## 1. Canonical UI Reference Recovery Package

Package:

`docs/UI_REFERENCE_PACKAGE_V1/Prompt-Action-UI-Reference-Materialized-V1.zip`

Observed size: `125042` bytes.

Companion checksum:

`2797cf5993ba6e38532d028135f5f8ab12f99bc55ed0b643b441e57ca5eeebb0`

Evidence from the successful `Materialize UI Reference Package` workflow proves that:

- the five Base64 image inputs were decoded;
- all five outputs were recognized as JPEG image data;
- all five materialized images were reported as `320x180`;
- two generated DOCX files were validated as ZIP/DOCX containers containing `word/document.xml`;
- the materialized ZIP was generated from the materialized reference directory;
- SHA256 was computed as the value above;
- the generated package/checksum was committed successfully.

### Result

`PASS_FOR_CLAIMED_UI_REFERENCE_SCOPE`

This package is accepted only as the canonical **UI reference recovery package**. It is not evidence of a complete Prompt Action application/source recovery.

## 2. Old UI Reference Package

Package:

`docs/UI_REFERENCE_PACKAGE_V1/Prompt-Action-UI-Reference-Package-V1.zip`

The canonical README explicitly classifies this as an old experimental artifact and identifies the Materialized V1 package as canonical.

### Result

`EXCLUDE_FROM_BASELINE`

Preserve as history/evidence; do not use as the active recovery baseline.

## 3. zz_BOOTSTRAP

Observed files:

- `zz_BOOTSTRAP/chunks/part001.b64`
- `zz_BOOTSTRAP/chunks/part002.b64`
- `zz_BOOTSTRAP/chunks/part003.b64`

The chunks exist and are preserved. However this remote audit could not prove all of the following from the actual decoded archive:

- exact package filename/boundary;
- canonical SHA256 of the reconstructed package;
- complete extract into an empty staging directory;
- complete internal file listing;
- presence of Legacy V22.5.1 source;
- presence of all eight required Prompt 1A–5 files;
- exact parent/version provenance of those prompt files.

### Result

`VERSION_UNKNOWN / EVIDENCE_ONLY`

Not sufficient to satisfy the Legacy or eight-prompt blocking gate.

## 4. zz_REBUILD

Observed files:

- `zz_REBUILD/chunks/part001.b64`
- `part002.b64`
- `part003.b64`
- `part004.b64`
- `part005.b64`
- `part006.b64`
- `part007.b64`
- `part008.b64`
- `part009.b64`

Git history contains commits named `Upload GitHub snapshot chunk 001` through `009`. This proves the chunks are intentional recovery evidence, but not the required source provenance.

One inspected chunk begins with Base64 data corresponding to a ZIP stream and exposes historical package paths such as changelog/version-control files. That alone is insufficient to promote the entire reconstructed archive to `VERIFIED_SOURCE` or `VERIFIED_RESCUE_ZIP`.

A full byte-accurate concatenate/decode/hash/extract test was not available in this remote-only execution channel. Therefore required Prompt 1A–5 and V22.5.1 cannot be declared present merely because these chunks exist.

### Result

`VERSION_UNKNOWN / EVIDENCE_ONLY`

## 5. Full Prompt Action Recovery Gate

Required scope for STEP 00 includes:

- verified Legacy V22.5.1 source/recovery;
- Prompt 1A;
- Prompt 1B;
- Prompt 1B1;
- Prompt 1B2;
- Prompt 2;
- Prompt 3;
- Prompt 4;
- Prompt 5;
- a recovery package whose actual extracted contents prove the scope claimed.

That full scope is not verified in the audited HEAD.

### Final recovery result

`BLOCKED`

The UI-reference recovery package passes its own limited scope. Full Prompt Action recovery does **not** pass STEP 00.

## 6. Safety conclusion

No recovery chunk, package, workflow, UI image, legacy marker, or source document was edited or deleted during this audit. Missing prompt files were not regenerated from documentation or assumptions.
