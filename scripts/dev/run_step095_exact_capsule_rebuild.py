from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "scripts/dev/rebuild_step095_bootstrap_from_preserved_chunks.py"

spec = importlib.util.spec_from_file_location("step095_rebuild", SOURCE)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load STEP 09.5 rebuild module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# The exact-byte capsule was created from the independently verified rescue ZIP.
# Prefer it explicitly; keep legacy preserved chunk locations as additional audit inputs.
module.CHUNK_DIRS = [ROOT / "docs/evidence/step095/exact_prompt_capsule", *module.CHUNK_DIRS]
module.main()
