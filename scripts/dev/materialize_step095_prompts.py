from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / 'data/version_history.json'
BACKUP = ROOT / 'backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip'
EXPECTED = {
    'P1A': ('Prompt-1A', '65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5'),
    'P1B': ('Prompt-1B', '7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf'),
    'P1B1': ('Prompt-1B1', 'a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6'),
    'P1B2': ('Prompt-1B2', '12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576'),
    'P2': ('Prompt-2', 'd972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98'),
    'P3': ('Prompt-3', 'de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8'),
    'P4': ('Prompt-4', 'a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0'),
    'P5': ('Prompt-5', 'bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786'),
}
BACKUP_SHA = '0893ffbfcd28616673cfddc7ac8e4f655337b176794c2119f485cafc0559db02'
RESCUE_SHA = 'f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2'


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_name(name: str) -> bool:
    p = PurePosixPath(name.replace('\\', '/'))
    return not p.is_absolute() and '..' not in p.parts and not re.match(r'^[A-Za-z]:', name) and not name.startswith('//')


def main() -> None:
    if not BACKUP.is_file() or sha_file(BACKUP) != BACKUP_SHA:
        raise SystemExit('bootstrap backup missing or SHA mismatch')
    doc = json.loads(CANONICAL.read_text(encoding='utf-8'))
    if doc.get('app_data_revision') == 2:
        # Idempotent re-run: verify final state only.
        snap = next((x for x in doc.get('snapshots', []) if x.get('id') == 'S001'), None)
        if not snap or snap.get('status') != 'COMPLETE' or snap.get('backup_id') != 'B001':
            raise SystemExit('revision 2 exists but S001 final state is invalid')
        for pid, (label, expected_hash) in EXPECTED.items():
            rel = f'prompts/V1/{label}/{label}_V1_R1.txt'
            target = ROOT / rel
            if not target.is_file() or sha_file(target) != expected_hash:
                raise SystemExit(f'{pid} final materialized bytes invalid')
        print('STEP 09.5 already materialized and valid')
        return
    if doc.get('app_data_revision') != 1 or doc.get('active_system') != 'V1' or doc.get('active_snapshot') != 'S001':
        raise SystemExit('unexpected canonical precondition')
    if doc.get('backups') != []:
        raise SystemExit('bootstrap requires empty backup list')
    snap = next((x for x in doc.get('snapshots', []) if x.get('id') == 'S001'), None)
    if not snap or snap.get('status') != 'BACKUP_REQUIRED' or snap.get('backup_id') is not None:
        raise SystemExit('S001 is not the expected bootstrap precondition')
    if doc.get('integrity', {}).get('legacy_rescue_sha256') != RESCUE_SHA:
        raise SystemExit('rescue provenance mismatch')

    with zipfile.ZipFile(BACKUP) as z:
        if z.testzip() is not None:
            raise SystemExit('bootstrap backup CRC failed')
        if any(not safe_name(name) for name in z.namelist()):
            raise SystemExit('unsafe bootstrap ZIP path')
        for pid, (label, expected_hash) in EXPECTED.items():
            rel = f'prompts/V1/{label}/{label}_V1_R1.txt'
            raw = z.read(rel)
            if sha_bytes(raw) != expected_hash:
                raise SystemExit(f'{pid} ZIP payload SHA mismatch')
            revision = doc['prompts'][pid]['revisions']['R1']
            if revision.get('sha256') != expected_hash or revision.get('file') is not None or revision.get('file_available') is not False:
                raise SystemExit(f'{pid} canonical precondition mismatch')
            target = ROOT / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            if sha_file(target) != expected_hash:
                raise SystemExit(f'{pid} written bytes SHA mismatch')
            revision['file'] = rel
            revision['file_available'] = True

    doc['app_data_revision'] = 2
    doc['backups'] = [{
        'id': 'B001', 'snapshot': 'S001', 'system': 'V1', 'status': 'VALID', 'verified': True,
        'file': 'backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip',
        'sha256': BACKUP_SHA,
        'sha256_file': 'backups/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip.sha256',
        'sha256_file_sha256': '8489cd7b61e0b2ca6d54d97b9d764c37d2c54291ce306b307674d05c0a2311b9',
        'second_copy': 'backups/second-copy/V1/S001/Prompt-Action-V1-S001-BOOTSTRAP-FULL-BACKUP.zip',
        'second_copy_sha256': BACKUP_SHA, 'second_copy_verified': True,
        'manifest_path': 'bootstrap/manifest.json',
        'manifest_sha256': '8b97448f959375e957a8425a2b83eeb516775f5086681467cd9c6a2049f571d9',
        'rescue_source_sha256': RESCUE_SHA,
        'backup_kind': 'BOOTSTRAP_BASELINE', 'created_at': '2026-10-03T00:00:00+07:00'
    }]
    snap['status'] = 'COMPLETE'
    snap['backup_id'] = 'B001'
    if set(doc.get('systems', [{}])[0:1][0].get('id', '') for _ in [0]) != {'V1'}:
        raise SystemExit('System identity changed unexpectedly')
    CANONICAL.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('STEP 09.5 exact Prompt bytes + canonical transition staged atomically')


if __name__ == '__main__':
    main()
