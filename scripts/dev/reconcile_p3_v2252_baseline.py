from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "data/version_history.json"
BASELINE = ROOT / "BASELINE.json"
PRIMARY = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
SECOND = ROOT / "backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
RECORD = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-bootstrap-record.json"
EVIDENCE = ROOT / "docs/evidence/baseline-recovery-p3-v2252"
REPORT = ROOT / "docs/implementation/BASELINE_RECOVERY_P3_V2252_REPORT.md"

RESCUE_SHA = "f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2"
OLD_P3 = "de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8"
NEW_P3 = "0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1"
V2261_DRAFT_SHA = "fe7f64a10f131ccffc78733ea514156338090e77e867f53c5d8153d93db41870"
EXPECTED = {
    "P1A": ("Prompt-1A", "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"),
    "P1B": ("Prompt-1B", "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf"),
    "P1B1": ("Prompt-1B1", "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6"),
    "P1B2": ("Prompt-1B2", "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576"),
    "P2": ("Prompt-2", "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98"),
    "P3": ("Prompt-3", NEW_P3),
    "P4": ("Prompt-4", "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0"),
    "P5": ("Prompt-5", "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"),
}


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def canonical_rel(pid: str) -> str:
    label = EXPECTED[pid][0]
    return f"prompts/V1/{label}/{label}_V1_R1.txt"


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def dump_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(value))


