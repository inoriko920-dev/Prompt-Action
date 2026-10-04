# Portable Windows Main-Derived Validation

Status: PENDING CI

Purpose: trigger a reproducibility build from a branch created directly from the current `main` after PR #15 merge. No application, canonical Prompt, Snapshot, backup, or STEP 11 state is changed by this validation note.

Expected validation:
- source application smoke test passes;
- PyInstaller onedir build succeeds on Windows x64;
- portable layout is complete;
- frozen `PromptAction.exe` smoke test exits 0;
- ZIP SHA-256 sidecar matches;
- artifact is uploaded successfully.
