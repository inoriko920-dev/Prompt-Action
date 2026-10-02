# STEP 00 — Conflict Register

## C-001 — Version marker conflicts with canonical legacy policy

- `START_HERE.txt` says `Prompt Action v22.5.2`.
- Canonical `PLAN.md` and `docs/VERSIONING_RULES.md` state that active Prompt Action restarts at System V1 and that `V22.5.1` is the required legacy source.
- Classification: `CONFLICT / HISTORY_METADATA`.
- Resolution for STEP 00: do not treat `START_HERE.txt` as legacy source; retain as evidence only.

## C-002 — Recovery chunks exist but provenance/scope is not proven as required source

- `zz_BOOTSTRAP/chunks` contains 3 Base64 chunks.
- `zz_REBUILD/chunks` contains 9 Base64 chunks, commit history describing them as GitHub snapshot chunks.
- No ordinary extracted Prompt 1A–5 or explicit V22.5.1 package is present in audited HEAD.
- Remote connector inspection cannot establish a full extract test, internal file list, parent/version provenance, or byte-level SHA256 for the decoded archive.
- Classification: `VERSION_UNKNOWN / EVIDENCE_ONLY`.
- Resolution: preserve unchanged; do not promote to baseline source.

## C-003 — Canonical versus experimental UI package

- `Prompt-Action-UI-Reference-Materialized-V1.zip` is canonical.
- `Prompt-Action-UI-Reference-Package-V1.zip` is explicitly described as an old experimental package.
- Classification: no overwrite; experimental package `EXCLUDE` from baseline.

## C-004 — Per-file UI SHA256 not independently recomputed in this remote-only audit

- Five materialized JPGs are readable and a successful GitHub Actions run validates each as JPEG 320x180.
- Exact Git blob identities are known.
- Canonical materialized ZIP SHA256 is verified.
- Per-image SHA256 was not independently recomputed from a local staging copy in this execution channel.
- Classification: audit limitation, not an integrity mismatch.

## Integrity conflicts

No evidence was found that STEP 00 overwrote an original file, changed a bootstrap/rebuild chunk, redesigned UI, or created replacement prompt source.
