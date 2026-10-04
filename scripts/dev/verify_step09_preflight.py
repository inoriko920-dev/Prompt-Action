from __future__ import annotations

import hashlib
import json
from pathlib import Path

from prompt_action.data.repository import VersionRepository
from prompt_action.services.step09 import CapabilityService, GlobalSearchService

ROOT = Path(__file__).resolve().parents[2]
RECOVERED_P3_SHA = "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report_names = ["STEP_00_BASELINE_REPORT.md", *[f"STEP_{index:02d}_SOL_EXECUTION_REPORT.md" for index in range(1, 9)]]
    prerequisites = {name: (ROOT / "docs/implementation" / name).is_file() for name in report_names}
    repository = VersionRepository(ROOT)
    state = repository.load()
    validation = repository.validate(state)
    document = state.document
    prompt_records = []
    for prompt_id, prompt in document.get("prompts", {}).items():
        for revision_id, revision in prompt.get("revisions", {}).items():
            prompt_records.append({
                "prompt_id": prompt_id,
                "revision_id": revision_id,
                "file_available": revision.get("file_available") is True,
                "file": revision.get("file"),
                "sha256": revision.get("sha256"),
            })
    physical_available = [x for x in prompt_records if x["file_available"]]
    backups = document.get("backups", []) if isinstance(document.get("backups"), list) else []
    search = GlobalSearchService(ROOT)
    future_caps = {name: CapabilityService(search_ready=search.ready).get(name).to_dict() for name in ("ADD_REVISION", "CREATE_BACKUP", "RESTORE")}
    p3_sha = document.get("prompts", {}).get("P3", {}).get("revisions", {}).get("R1", {}).get("sha256")
    payload = {
        "status": "PASS",
        "prerequisites": prerequisites,
        "canonical": {
            "valid": validation.is_valid,
            "active_system": document.get("active_system"),
            "active_snapshot": document.get("active_snapshot"),
            "prompt_count": len(document.get("prompts", {})),
            "physical_prompt_revision_count": len(physical_available),
            "backup_record_count": len(backups),
            "p3_r1_sha256": p3_sha,
            "production_compare_download_expected_blocked": len(physical_available) == 0 and len(backups) == 0,
        },
        "search": {"ready": search.ready, "entity_count": len(search.entities)},
        "future_capabilities": future_caps,
        "protected": {
            "BASELINE.json": sha(ROOT / "BASELINE.json"),
            "data/version_history.json": sha(ROOT / "data/version_history.json"),
            "prompt_bytes_reconstructed": document.get("integrity", {}).get("prompt_bytes_reconstructed"),
        },
        "failures": [],
    }
    if not all(prerequisites.values()): payload["failures"].append("STEP 00-08 report prerequisite missing")
    if not validation.is_valid: payload["failures"].append("canonical invalid")
    if document.get("active_system") != "V1" or document.get("active_snapshot") != "S001": payload["failures"].append("canonical identity changed unexpectedly")
    if p3_sha != RECOVERED_P3_SHA: payload["failures"].append("reconciled P3 baseline hash mismatch")
    if payload["protected"]["prompt_bytes_reconstructed"] is not False: payload["failures"].append("prompt reconstruction policy changed")
    if not search.ready: payload["failures"].append("search index not ready")
    if any(value["enabled"] for value in future_caps.values()): payload["failures"].append("future-owner mutation capability enabled")
    payload["status"] = "PASS" if not payload["failures"] else "FAIL"
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
