from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import zlib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PRIMARY = ROOT / "backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
SECOND = ROOT / "backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip"
EVIDENCE = ROOT / "docs/evidence/step095/archive_repair.json"
EXPECTED = {
    "P1A": ("Prompt-1A", "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"),
    "P1B": ("Prompt-1B", "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf"),
    "P1B1": ("Prompt-1B1", "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6"),
    "P1B2": ("Prompt-1B2", "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576"),
    "P2": ("Prompt-2", "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98"),
    "P3": ("Prompt-3", "de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8"),
    "P4": ("Prompt-4", "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0"),
    "P5": ("Prompt-5", "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"),
}
LOCAL_HEADER = 0x04034B50


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def safe_name(name: str) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and not re.match(r"^[A-Za-z]:", name) and not name.startswith("//")


def expected_rel(prompt_id: str) -> str:
    label = EXPECTED[prompt_id][0]
    return f"prompts/V1/{label}/{label}_V1_R1.txt"


def normal_zip_payloads(path: Path) -> dict[str, bytes] | None:
    try:
        with zipfile.ZipFile(path) as zf:
            if zf.testzip() is not None:
                return None
            names = zf.namelist()
            if names != sorted(names) or len(names) != len(set(names)):
                return None
            return {name: zf.read(name) for name in names}
    except zipfile.BadZipFile:
        return None


def recover_local_payloads(path: Path) -> dict[str, bytes]:
    raw = path.read_bytes()
    payloads: dict[str, bytes] = {}
    pos = 0
    while pos + 30 <= len(raw):
        signature = struct.unpack_from("<I", raw, pos)[0]
        if signature != LOCAL_HEADER:
            break
        (
            _signature,
            _version,
            flags,
            method,
            _mtime,
            _mdate,
            crc32_expected,
            compressed_size,
            uncompressed_size,
            name_len,
            extra_len,
        ) = struct.unpack_from("<IHHHHHIIIHH", raw, pos)
        if flags & 0x08:
            raise SystemExit("cannot safely recover ZIP entries that use data descriptors")
        name_start = pos + 30
        name_end = name_start + name_len
        data_start = name_end + extra_len
        data_end = data_start + compressed_size
        if data_end > len(raw):
            raise SystemExit("truncated local ZIP entry")
        name = raw[name_start:name_end].decode("utf-8")
        if not safe_name(name) or name in payloads:
            raise SystemExit(f"unsafe or duplicate recovered ZIP path: {name}")
        compressed = raw[data_start:data_end]
        if method == zipfile.ZIP_STORED:
            payload = compressed
        elif method == zipfile.ZIP_DEFLATED:
            payload = zlib.decompress(compressed, -15)
        else:
            raise SystemExit(f"unsupported ZIP compression method {method} for {name}")
        if len(payload) != uncompressed_size:
            raise SystemExit(f"recovered size mismatch: {name}")
        if (zlib.crc32(payload) & 0xFFFFFFFF) != crc32_expected:
            raise SystemExit(f"recovered CRC mismatch: {name}")
        payloads[name] = payload
        pos = data_end
    if not payloads:
        raise SystemExit("no recoverable local ZIP entries found")
    return payloads


def verify_semantics(payloads: dict[str, bytes]) -> None:
    names = sorted(payloads)
    if any(not safe_name(name) for name in names):
        raise SystemExit("recovered ZIP contains unsafe path")
    if "bootstrap/manifest.json" not in payloads:
        raise SystemExit("bootstrap manifest missing after recovery")
    manifest = json.loads(payloads["bootstrap/manifest.json"].decode("utf-8"))
    if manifest.get("system") != "V1" or manifest.get("snapshot") != "S001":
        raise SystemExit("bootstrap manifest identity mismatch after recovery")
    if manifest.get("composition") != {pid: "R1" for pid in EXPECTED}:
        raise SystemExit("bootstrap manifest composition mismatch after recovery")
    entries = manifest.get("entries", [])
    if not isinstance(entries, list) or not entries:
        raise SystemExit("bootstrap manifest entries missing after recovery")
    for entry in entries:
        name = entry.get("path")
        if not isinstance(name, str) or name not in payloads:
            raise SystemExit(f"manifest entry missing after recovery: {name}")
        payload = payloads[name]
        if len(payload) != entry.get("size") or sha_bytes(payload) != entry.get("sha256"):
            raise SystemExit(f"manifest hash mismatch after recovery: {name}")
    for pid, (_, expected_hash) in EXPECTED.items():
        rel = expected_rel(pid)
        payload = payloads.get(rel)
        if payload is None or sha_bytes(payload) != expected_hash:
            raise SystemExit(f"{pid}: protected Prompt hash mismatch during recovery")
        payload.decode("utf-8")


def write_deterministic_zip(path: Path, payloads: dict[str, bytes]) -> None:
    temp = path.with_suffix(path.suffix + ".repair.tmp")
    if temp.exists():
        temp.unlink()
    with zipfile.ZipFile(temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name in sorted(payloads):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            zf.writestr(info, payloads[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(temp) as zf:
        if zf.testzip() is not None or zf.namelist() != sorted(payloads):
            temp.unlink(missing_ok=True)
            raise SystemExit("rebuilt bootstrap ZIP did not verify")
    temp.replace(path)


def main() -> int:
    if not PRIMARY.is_file():
        raise SystemExit(f"bootstrap backup missing: {PRIMARY}")
    original_sha = sha_file(PRIMARY)
    payloads = normal_zip_payloads(PRIMARY)
    repaired_primary = False
    if payloads is None:
        payloads = recover_local_payloads(PRIMARY)
        verify_semantics(payloads)
        write_deterministic_zip(PRIMARY, payloads)
        repaired_primary = True
    else:
        verify_semantics(payloads)

    primary_sha = sha_file(PRIMARY)
    second_was_identical = SECOND.is_file() and sha_file(SECOND) == primary_sha
    if not second_was_identical:
        SECOND.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(PRIMARY, SECOND)
    second_sha = sha_file(SECOND)
    if second_sha != primary_sha:
        raise SystemExit("second-copy repair failed")

    final_payloads = normal_zip_payloads(PRIMARY)
    if final_payloads is None:
        raise SystemExit("primary ZIP is still invalid after guarded repair")
    verify_semantics(final_payloads)

    evidence = {
        "status": "PASS",
        "primary_repaired": repaired_primary,
        "second_copy_replaced": not second_was_identical,
        "original_primary_sha256": original_sha,
        "final_primary_sha256": primary_sha,
        "final_second_copy_sha256": second_sha,
        "entry_count": len(final_payloads),
        "prompt_hashes_preserved": True,
        "payload_reconstruction": False,
        "repair_scope": "ZIP container metadata/central-directory only",
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
