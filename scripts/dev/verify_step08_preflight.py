from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PySide6.QtGui import QImage
from prompt_action.settings.repository import SettingsRepository
from prompt_action.settings.validator import validate_settings


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    impl = root / "docs" / "implementation"
    required = ["STEP_00_BASELINE_REPORT.md","STEP_01_SOL_EXECUTION_REPORT.md","STEP_02_SOL_EXECUTION_REPORT.md","STEP_03_SOL_EXECUTION_REPORT.md","STEP_04_SOL_EXECUTION_REPORT.md","STEP_05_SOL_EXECUTION_REPORT.md","STEP_06_SOL_EXECUTION_REPORT.md","STEP_07_SOL_EXECUTION_REPORT.md"]
    failures: list[str] = []
    reports = {}
    for name in required:
        p = impl / name
        ok = p.is_file() and "PASS" in p.read_text(encoding="utf-8", errors="replace")
        reports[name] = ok
        if not ok: failures.append(f"missing PASS prerequisite: {name}")

    master = root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images/05-Pengaturan.jpg"
    image = QImage(str(master)) if master.is_file() else QImage()
    master_info = {"path":str(master.relative_to(root)) if master.is_file() else str(master),"exists":master.is_file(),"readable":not image.isNull(),"width":image.width() if not image.isNull() else 0,"height":image.height() if not image.isNull() else 0,"sha256":sha256(master) if master.is_file() else None}
    if not master_info["readable"]: failures.append("master 05-Pengaturan.jpg unreadable")

    repo = SettingsRepository(root)
    loaded = repo.load()
    validation = validate_settings(loaded.settings, root)
    protected = {"BASELINE.json":sha256(root/"BASELINE.json"),"data/version_history.json":sha256(root/"data/version_history.json"),"master":master_info["sha256"]}
    if protected["BASELINE.json"] != "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d": failures.append("BASELINE.json hash changed")
    if protected["data/version_history.json"] != "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb": failures.append("canonical version_history.json hash changed")
    result = {"status":"PASS" if not failures else "BLOCKED","prerequisites":reports,"master_settings":master_info,"settings":{"source":loaded.source,"degraded":loaded.degraded,"error":loaded.error,"valid":validation.valid,"errors":validation.errors,"warnings":validation.warnings,"settings_path":str(repo.settings_path.relative_to(root))},"protected":protected,"failures":failures}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
