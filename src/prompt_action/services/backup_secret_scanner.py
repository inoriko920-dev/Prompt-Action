from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

from prompt_action.domain.errors import BackupWorkflowError


@dataclass(frozen=True, slots=True)
class SecretFinding:
    rule: str
    path: str
    line: int | None = None


_FILENAME_RULES = {
    ".env",
    ".env.local",
    "credentials.json",
    "client_secret.json",
    "secrets.json",
    "id_rsa",
    "id_ed25519",
}

_TEXT_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_token", re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("google_api_key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "credential_assignment",
        re.compile(
            r"(?im)^\s*(?:password|passwd|api[_-]?key|access[_-]?token|secret)\s*[:=]\s*[\"']?(?!<|example|dummy|placeholder|none|null)[A-Za-z0-9_./+@:-]{12,}"
        ),
    ),
)


def scan_bytes(payload: bytes, *, logical_path: str) -> list[SecretFinding]:
    name = Path(logical_path).name.lower()
    if name in _FILENAME_RULES:
        return [SecretFinding("secret_filename", logical_path, None)]
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        # Backup inputs in STEP 11 are expected to be known canonical/data files.
        # Opaque binary inputs are not scanned as text here; ZIP planning controls
        # exactly which binary files may enter the archive.
        return []
    findings: list[SecretFinding] = []
    for rule, pattern in _TEXT_RULES:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.append(SecretFinding(rule, logical_path, line))
    return findings


def scan_sources(items: Iterable[tuple[str, bytes]]) -> None:
    findings: list[SecretFinding] = []
    for logical_path, payload in items:
        findings.extend(scan_bytes(payload, logical_path=logical_path))
    if findings:
        compact = ", ".join(
            f"{item.path}:{item.line or '-'}[{item.rule}]" for item in findings[:8]
        )
        raise BackupWorkflowError("SECRET_DETECTED", f"Backup blocked by secret scanner: {compact}")
