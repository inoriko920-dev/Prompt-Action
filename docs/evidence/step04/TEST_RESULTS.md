# STEP 04 Test Results

Workflow run `37106329477` on head `063d42eec213f9438fe7cf2faf00dbb4db4234b8`: **SUCCESS**.

## STEP 04 T01–T35

| Test | Contract | Result |
|---|---|---|
| T01 | Dashboard route opens | PASS |
| T02 | No production hardcode V1/S004 sample fixture | PASS |
| T03 | KPI System from canonical engine | PASS |
| T04 | KPI Snapshot from canonical engine | PASS |
| T05 | Active Prompt count correct | PASS |
| T06 | Backup healthy mapping | PASS |
| T07 | Backup-required mapping | PASS |
| T08 | Unknown backup mapping | PASS |
| T09 | Baseline has no fake PRIMARY | PASS |
| T10 | PRIMARY change render | PASS |
| T11 | SYNC changes 0/1/many | PASS |
| T12 | Baseline prompt grid 8 items | PASS |
| T13 | Dynamic prompt count | PASS |
| T14 | Integrity warning item | PASS |
| T15 | Lihat Snapshot navigation intent | PASS |
| T16 | Prompt click navigation intent | PASS |
| T17 | Recent-change action intent | PASS |
| T18 | Backup button disabled by capability | PASS |
| T19 | Download enabled only for valid file | PASS |
| T20 | Loading state has no sample values | PASS |
| T21 | Empty state | PASS |
| T22 | Invalid-data blocking state | PASS |
| T23 | Degraded state | PASS |
| T24 | Error + safe retry | PASS |
| T25 | Refresh idempotent | PASS |
| T26 | No domain write on Dashboard load | PASS |
| T27 | 1600×900 visual baseline | PASS |
| T28 | 1920×1080 visual baseline | PASS |
| T29 | 1366×768 usability | PASS |
| T30 | DPI 125% | PASS |
| T31 | DPI 150% | PASS |
| T32 | Keyboard tab/focus | PASS |
| T33 | Long text/wrap handling | PASS |
| T34 | Restart retains correct read state | PASS |
| T35 | STEP 01–03 smoke regression | PASS |

Pytest result: **35 passed**.

## Regression

`tests/step01 tests/step02 tests/step03`: **73 passed**.

Additional gates:
- prerequisite/canonical preflight: PASS
- STEP 03 regression evidence generation: PASS
- explicit 175% DPI probe: PASS
- module smoke `python -m prompt_action --smoke-test-ms 180`: PASS
- capture QML warnings: `[]`

## Integrity

Canonical and protected source hashes matched preflight expectations. Dashboard load/refresh did not mutate `data/version_history.json`.
