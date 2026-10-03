# STEP 09 Path Safety Evidence

Validated by T38–T50 on Windows CI.

- `../` path traversal is rejected with `PATH_ESCAPE`.
- Absolute source injection is rejected with `PATH_ABSOLUTE_SOURCE`.
- Resolved/symlink-style escape outside the allowed root is rejected with `PATH_SYMLINK_ESCAPE`.
- Missing/non-regular sources are rejected.
- Long destination paths fail with an actionable `PATH_TOO_LONG` error.
- Unicode and spaces in destination folders are supported.
- Existing destination defaults to non-overwrite; `cancel`, `keep_both`, and explicit `replace` are separate policies.
- Streaming copy writes to `.tmp-*` first and finalizes atomically.
- Cancel before/during copy removes temp state and does not leave a final ZIP.
- Simulated copy failure removes temp state and does not leave a final ZIP.
- Open-folder target is resolved without shell-string construction.

Download sources are resolved from stable canonical entity references; STEP 09 does not accept an arbitrary UI-supplied source path.
