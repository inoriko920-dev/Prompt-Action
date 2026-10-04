from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def replace_once(relative: str, old: str, new: str) -> None:
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise SystemExit(f"expected migration pattern missing: {relative}\n--- OLD ---\n{old}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    # STEP 03: immutable UI reference assets remain byte-pinned. Canonical/baseline
    # metadata are intentionally allowed to evolve in later validated steps.
    replace_once(
        "tests/step03/test_step03_ui_shell.py",
        '    "BASELINE.json": "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d",\n    "data/version_history.json": "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb",\n',
        '',
    )

    # STEP 04: isolated dashboard fixtures must materialize any canonical prompt
    # files they claim are available. The production baseline is now COMPLETE;
    # BACKUP_REQUIRED remains tested as an explicit synthetic state only.
    replace_once(
        "tests/step04/test_step04_dashboard.py",
        "import subprocess\nimport sys\n",
        "import subprocess\nimport sys\nimport shutil\n",
    )
    replace_once(
        "tests/step04/test_step04_dashboard.py",
        '    (tmp_path / "data/version_history.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")\n    return tmp_path\n',
        '    (tmp_path / "data/version_history.json").write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")\n    for prompt in document.get("prompts", {}).values():\n        for revision in prompt.get("revisions", {}).values():\n            rel = revision.get("file")\n            if revision.get("file_available") is True and isinstance(rel, str) and rel:\n                source = ROOT / rel\n                target = tmp_path / rel\n                if source.is_file():\n                    target.parent.mkdir(parents=True, exist_ok=True)\n                    shutil.copy2(source, target)\n    return tmp_path\n',
    )
    replace_once(
        "tests/step04/test_step04_dashboard.py",
        'def test_t07_backup_required_mapping(tmp_path):\n    state = _service(tmp_path, deepcopy(BASE_DOC)).read()\n    assert state.backup_health == "PERLU BACKUP" and state.recovery_health == "REQUIRED"\n',
        'def test_t07_backup_required_mapping(tmp_path):\n    service = _service(tmp_path, deepcopy(BASE_DOC))\n    health, recovery, _, _, _ = service._backup_state(BASE_DOC, {"id": "Sx", "status": "BACKUP_REQUIRED", "backup_id": None})\n    assert health == "PERLU BACKUP" and recovery == "REQUIRED"\n',
    )

    # STEP 05: V22.5.1 remains the baseline source, but verified prompt-specific
    # legacy releases may coexist (P3 v22.5.2 recovery).
    replace_once(
        "scripts/dev/verify_step05_preflight.py",
        '    if len(legacy) != 1 or legacy[0].get("id") != "V22.5.1":\n        failures.append("STEP 05 requires one canonical Legacy V22.5.1 node")\n',
        '    baseline_legacy = [item for item in legacy if isinstance(item, dict) and item.get("id") == "V22.5.1"]\n    if len(baseline_legacy) != 1:\n        failures.append("STEP 05 requires exactly one canonical Legacy V22.5.1 baseline node")\n',
    )

    # STEP 06: after STEP 09.5, official R1 bytes are materialized and exact-byte
    # downloads are honestly available. Protect prompt bytes, not mutable metadata.
    replace_once(
        "tests/step06/test_step06_per_prompt.py",
        'def test_t14_history_only_file_state(): assert state()["selected_revision"]["file_state"] == "HISTORY_ONLY"\n',
        'def test_t14_materialized_file_state(): assert state()["selected_revision"]["file_state"] == "VALID"\n',
    )
    replace_once(
        "tests/step06/test_step06_per_prompt.py",
        'def test_t16_active_download_disabled(): assert state()["capabilities"]["can_download_active"] is False\ndef test_t17_selected_download_disabled(): assert state()["capabilities"]["can_download_selected"] is False\n',
        'def test_t16_active_download_enabled_for_verified_bytes(): assert state()["capabilities"]["can_download_active"] is True\ndef test_t17_selected_download_enabled_for_verified_bytes(): assert state()["capabilities"]["can_download_selected"] is True\n',
    )
    replace_once(
        "tests/step06/test_step06_per_prompt.py",
        'def test_t42_baseline_hash_protected(): assert digest(ROOT/"BASELINE.json") == "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d"\ndef test_t43_version_history_hash_protected(): assert digest(CANONICAL) == "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"\n',
        'def test_t42_materialized_p1a_hash_protected(): assert digest(ROOT/"prompts/V1/Prompt-1A/Prompt-1A_V1_R1.txt") == "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"\ndef test_t43_recovered_p3_hash_protected(): assert digest(ROOT/"prompts/V1/Prompt-3/Prompt-3_V1_R1.txt") == "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"\n',
    )

    # STEP 07: S001 now has a fully verified B001 bootstrap backup. The STEP 07
    # read-only projection must truthfully show SAFE/AMAN and usable read actions.
    path = "tests/step07/test_step07_backup_recovery.py"
    replacements = [
        ('def test_t04_backup_required(): assert state()["snapshot_status"] == "BACKUP_REQUIRED"\n', 'def test_t04_snapshot_complete(): assert state()["snapshot_status"] == "COMPLETE"\n'),
        ('def test_t05_health_required(): assert state()["recovery_health"] == "REQUIRED"\n', 'def test_t05_health_safe(): assert state()["recovery_health"] == "SAFE"\n'),
        ('def test_t06_label_not_safe(): assert state()["recovery_label"] == "BELUM AMAN"\n', 'def test_t06_label_safe(): assert state()["recovery_label"] == "AMAN"\n'),
        ('def test_t07_no_fake_latest_backup(): assert state()["latest_backup"] is None\n', 'def test_t07_latest_backup_is_real_b001(): assert state()["latest_backup"] is not None and state()["latest_backup"]["id"] == "B001" and state()["latest_backup"]["valid"] is True\n'),
        ('def test_t09_history_required(): assert state()["history"][0]["status"] == "REQUIRED"\n', 'def test_t09_history_valid(): assert state()["history"][0]["status"] == "VALID"\n'),
        ('def test_t12_active_prompts_false(): assert next(x for x in state()["checklist"] if x["key"] == "active_prompts")["ok"] is False\n', 'def test_t12_active_prompts_true(): assert next(x for x in state()["checklist"] if x["key"] == "active_prompts")["ok"] is True\n'),
        ('def test_t13_revisions_false(): assert next(x for x in state()["checklist"] if x["key"] == "revisions")["ok"] is False\n', 'def test_t13_revisions_true(): assert next(x for x in state()["checklist"] if x["key"] == "revisions")["ok"] is True\n'),
        ('def test_t14_full_backup_false(): assert next(x for x in state()["checklist"] if x["key"] == "full_backup")["ok"] is False\n', 'def test_t14_full_backup_true(): assert next(x for x in state()["checklist"] if x["key"] == "full_backup")["ok"] is True\n'),
        ('def test_t15_sha_false(): assert next(x for x in state()["checklist"] if x["key"] == "sha256")["ok"] is False\n', 'def test_t15_sha_true(): assert next(x for x in state()["checklist"] if x["key"] == "sha256")["ok"] is True\n'),
        ('def test_t16_verify_false(): assert next(x for x in state()["checklist"] if x["key"] == "zip_verified")["ok"] is False\n', 'def test_t16_verify_true(): assert next(x for x in state()["checklist"] if x["key"] == "zip_verified")["ok"] is True\n'),
        ('def test_t17_second_copy_false(): assert next(x for x in state()["checklist"] if x["key"] == "second_copy")["ok"] is False\n', 'def test_t17_second_copy_true(): assert next(x for x in state()["checklist"] if x["key"] == "second_copy")["ok"] is True\n'),
        ('def test_t18_download_disabled(): assert state()["actions"]["can_download_backup"] is False\n', 'def test_t18_download_enabled(): assert state()["actions"]["can_download_backup"] is True\n'),
        ('def test_t19_sha_download_disabled(): assert state()["actions"]["can_download_sha256"] is False\n', 'def test_t19_sha_download_enabled(): assert state()["actions"]["can_download_sha256"] is True\n'),
        ('def test_t20_verify_disabled(): assert state()["actions"]["can_verify_backup"] is False\n', 'def test_t20_verify_enabled(): assert state()["actions"]["can_verify_backup"] is True\n'),
        ('def test_t21_folder_disabled(): assert state()["actions"]["can_open_folder"] is False\n', 'def test_t21_folder_enabled(): assert state()["actions"]["can_open_folder"] is True\n'),
        ('def test_t45_baseline_unchanged():\n    assert digest(ROOT / "BASELINE.json") == "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d"\n\ndef test_t46_canonical_unchanged():\n    assert digest(CANONICAL) == "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"\n', 'def test_t45_reconciled_backup_hash_protected():\n    assert digest(ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip") == "f04e1b69c2613bf238c547bfab9cc81ab5708c100843e13b6750ea950f33d8a6"\n\ndef test_t46_recovered_p3_hash_protected():\n    assert digest(ROOT / "prompts/V1/Prompt-3/Prompt-3_V1_R1.txt") == "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"\n'),
    ]
    for old, new in replacements:
        replace_once(path, old, new)

    # STEP 08: settings must not freeze mutable canonical metadata to a STEP 02
    # hash. Validate the reconciled canonical identity instead.
    replace_once(
        "scripts/dev/verify_step08_preflight.py",
        '    if protected["BASELINE.json"] != "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d": failures.append("BASELINE.json hash changed")\n    if protected["data/version_history.json"] != "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb": failures.append("canonical version_history.json hash changed")\n',
        '    canonical = json.loads((root/"data/version_history.json").read_text(encoding="utf-8"))\n    if canonical.get("active_system") != "V1" or canonical.get("active_snapshot") != "S001": failures.append("canonical identity changed unexpectedly")\n    if canonical.get("prompts", {}).get("P3", {}).get("revisions", {}).get("R1", {}).get("sha256") != "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1": failures.append("reconciled P3 baseline hash mismatch")\n',
    )
    replace_once(
        "tests/step08/test_step08_settings.py",
        'def test_t50_protected_canonical_prompt_files_unchanged():\n    assert digest(BASELINE)=="8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d" and digest(CANONICAL)=="1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"\n',
        'def test_t50_reconciled_canonical_contract():\n    doc=json.loads(CANONICAL.read_text(encoding="utf-8")); assert doc["active_system"]=="V1" and doc["active_snapshot"]=="S001" and doc["prompts"]["P3"]["revisions"]["R1"]["sha256"]=="0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"\n',
    )

    # STEP 09: mutable baseline/canonical metadata may evolve after STEP 09.
    # Keep domain validation, reconstruction policy and capability gates as proof.
    replace_once(
        "scripts/dev/verify_step09_preflight.py",
        'EXPECTED_BASELINE = "8ffd22fe3636309ce0484f8b724f9fe306f3156383c5f4efbcc7e59f79e90b6d"\nEXPECTED_CANONICAL = "1a0fddf98b000bb908e12e5aa617b42793a399a8dd9cb36e1acf7204ca8465bb"\n\n',
        '',
    )
    replace_once(
        "scripts/dev/verify_step09_preflight.py",
        '    if payload["protected"]["BASELINE.json"] != EXPECTED_BASELINE: payload["failures"].append("BASELINE hash changed")\n    if payload["protected"]["data/version_history.json"] != EXPECTED_CANONICAL: payload["failures"].append("canonical hash changed")\n',
        '',
    )

    print("post-STEP09.5 regression contract migration applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
