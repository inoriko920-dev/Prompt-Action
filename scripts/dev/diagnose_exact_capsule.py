from __future__ import annotations

import base64
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPSULE = ROOT / "docs/evidence/step095/exact_prompt_capsule"


def split_padded_streams(text: str) -> list[str]:
    compact = "".join(text.split())
    out: list[str] = []
    start = 0
    i = 0
    while i < len(compact):
        if compact[i] == "=":
            j = i
            while j + 1 < len(compact) and compact[j + 1] == "=":
                j += 1
            seg = compact[start:j + 1]
            if seg:
                out.append(seg)
            start = j + 1
            i = j + 1
        else:
            i += 1
    if start < len(compact):
        out.append(compact[start:])
    return [s for s in out if s]


def decode_segment(seg: str) -> bytes | None:
    padded = seg + ("=" * ((-len(seg)) % 4))
    try:
        return base64.b64decode(padded, validate=True)
    except Exception:
        return None


def main() -> int:
    report: dict[str, object] = {"parts": []}
    concatenated_raw = bytearray()
    for path in sorted(CAPSULE.glob("part*.b64")):
        text = path.read_text(encoding="ascii")
        compact = "".join(text.split())
        segs = split_padded_streams(text)
        seg_report = []
        for idx, seg in enumerate(segs, 1):
            raw = decode_segment(seg)
            seg_report.append({
                "index": idx,
                "chars": len(seg),
                "mod4": len(seg) % 4,
                "ends_padding": seg.endswith("="),
                "decoded_bytes": len(raw) if raw is not None else None,
                "decoded_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
                "starts_pk": bool(raw and raw.startswith(b"PK")),
            })
            if raw is not None:
                concatenated_raw.extend(raw)
        report["parts"].append({
            "name": path.name,
            "chars": len(compact),
            "padding_chars": compact.count("="),
            "segments": seg_report,
        })
    raw = bytes(concatenated_raw)
    report["decoded_segments_concat"] = {
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "starts_pk": raw.startswith(b"PK"),
        "local_headers": len(re.findall(re.escape(b"PK\x03\x04"), raw)),
        "eocd_headers": len(re.findall(re.escape(b"PK\x05\x06"), raw)),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