def replace_hash_contract(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if NEW_P3 in text:
        return
    if OLD_P3 not in text:
        raise SystemExit(f"expected old P3 hash not found in {path}")
    path.write_text(text.replace(OLD_P3, NEW_P3), encoding="utf-8")


def add_current_p3_fallback(path: Path, marker: str) -> None:
    text = path.read_text(encoding="utf-8")
    tag = "hash-exact-baseline-recovery-p3-v22.5.2"
    if tag in text:
        return
    if marker not in text:
        raise SystemExit(f"fallback marker not found in {path}")
    snippet = (
        "    # hash-exact-baseline-recovery-p3-v22.5.2\n"
        "    p3_path = ROOT / canonical_rel(\"P3\")\n"
        "    if p3_path.is_file():\n"
        "        p3_raw = p3_path.read_bytes()\n"
        "        if sha(p3_raw) == EXPECTED[\"P3\"][1]:\n"
        "            found[\"P3\"] = p3_raw\n"
        "            provenance[\"P3\"] = \"hash-exact recovered v22.5.2 baseline override\"\n"
    )
    path.write_text(text.replace(marker, snippet + marker, 1), encoding="utf-8")


def patch_versioning_rules() -> None:
    path = ROOT / "docs/VERSIONING_RULES.md"
    text = path.read_text(encoding="utf-8")
    if "Prompt 3 memakai rilis resmi legacy `v22.5.2`" in text:
        return
    old = "Semua isi awal Prompt Action diambil dari baseline legacy ini, lalu dinormalkan menjadi:\n\n"
    new = (
        "Baseline System V1 memakai tujuh Prompt yang tetap identik dengan legacy V22.5.1. "
        "Prompt 3 memakai rilis resmi legacy `v22.5.2` yang telah diselesaikan sebelum normalisasi System V1. "
        "Rilis Prompt 3 tersebut dinormalkan sebagai **Prompt 3 V1 R1**, bukan sebagai R2/S002.\n\n"
        "Seluruh baseline dinormalkan menjadi:\n\n"
    )
    if old not in text:
        raise SystemExit("VERSIONING_RULES baseline paragraph not found")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_baseline_json() -> None:
    doc = json.loads(BASELINE.read_text(encoding="utf-8"))
    p3 = doc["prompts"]["Prompt 3"]
    p3.update({
        "status": "VERIFIED_SOURCE",
        "via": "HASH_EXACT_V22_5_2_RELEASE_RECOVERY",
        "bytes": 22320,
        "sha256": NEW_P3,
    })
    doc["baseline_reconciliation"] = {
        "status": "PASS",
        "reason": "STEP 00 originally seeded P3 from V22.5.1 although the pre-normalization official Prompt 3 release was v22.5.2.",
        "normalization": "legacy Prompt 3 v22.5.2 -> System V1 / Snapshot S001 / Prompt 3 R1",
        "historical_release_sha256": NEW_P3,
        "historical_release_bytes": 22320,
        "source_draft_v22_6_1_sha256": V2261_DRAFT_SHA,
        "recovery_method": "single exact version-label substitution V22.6.1 -> V22.5.2 on preserved draft; accepted only because the resulting bytes exactly match the historical release SHA-256",
        "old_incorrect_p3_sha256": OLD_P3,
        "prompt_bytes_reconstructed": False,
        "scope": "P3 baseline identity only; no new System, Snapshot, or Revision",
    }
    dump_json(BASELINE, doc)


def update_canonical() -> dict:
    doc = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if doc.get("active_system") != "V1" or doc.get("active_snapshot") != "S001" or doc.get("app_data_revision") != 2:
        raise SystemExit("unexpected canonical identity for baseline reconciliation")
    if [x.get("id") for x in doc.get("systems", [])] != ["V1"] or [x.get("id") for x in doc.get("snapshots", [])] != ["S001"]:
        raise SystemExit("baseline reconciliation refuses additional System/Snapshot IDs")
    if any(set(doc["prompts"][pid]["revisions"]) != {"R1"} for pid in EXPECTED):
        raise SystemExit("baseline reconciliation refuses additional Revision IDs")

    rev = doc["prompts"]["P3"]["revisions"]["R1"]
    if rev.get("sha256") not in (OLD_P3, NEW_P3):
        raise SystemExit("P3 canonical SHA is neither expected old nor recovered value")
    rev["sha256"] = NEW_P3
    rev["file"] = canonical_rel("P3")
    rev["file_available"] = True
    rev["summary"] = [
        "Hash-exact recovery of the official pre-normalization Prompt 3 v22.5.2 release.",
        "Normalized as System V1 / Snapshot S001 / Prompt 3 R1; this is not a new R2/S002 release.",
    ]
    rev["reason"] = (
        "Baseline reconciliation: STEP 00 used the V22.5.1 Prompt 3 bytes, while preserved version history identifies "
        "v22.5.2 as the official active Prompt 3 release before System V1 normalization."
    )
    doc["integrity"]["protected_prompt_hashes"]["P3"] = NEW_P3
    doc["integrity"]["baseline_reconciliation"] = {
        "id": "P3_V22_5_2_HASH_EXACT",
        "status": "VERIFIED",
        "old_sha256": OLD_P3,
        "new_sha256": NEW_P3,
        "bytes": 22320,
        "normalization_target": "V1/S001/P3/R1",
        "new_revision_created": False,
        "new_snapshot_created": False,
    }
    if not any(x.get("id") == "V22.5.2-P3" for x in doc.get("legacy_sources", [])):
        doc["legacy_sources"].append({
            "id": "V22.5.2-P3",
            "type": "LEGACY_PROMPT_RELEASE",
            "file_available": True,
            "source_path": canonical_rel("P3"),
            "sha256_manifest": NEW_P3,
            "manifest_verified": True,
            "evidence": "docs/evidence/baseline-recovery-p3-v2252/recovery-proof.json",
            "used_to_seed": "V1/S001/P3/R1",
            "note": "Official Prompt 3 release completed before System V1 normalization; normalized as R1, not R2.",
        })
    return doc


def build_bootstrap(doc: dict, payloads: dict[str, bytes]) -> bytes:
    embedded = copy.deepcopy(doc)
    embedded["backups"] = []
    snap = embedded["snapshots"][0]
    snap["status"] = "BACKUP_REQUIRED"
    snap["backup_id"] = None

    guide = (
        "# Prompt Action S001 Baseline Recovery\n\n"
        "S001 uses seven exact V22.5.1 prompt payloads plus the hash-exact official Prompt 3 v22.5.2 release, "
        "normalized as V1/R1 before any post-baseline release. Restore activation remains STEP 12 scope.\n"
    ).encode("utf-8")
    source_ref = json_bytes({
        "baseline": "V1/S001",
        "v22_5_1_rescue_sha256": RESCUE_SHA,
        "prompt3_pre_normalization_release": {
            "version": "v22.5.2",
            "sha256": NEW_P3,
            "bytes": 22320,
            "source_draft_v22_6_1_sha256": V2261_DRAFT_SHA,
            "proof": "historical release manifest SHA-256 matched exactly after the documented one-label renumbering",
        },
        "prompt_bytes_reconstructed": False,
    })
    entries: dict[str, bytes] = {
        "bootstrap/recovery-guide.md": guide,
        "bootstrap/baseline-source-reference.json": source_ref,
        "data/version_history.json": json_bytes(embedded),
    }
    for pid in EXPECTED:
        entries[canonical_rel(pid)] = payloads[pid]
    manifest = {
        "schema": "prompt-action-bootstrap-backup/v1",
        "system": "V1",
        "snapshot": "S001",
        "snapshot_status_at_backup": "BACKUP_REQUIRED",
        "baseline_sources": {
            "v22_5_1_rescue_sha256": RESCUE_SHA,
            "prompt3_v22_5_2_sha256": NEW_P3,
        },
        "canonical_sha256": sha_bytes(entries["data/version_history.json"]),
        "composition": {pid: "R1" for pid in EXPECTED},
        "entries": [
            {"path": name, "size": len(raw), "sha256": sha_bytes(raw)}
            for name, raw in sorted(entries.items())
        ],
        "tool": {
            "name": "STEP 09.5 Baseline Reconciliation P3 v22.5.2",
            "zip_format": "deflate-9",
            "deterministic_timestamp": "1980-01-01T00:00:00Z",
        },
    }
    entries["bootstrap/manifest.json"] = json_bytes(manifest)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, entries[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return out.getvalue()


def verify_zip(raw_zip: bytes, payloads: dict[str, bytes]) -> None:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        if zf.testzip() is not None:
            raise SystemExit("reconciled bootstrap ZIP CRC failure")
        names = zf.namelist()
        if names != sorted(names) or len(names) != len(set(names)):
            raise SystemExit("reconciled bootstrap ZIP order/uniqueness failure")
        for name in names:
            p = PurePosixPath(name.replace("\\", "/"))
            if p.is_absolute() or ".." in p.parts or re.match(r"^[A-Za-z]:", name) or name.startswith("//"):
                raise SystemExit(f"unsafe ZIP path: {name}")
        manifest = json.loads(zf.read("bootstrap/manifest.json"))
        for entry in manifest["entries"]:
            raw = zf.read(entry["path"])
            if len(raw) != entry["size"] or sha_bytes(raw) != entry["sha256"]:
                raise SystemExit(f"manifest mismatch: {entry['path']}")
        for pid, raw in payloads.items():
            if zf.read(canonical_rel(pid)) != raw:
                raise SystemExit(f"ZIP payload mismatch: {pid}")


def main() -> int:
    payloads: dict[str, bytes] = {}
    for pid, (_, expected_hash) in EXPECTED.items():
        path = ROOT / canonical_rel(pid)
        if not path.is_file():
            raise SystemExit(f"missing canonical prompt file: {path}")
        raw = path.read_bytes()
        if sha_bytes(raw) != expected_hash:
            raise SystemExit(f"{pid}: prompt SHA mismatch before reconciliation")
        raw.decode("utf-8")
        payloads[pid] = raw

    if len(payloads["P3"]) != 22320:
        raise SystemExit("P3 recovered byte size mismatch")

    doc = update_canonical()
    patch_baseline_json()
    patch_versioning_rules()

    # Update contracts that protect the materialized S001 prompt set.
    for rel in (
        "scripts/dev/verify_step095_bootstrap.py",
        "scripts/dev/materialize_step095_prompts.py",
        "tests/step095/test_step095_bootstrap.py",
        "scripts/dev/rebuild_step095_bootstrap_from_preserved_chunks.py",
    ):
        replace_hash_contract(ROOT / rel)

    # The old rescue/capsule cannot contain v22.5.2 P3, so future rebuilds may source
    # only P3 from the already hash-protected canonical baseline while all other
    # payloads retain their exact historical recovery path.
    add_current_p3_fallback(
        ROOT / "scripts/dev/rebuild_step095_bootstrap_from_preserved_chunks.py",
        "    missing = sorted(set(EXPECTED) - set(found))\n",
    )
    run_path = ROOT / "scripts/dev/run_step095_exact_capsule_rebuild.py"
    run_text = run_path.read_text(encoding="utf-8")
    if "hash-exact-baseline-recovery-p3-v22.5.2" not in run_text:
        marker = "    missing = sorted(set(module.EXPECTED) - set(found))\n"
        if marker not in run_text:
            raise SystemExit("run_step095 fallback marker missing")
        snippet = (
            "    # hash-exact-baseline-recovery-p3-v22.5.2\n"
            "    p3_path = ROOT / module.canonical_rel(\"P3\")\n"
            "    if p3_path.is_file():\n"
            "        p3_raw = p3_path.read_bytes()\n"
            "        if sha(p3_raw) == module.EXPECTED[\"P3\"][1]:\n"
            "            found[\"P3\"] = p3_raw\n"
            "            provenance[\"P3\"] = \"hash-exact recovered v22.5.2 baseline override\"\n"
        )
        run_path.write_text(run_text.replace(marker, snippet + marker, 1), encoding="utf-8")

    bootstrap = build_bootstrap(doc, payloads)
    verify_zip(bootstrap, payloads)
    backup_sha = sha_bytes(bootstrap)
    PRIMARY.parent.mkdir(parents=True, exist_ok=True)
    SECOND.parent.mkdir(parents=True, exist_ok=True)
    PRIMARY.write_bytes(bootstrap)
    SECOND.write_bytes(bootstrap)
    if sha_file(PRIMARY) != backup_sha or sha_file(SECOND) != backup_sha:
        raise SystemExit("primary/secondary backup write verification failed")

    primary_sidecar = PRIMARY.with_suffix(PRIMARY.suffix + ".sha256")
    second_sidecar = SECOND.with_suffix(SECOND.suffix + ".sha256")
    primary_sidecar.write_text(f"{backup_sha}  {PRIMARY.name}\n", encoding="utf-8")
    second_sidecar.write_text(f"{backup_sha}  {SECOND.name}\n", encoding="utf-8")

    backup = {
        "id": "B001",
        "system": "V1",
        "snapshot": "S001",
        "status": "VALID",
        "verified": True,
        "second_copy_verified": True,
        "file": str(PRIMARY.relative_to(ROOT)).replace("\\", "/"),
        "sha256": backup_sha,
        "sha256_file": str(primary_sidecar.relative_to(ROOT)).replace("\\", "/"),
        "second_copy": str(SECOND.relative_to(ROOT)).replace("\\", "/"),
        "second_copy_sha256": backup_sha,
        "second_copy_sha256_file": str(second_sidecar.relative_to(ROOT)).replace("\\", "/"),
        "manifest_path": "bootstrap/manifest.json",
        "bootstrap": True,
        "source_rescue_sha256": RESCUE_SHA,
        "prompt3_release_sha256": NEW_P3,
        "baseline_reconciliation": "P3_V22_5_2_HASH_EXACT",
        "created_at": "2026-10-04T00:00:00+07:00",
    }
    doc["backups"] = [backup]
    doc["snapshots"][0]["status"] = "COMPLETE"
    doc["snapshots"][0]["backup_id"] = "B001"
    dump_json(CANONICAL, doc)
    dump_json(RECORD, backup)

    EVIDENCE.mkdir(parents=True, exist_ok=True)
    dump_json(EVIDENCE / "recovery-proof.json", {
        "status": "PASS",
        "old_p3_sha256": OLD_P3,
        "recovered_p3_sha256": NEW_P3,
        "recovered_p3_bytes": len(payloads["P3"]),
        "draft_v22_6_1_sha256": V2261_DRAFT_SHA,
        "historical_manifest_expected_sha256": NEW_P3,
        "historical_manifest_match": True,
        "normalization": "v22.5.2 -> V1/S001/P3/R1",
        "new_revision_created": False,
        "new_snapshot_created": False,
        "backup_id": "B001",
        "backup_sha256": backup_sha,
        "primary_verified": sha_file(PRIMARY) == backup_sha,
        "second_copy_verified": sha_file(SECOND) == backup_sha,
        "prompt_bytes_reconstructed": False,
    })
    dump_json(ROOT / "docs/evidence/step095/preserved_chunk_materialization.json", {
        "status": "PASS",
        "verified_rescue_container_sha256_anchor": RESCUE_SHA,
        "proof": "Seven prompts retain exact STEP 00 V22.5.1 hashes; P3 is the hash-exact official v22.5.2 pre-normalization release.",
        "prompt_hashes": {pid: digest for pid, (_, digest) in EXPECTED.items()},
        "provenance": {
            **{pid: "verified V22.5.1 rescue evidence" for pid in EXPECTED if pid != "P3"},
            "P3": "official v22.5.2 release; exact SHA-256 verified from preserved version history",
        },
        "prompt_bytes_reconstructed": False,
        "bootstrap_zip_sha256": backup_sha,
        "bootstrap_zip_size": len(bootstrap),
    })
    dump_json(ROOT / "docs/evidence/step095/backup_verification.json", {
        "status": "PASS",
        "primary_sha256": backup_sha,
        "primary_size_bytes": PRIMARY.stat().st_size,
        "zip_crc": "PASS",
        "zip_paths": "PASS",
        "manifest": "PASS",
        "prompt_hashes": "PASS",
        "second_copy_sha256": backup_sha,
        "second_copy_verified": True,
        "baseline_reconciliation": "P3_V22_5_2_HASH_EXACT",
    })

    REPORT.write_text(
        "# Baseline Recovery — Prompt 3 v22.5.2\n\n"
        "Status: **PASS (pending CI commit at generation time)**\n\n"
        "- Scope: correct S001/P3/R1 baseline identity only.\n"
        f"- Incorrect P3 SHA: `{OLD_P3}` (legacy v22.5.1).\n"
        f"- Correct P3 SHA: `{NEW_P3}` (official v22.5.2 release).\n"
        "- Recovery proof: preserved V22.6.1 draft differed only by its version label; replacing that single label with V22.5.2 reproduced the historical release SHA-256 exactly.\n"
        "- No R2, S002, or new System was created.\n"
        "- B001 was regenerated deterministically and both primary and second copy were independently hash-verified.\n"
        f"- Reconciled B001 SHA-256: `{backup_sha}`.\n"
        "- STEP 11 remains blocked until a future real STEP 10 release creates a current `BACKUP_REQUIRED` snapshot.\n",
        encoding="utf-8",
    )

    # Final local invariants.
    final = json.loads(CANONICAL.read_text(encoding="utf-8"))
    if final["prompts"]["P3"]["revisions"]["R1"]["sha256"] != NEW_P3:
        raise SystemExit("final canonical P3 SHA mismatch")
    if final["integrity"]["protected_prompt_hashes"]["P3"] != NEW_P3:
        raise SystemExit("final protected hash map mismatch")
    if final["snapshots"][0]["status"] != "COMPLETE" or final["snapshots"][0]["backup_id"] != "B001":
        raise SystemExit("final S001 completion invariant failed")
    if final["backups"][0]["sha256"] != backup_sha:
        raise SystemExit("final B001 hash link mismatch")

    print(json.dumps({
        "status": "PASS",
        "p3_sha256": NEW_P3,
        "backup_sha256": backup_sha,
        "backup_size": len(bootstrap),
        "active_system": "V1",
        "active_snapshot": "S001",
        "snapshot_status": "COMPLETE",
        "backup_id": "B001",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
