from __future__ import annotations
import hashlib, json, re
from pathlib import Path, PurePosixPath
import zipfile
from prompt_action.data.repository import VersionRepository
from prompt_action.presentation.backup_query_service import BackupRecoveryQueryService
from prompt_action.services.step09.download import DownloadService
ROOT=Path(__file__).resolve().parents[2]; D=json.loads((ROOT/'data/version_history.json').read_text(encoding='utf-8')); E=ROOT/'docs/evidence/step095'
EXPECTED={"P1A":"65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5","P1B":"7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf","P1B1":"a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6","P1B2":"12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576","P2":"d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98","P3":"de7268db093be34156ccbdff04ada92956bc7469d75f222ec7bf3e5f19d77fc8","P4":"a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0","P5":"bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"}; RESCUE='f7ac13dd184df23a72a96854c458ba8cac6fe1c42e2dd7edd0121794a7ccfdb2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rev(pid): return D['prompts'][pid]['revisions']['R1']
def backup(): return next(x for x in D['backups'] if x['id']=='B001')
def zopen(): return zipfile.ZipFile(ROOT/backup()['file'])
def test_t01_prior_steps_pass():
 paths=[ROOT/'STEP_00_BASELINE_REPORT.md']+[ROOT/f'docs/implementation/STEP_{n:02d}_SOL_EXECUTION_REPORT.md' for n in range(1,10)]
 assert all(p.is_file() and 'PASS' in p.read_text(encoding='utf-8',errors='ignore') for p in paths)
def test_t02_identity_unchanged(): assert D['active_system']=='V1' and D['active_snapshot']=='S001'
def test_t03_single_data_revision_increment(): assert D['app_data_revision']==2
def test_t04_rescue_sha_evidence(): assert json.loads((E/'rescue_verification.json').read_text())['rescue_sha256']==RESCUE
def test_t05_rescue_was_verified_pre_materialization(): assert json.loads((E/'rescue_verification.json').read_text())['verified_before_materialization'] is True
def test_t06_rescue_mapping_is_exact_eight(): assert set(json.loads((E/'rescue_verification.json').read_text())['mapping'])==set(EXPECTED)
def test_t07_p1a_exact(): assert sha(ROOT/rev('P1A')['file'])==EXPECTED['P1A']==rev('P1A')['sha256']
def test_t08_p1b_exact(): assert sha(ROOT/rev('P1B')['file'])==EXPECTED['P1B']==rev('P1B')['sha256']
def test_t09_p1b1_exact(): assert sha(ROOT/rev('P1B1')['file'])==EXPECTED['P1B1']==rev('P1B1')['sha256']
def test_t10_p1b2_exact(): assert sha(ROOT/rev('P1B2')['file'])==EXPECTED['P1B2']==rev('P1B2')['sha256']
def test_t11_p2_exact(): assert sha(ROOT/rev('P2')['file'])==EXPECTED['P2']==rev('P2')['sha256']
def test_t12_p3_exact(): assert sha(ROOT/rev('P3')['file'])==EXPECTED['P3']==rev('P3')['sha256']
def test_t13_p4_exact(): assert sha(ROOT/rev('P4')['file'])==EXPECTED['P4']==rev('P4')['sha256']
def test_t14_p5_exact(): assert sha(ROOT/rev('P5')['file'])==EXPECTED['P5']==rev('P5')['sha256']
def test_t15_all_materialized(): assert all(rev(p)['file_available'] is True for p in EXPECTED)
def test_t16_canonical_names(): assert all(rev(p)['file']==f"prompts/V1/{D['prompts'][p]['display_name'].replace(' ','-')}/{D['prompts'][p]['display_name'].replace(' ','-')}_V1_R1.txt" for p in EXPECTED)
def test_t17_no_new_revision_ids(): assert all(set(D['prompts'][p]['revisions'])=={'R1'} for p in EXPECTED)
def test_t18_no_new_system_snapshot_ids(): assert [x['id'] for x in D['systems']]==['V1'] and [x['id'] for x in D['snapshots']]==['S001']
def test_t19_protected_hash_map_unchanged(): assert D['integrity']['protected_prompt_hashes']==EXPECTED
def test_t20_canonical_validator_passes():
 r=VersionRepository(ROOT); assert r.validate(r.load()).is_valid
def test_t21_b001_only_backup(): assert [x['id'] for x in D['backups']]==['B001']
def test_t22_primary_backup_hash(): assert sha(ROOT/backup()['file'])==backup()['sha256']
def test_t23_sidecar_matches(): assert (ROOT/backup()['sha256_file']).read_text().split()[0]==backup()['sha256']
def test_t24_second_copy_distinct(): assert (ROOT/backup()['file']).resolve()!=(ROOT/backup()['second_copy']).resolve()
def test_t25_second_copy_hash(): assert sha(ROOT/backup()['second_copy'])==backup()['sha256'] and backup()['second_copy_verified'] is True
def test_t26_zip_reopens_crc_clean():
 with zopen() as z: assert z.testzip() is None
def test_t27_zip_sorted():
 with zopen() as z: assert z.namelist()==sorted(z.namelist())
def test_t28_zip_unique_entries():
 with zopen() as z: assert len(z.namelist())==len(set(z.namelist()))
def test_t29_zip_paths_safe():
 with zopen() as z:
  for name in z.namelist():
   p=PurePosixPath(name.replace('\\','/')); assert not p.is_absolute() and '..' not in p.parts and not re.match(r'^[A-Za-z]:',name) and not name.startswith('//')
def test_t30_manifest_identity():
 with zopen() as z:
  m=json.loads(z.read('bootstrap/manifest.json')); assert m['system']=='V1' and m['snapshot']=='S001'
def test_t31_manifest_composition():
 with zopen() as z: assert json.loads(z.read('bootstrap/manifest.json'))['composition']=={p:'R1' for p in EXPECTED}
def test_t32_manifest_entry_hashes():
 with zopen() as z:
  m=json.loads(z.read('bootstrap/manifest.json')); assert all(hashlib.sha256(z.read(e['path'])).hexdigest()==e['sha256'] for e in m['entries'])
def test_t33_embedded_canonical_is_precompletion_rev2():
 with zopen() as z:
  c=json.loads(z.read('data/version_history.json')); assert c['app_data_revision']==2 and c['snapshots'][0]['status']=='BACKUP_REQUIRED' and c['backups']==[]
def test_t34_backup_has_recovery_guide():
 with zopen() as z: assert 'bootstrap/recovery-guide.md' in z.namelist()
def test_t35_final_s001_complete():
 s=D['snapshots'][0]; assert s['status']=='COMPLETE' and s['backup_id']=='B001'
def test_t36_backup_record_valid_flags(): assert backup()['status']=='VALID' and backup()['verified'] is True and backup()['second_copy_verified'] is True
def test_t37_no_prompt_reconstruction_flag(): assert D['integrity']['prompt_bytes_reconstructed'] is False
def test_t38_allowed_diff_evidence_declares_no_new_ids(): assert 'new Revision R' in json.loads((E/'allowed_canonical_diff.json').read_text())['forbidden_changes_verified_absent']
def test_t39_backup_ui_safe():
 s=BackupRecoveryQueryService(ROOT).read(); assert s['snapshot_status']=='COMPLETE' and s['recovery_health']=='SAFE' and s['recovery_label']=='AMAN'
def test_t40_step09_download_exact_p3():
 p=DownloadService(ROOT).prepare({'type':'active_prompt','prompt_id':'P3'}); assert p.sha256==EXPECTED['P3'] and sha(p.source_path)==EXPECTED['P3']
