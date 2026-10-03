from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PySide6.QtGui import QImage

from prompt_action.data.repository import VersionRepository
from prompt_action.services.version_engine import VersionEngine


REPORTS = [
    Path("docs/implementation/STEP_00_BASELINE_REPORT.md"),
    Path("docs/implementation/STEP_01_SOL_EXECUTION_REPORT.md"),
    Path("docs/implementation/STEP_02_SOL_EXECUTION_REPORT.md"),
    Path("docs/implementation/STEP_03_SOL_EXECUTION_REPORT.md"),
]
MASTER = Path("docs/UI_REFERENCE_PACKAGE_V1/materialized/images/01-Dashboard.jpg")
PROTECTED = [
    Path("BASELINE.json"),
    Path("data/version_history.json"),
    Path("docs/UI_REFERENCE_PACKAGE_V1/materialized/VERSIONING_RULES.md"),
    MASTER,
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    failures: list[str] = []
    prereq = {}
    for rel in REPORTS:
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        ok = path.is_file() and "PASS" in text
        prereq[str(rel)] = {"exists": path.is_file(), "pass_marker": ok}
        if not ok:
            failures.append(f"Prerequisite report not PASS: {rel}")

    image_path = root / MASTER
    image = QImage(str(image_path))
    image_ok = image_path.is_file() and not image.isNull()
    master = {
        "path": str(MASTER),
        "exists": image_path.is_file(),
        "readable": image_ok,
        "width": image.width() if image_ok else 0,
        "height": image.height() if image_ok else 0,
        "sha256": sha256(image_path) if image_path.is_file() else None,
    }
    if not image_ok:
        failures.append("Master Dashboard image is missing or unreadable")

    repo = VersionRepository(root)
    engine = VersionEngine(repo)
    state = repo.load()
    report = repo.validate(state)
    if not report.is_valid:
        failures.append("Canonical version_history is invalid")
    try:
        context = engine.get_active_context()
    except Exception as exc:
        failures.append(f"VersionEngine active context failed: {exc}")
        context = None

    protected = {}
    for rel in PROTECTED:
        path = root / rel
        protected[str(rel)] = {"exists": path.is_file(), "sha256": sha256(path) if path.is_file() else None}
        if not path.is_file():
            failures.append(f"Protected input missing: {rel}")

    payload = {
        "status": "PASS" if not failures else "BLOCKED",
        "prerequisites": prereq,
        "master_dashboard": master,
        "canonical": {
            "valid": report.is_valid,
            "issues": report.to_dict(),
            "active_system": state.active_system,
            "active_snapshot": state.active_snapshot,
            "active_context": context,
        },
        "protected": protected,
        "failures": failures,
    }
    out = root / "ci-step04-preflight"
    out.mkdir(parents=True, exist_ok=True)
    (out / "preflight.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
