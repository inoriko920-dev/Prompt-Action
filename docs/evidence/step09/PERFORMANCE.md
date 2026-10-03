# STEP 09 Performance Notes

Observed on the successful Windows hosted CI run:

- STEP 09 T01–T60: 60 tests in **1.47s**.
- STEP 01–08 regression: 284 tests in **12.54s**.
- Production canonical search index: **18 metadata entities**; exact query `P3` returns deterministic results without UI warning.
- Download fixture uses chunked streaming with a 4096-byte test chunk size and performs multiple chunks; the service does not load the full ZIP into one application buffer.
- Search result cap and stale-query cancellation are covered by T08/T11.
- DPI 150 application smoke and 1366×768 QML state both pass.

These are baseline engineering measurements, not claims about final release-scale performance. The ASTRA planning target of interactive metadata search up to approximately 5,000 entities remains a later scale benchmark; STEP 09 establishes deterministic bounded architecture and streaming behavior needed for that target.
