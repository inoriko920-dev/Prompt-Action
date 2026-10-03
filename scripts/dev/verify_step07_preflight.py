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
    failures: list[str] = []
    prereqs = {}
    for i in range(0, 7):
        name = "STEP_00_BASELINE_REPORT.md" if i == 0 else f"STEP_0{i}_SOL_EXECUTION_REPORT.md"
        path = root / "docs/implementation" / name
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        ok = path.is_file() and "PASS" in text
        prereqs[name] = ok
        if not ok:
            failures.append(f"Missing PASS prerequisite: {name}")

    master = root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/04-Backup-Recovery.jpg"
    image = QImage(str(master))
    if image.isNull():
        failures.append("Master Backup & Recovery reference unreadable")

    repository = VersionRepository(root)
    state = repository.load()
    report = repository.validate(state)
    if not report.is_valid:
        failures.append("Canonical version history invalid")
    doc = state.document
    active_snapshot = next((s for s in doc.get("snapshots", []) if s.get("id") == doc.get("active_snapshot")), None)
    if not active_snapshot:
        failures.append("Active snapshot missing")

    result = {
        "status": "PASS" if not failures else "FAIL",
        "prerequisites": prereqs,
        "master_backup_recovery": {
            "path": str(master.relative_to(root)), "exists": master.is_file(), "readable": not image.isNull(),
            "width": image.width(), "height": image.height(), "sha256": sha256(master) if master.is_file() else None,
        },
        "canonical": {
            "valid": report.is_valid,
            "active_system": doc.get("active_system"), "active_snapshot": doc.get("active_snapshot"),
            "snapshot_status": active_snapshot.get("status") if active_snapshot else None,
            "backups": len(doc.get("backups", [])),
        },
        "protected": {
            "BASELINE.json": sha256(root / "BASELINE.json"),
            "data/version_history.json": sha256(root / "data/version_history.json"),
            "master": sha256(master) if master.is_file() else None,
        },
        "failures": failures,
    }
    out = root / "ci-step07-preflight"
    out.mkdir(parents=True, exist_ok=True)
    (out / "preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
