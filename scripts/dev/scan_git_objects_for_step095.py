from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGETS = {
    "P1A": (5401, "65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5"),
    "P1B": (43390, "7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf"),
    "P1B1": (25510, "a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6"),
    "P1B2": (19437, "12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576"),
    "P2": (15810, "d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98"),
    "P3": (23652, "de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8"),
    "P4": (6514, "a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0"),
    "P5": (6107, "bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"),
    "LEGACY_RESCUE_ZIP": (69158, "f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2"),
}


def run(*args: str, input_bytes: bytes | None = None) -> bytes:
    return subprocess.check_output(args, cwd=ROOT, input=input_bytes)


def main() -> int:
    objects = run("git", "rev-list", "--objects", "--all").decode("utf-8", errors="replace").splitlines()
    oid_paths: dict[str, set[str]] = {}
    for line in objects:
        if not line.strip():
            continue
        oid, *rest = line.split(" ", 1)
        oid_paths.setdefault(oid, set())
        if rest:
            oid_paths[oid].add(rest[0])

    oids = list(oid_paths)
    batch_input = ("\n".join(oids) + "\n").encode()
    meta = run("git", "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", input_bytes=batch_input).decode().splitlines()
    size_to_targets: dict[int, list[tuple[str, str]]] = {}
    for name, (size, digest) in TARGETS.items():
        size_to_targets.setdefault(size, []).append((name, digest))

    candidates = []
    matches: dict[str, list[dict]] = {name: [] for name in TARGETS}
    for line in meta:
        parts = line.split()
        if len(parts) != 3:
            continue
        oid, kind, size_text = parts
        if kind != "blob":
            continue
        size = int(size_text)
        if size not in size_to_targets:
            continue
        raw = run("git", "cat-file", "blob", oid)
        digest = hashlib.sha256(raw).hexdigest()
        item = {"oid": oid, "size": size, "sha256": digest, "paths": sorted(oid_paths.get(oid, set()))}
        candidates.append(item)
        for target_name, target_sha in size_to_targets[size]:
            if digest == target_sha:
                matches[target_name].append(item)

    report = {
        "reachable_object_count": len(oids),
        "size_filtered_blob_candidates": len(candidates),
        "matches": matches,
        "missing": [name for name, values in matches.items() if not values],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if matches["P1B2"]:
        print("P1B2_EXACT_GIT_BLOB_FOUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
