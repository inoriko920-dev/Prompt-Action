from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PySide6.QtGui import QImage


MASTER_REFS = [
    "01-Dashboard.jpg",
    "02-Sejarah-Sistem.jpg",
    "03-Per-Prompt.jpg",
    "04-Backup-Recovery.jpg",
    "05-Pengaturan.jpg",
]

PREREQUISITE_REPORTS = [
    ("STEP 00", "docs/implementation/STEP_00_BASELINE_REPORT.md"),
    ("STEP 01", "docs/implementation/STEP_01_SOL_EXECUTION_REPORT.md"),
    ("STEP 02", "docs/implementation/STEP_02_SOL_EXECUTION_REPORT.md"),
]

PROTECTED_FILES = [
    "BASELINE.json",
    "data/version_history.json",
    "docs/UI_REFERENCE_PACKAGE_V1/materialized/VERSIONING_RULES.md",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("evidence/step03/input-gate"))
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    output = (root / args.output).resolve() if not args.output.is_absolute() else args.output.resolve()
    refs_output = output / "master_refs"
    refs_output.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    report: dict[str, object] = {
        "repo_root": str(root),
        "prerequisites": {},
        "master_refs": {},
        "protected_files": {},
    }

    prerequisite_result: dict[str, object] = {}
    for label, relative in PREREQUISITE_REPORTS:
        path = root / relative
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        passed = path.is_file() and "PASS" in text.upper()
        prerequisite_result[label] = {"path": relative, "exists": path.is_file(), "pass_marker": passed}
        if not passed:
            failures.append(f"{label} PASS evidence missing: {relative}")
    report["prerequisites"] = prerequisite_result

    master_dir = root / "docs/UI_REFERENCE_PACKAGE_V1/materialized/images"
    refs_result: dict[str, object] = {}
    for name in MASTER_REFS:
        path = master_dir / name
        entry: dict[str, object] = {"path": str(path.relative_to(root)), "exists": path.is_file()}
        if path.is_file():
            image = QImage(str(path))
            entry.update(
                {
                    "readable": not image.isNull(),
                    "width": image.width(),
                    "height": image.height(),
                    "sha256": sha256(path),
                    "bytes": path.stat().st_size,
                }
            )
            if image.isNull() or image.width() != 320 or image.height() != 180:
                failures.append(f"Master reference invalid: {name}")
            else:
                shutil.copy2(path, refs_output / name)
        else:
            failures.append(f"Master reference missing: {name}")
        refs_result[name] = entry
    report["master_refs"] = refs_result

    protected_result: dict[str, object] = {}
    for relative in PROTECTED_FILES:
        path = root / relative
        exists = path.is_file()
        protected_result[relative] = {"exists": exists, "sha256": sha256(path) if exists else None}
        if not exists:
            failures.append(f"Protected source missing: {relative}")
    report["protected_files"] = protected_result

    report["status"] = "PASS" if not failures else "BLOCKED"
    report["failures"] = failures
    output.mkdir(parents=True, exist_ok=True)
    (output / "input_gate.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
