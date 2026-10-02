# STEP 00 — Conflict Register

## C-001 — Version marker differs from canonical legacy policy

- `START_HERE.txt` says `Prompt Action v22.5.2`.
- Canonical `PLAN.md` and `docs/VERSIONING_RULES.md` state that active Prompt Action restarts at System V1 and that `V22.5.1` is the required legacy source.
- Classification: `CONFLICT / HISTORY_METADATA`.
- Resolution: `START_HERE.txt` remains evidence-only and is not used as the legacy baseline.
- Blocking: **NO**, because V22.5.1 is now independently verified from the supplied rescue ZIP.

## C-002 — Old encoded recovery chunks have unresolved provenance

- `zz_BOOTSTRAP/chunks` contains 3 Base64 chunks.
- `zz_REBUILD/chunks` contains 9 Base64 chunks.
- Their exact decoded provenance remains `VERSION_UNKNOWN`.
- Resolution: preserve unchanged as `EVIDENCE_ONLY`.
- Blocking: **NO**, because a separate V22.5.1 rescue ZIP now passes hash/extract/manifest/source verification and supplies the complete required Prompt 1A–5 corpus.

## C-003 — Canonical versus experimental UI package

- `Prompt-Action-UI-Reference-Materialized-V1.zip` is canonical.
- `Prompt-Action-UI-Reference-Package-V1.zip` is explicitly described as an old experimental package.
- Resolution: experimental package remains `EXCLUDE`; no overwrite.
- Blocking: **NO**.

## C-004 — Repo-native UI integrity representation

- Five materialized JPGs are readable and a successful GitHub Actions run validates each as JPEG 320x180.
- Exact immutable Git blob identities are recorded for all five.
- The canonical materialized UI ZIP has verified SHA256 `2797cf5993ba6e38532d028135f5f8ab12f99bc55ed0b643b441e57ca5eeebb0` and was generated from the materialized directory by the successful workflow.
- Resolution: treat the Git object IDs + successful workflow + canonical package SHA256 as repository-side integrity evidence for STEP 00.
- Blocking: **NO**.

## C-005 — Prompt 1A has no inline V22.5.1 marker

- Prompt 1A itself does not contain the string `V22.5.1`.
- The V22.5.1 package index includes active workflow `1A`.
- `03-Sumber-Pedoman-Pembaruan-V22.5.1.txt` and `01-Audit-Sinkronisasi-V22.txt` explicitly state that Prompt 1A was unchanged.
- Prompt 1A SHA256 matches the V22.5.1 manifest exactly.
- Resolution: Prompt 1A is accepted as the active V22.5.1 baseline source.
- Blocking: **NO**.

## Integrity conflicts

No unexplained hash mismatch, overwritten original, source reconstruction, UI redesign, bootstrap/rebuild modification, or destructive repository operation was found.

**Open blocking conflicts: 0**
