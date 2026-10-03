# STEP 08 Test Results

Validated head: `39259e7dc98cd28d225fad05003c53e60338dae9`

- STEP 08 T01–T50: **50/50 PASS**
- DPI smoke 100/125/150/175: **PASS**
- STEP 01–07 regression: **234 PASS**
- STEP 03 visual evidence regeneration: **PASS**
- STEP 04 visual evidence regeneration: **PASS**
- STEP 05 visual evidence regeneration: **PASS**
- STEP 06 visual evidence regeneration: **PASS**
- STEP 07 visual evidence regeneration: **PASS**
- module Settings smoke: **PASS**
- protected hash recheck: **PASS**
- QML capture warnings: `[]`

Successful workflow: `STEP 08 Settings CI`, run `37121864116`, job `111199388763`.

The preceding attempt reached visual capture and initially produced 48 PASS / 2 FAIL. One failure was a duplicated temporary-directory test fixture; the other exposed an over-broad sanitizer match for `pat` inside `path`. Both were corrected before this final validated run.
