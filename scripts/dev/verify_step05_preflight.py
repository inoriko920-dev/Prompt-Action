from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PySide6.QtGui import QImage

from prompt_action.data.repository import VersionRepository


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    required_reports = [root / "docs/implementation" / f"STEP_0{i}_SOL_EXECUTION_REPORT.md" for i in range(1, 5)]
    required_reports.insert(0, root / "docs/implementation/STEP_00_BASELINE_REPORT.md")
    prerequisites = {}
    failures: list[str] = []
    for path in required_reports:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        ok = path.is_file() and "PASS" in text
        prerequisites[str(path.relative_to(root))] = {"exists": path.is_file(), "pass_marker": ok}
        if not ok:
            failures.append(f"Prerequisite report missing PASS: {path.name}")

    master = root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/02-Sejarah-Sistem.jpg"
    image = QImage(str(master))
    master_info = {"path": str(master.relative_to(root)), "exists": master.is_file(), "readable": not image.isNull(), "width": image.width(), "height": image.height(), "sha256": sha256(master) if master.is_file() else None}
    if image.isNull():
        failures.append("Master 02-Sejarah-Sistem.jpg unreadable")

    repository = VersionRepository(root)
    state = repository.load()
    report = repository.validate(state)
    if not report.is_valid:
        failures.append("Canonical version history invalid")
    document = state.document
    legacy = document.get("legacy_sources", [])
    if len(legacy) != 1 or legacy[0].get("id") != "V22.5.1":
        failures.append("STEP 05 requires one canonical Legacy V22.5.1 node")

    protected_paths = [root / "BASELINE.json", root / "data/version_history.json", root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/VERSIONING_RULES.md", master]
    result = {
        "status": "PASS" if not failures else "FAIL",
        "prerequisites": prerequisites,
        "master_history": master_info,
        "canonical": {"valid": report.is_valid, "active_system": document.get("active_system"), "active_snapshot": document.get("active_snapshot"), "systems": len(document.get("systems", [])), "snapshots": len(document.get("snapshots", [])), "legacy_sources": len(legacy)},
        "protected": {str(path.relative_to(root)): {"exists": path.is_file(), "sha256": sha256(path) if path.is_file() else None} for path in protected_paths},
        "failures": failures,
    }
    output = root / "ci-step05-preflight"
    output.mkdir(parents=True, exist_ok=True)
    (output / "preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
