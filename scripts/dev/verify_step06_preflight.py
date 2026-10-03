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
    required_reports = [root / "docs/implementation/STEP_00_BASELINE_REPORT.md"]
    required_reports.extend(root / "docs/implementation" / f"STEP_0{i}_SOL_EXECUTION_REPORT.md" for i in range(1, 6))
    prerequisites = {}
    failures: list[str] = []
    for path in required_reports:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        ok = path.is_file() and "PASS" in text
        prerequisites[str(path.relative_to(root))] = {"exists": path.is_file(), "pass_marker": ok}
        if not ok:
            failures.append(f"Prerequisite report missing PASS: {path.name}")

    master = root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/03-Per-Prompt.jpg"
    image = QImage(str(master))
    master_info = {"path": str(master.relative_to(root)), "exists": master.is_file(), "readable": not image.isNull(), "width": image.width(), "height": image.height(), "sha256": sha256(master) if master.is_file() else None}
    if image.isNull():
        failures.append("Master 03-Per-Prompt.jpg unreadable")

    repository = VersionRepository(root)
    state = repository.load()
    report = repository.validate(state)
    if not report.is_valid:
        failures.append("Canonical prompt registry/revision graph invalid")
    document = state.document
    prompts = document.get("prompts", {}) if isinstance(document.get("prompts"), dict) else {}
    snapshots = {item.get("id"): item for item in document.get("snapshots", []) if isinstance(item, dict)}
    active_snapshot = snapshots.get(document.get("active_snapshot"), {})
    prompt_state = active_snapshot.get("prompt_state", {}) if isinstance(active_snapshot, dict) else {}
    if len(prompts) != 8:
        failures.append(f"Expected 8 canonical prompts; found {len(prompts)}")
    for prompt_id, prompt in prompts.items():
        if not isinstance(prompt, dict) or not isinstance(prompt.get("revisions"), dict) or not prompt.get("revisions"):
            failures.append(f"Prompt {prompt_id} missing official revision graph")
            continue
        if prompt.get("active_revision") != prompt_state.get(prompt_id):
            failures.append(f"Active revision pointer mismatch for {prompt_id}")

    protected_paths = [root / "BASELINE.json", root / "data/version_history.json", root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/VERSIONING_RULES.md", master]
    result = {
        "status": "PASS" if not failures else "FAIL",
        "prerequisites": prerequisites,
        "master_per_prompt": master_info,
        "canonical": {"valid": report.is_valid, "active_system": document.get("active_system"), "active_snapshot": document.get("active_snapshot"), "prompts": len(prompts), "prompt_ids": list(prompts), "active_prompt_state": prompt_state},
        "protected": {str(path.relative_to(root)): {"exists": path.is_file(), "sha256": sha256(path) if path.is_file() else None} for path in protected_paths},
        "failures": failures,
    }
    output = root / "ci-step06-preflight"
    output.mkdir(parents=True, exist_ok=True)
    (output / "preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
