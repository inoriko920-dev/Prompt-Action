from __future__ import annotations
import hashlib, json, re
from pathlib import Path, PurePosixPath
import zipfile
from prompt_action.data.repository import VersionRepository
ROOT=Path(__file__).resolve().parents[2]
EXPECTED={"P1A":"65fb561dfaf328b204bb86ef2a55789e835fa56cfab01d89f1c67a7b348a46c5","P1B":"7064081b9a264ba66da2c4eb297cc00f0f2d4133a97c84bed6f0171318d870cf","P1B1":"a750b81cc0aa3b0fef5d6daaaaddddbae2be4c522ea4813784952f09eed26cc6","P1B2":"12cc083ac1e107a2ffa4b10269b644df30f401ee3bd10a5fe42c9605c7b46576","P2":"d972981dde11a5f07a76d8c9357c9ce2ae84ac2a52a6e06545936ca45c27ef98","P3":"0aa955989b428700293a4d76793718bd33c78015f3b0021256a665dd386c3de1","P4":"a1bdb7c980de1aadd10e9492730892977e7a525d6dbbd5e8643ddec4da48b1c0","P5":"bf0c0ea1dca1414794ad54a6c9f9d2a0617766706e55d366c2df081944fb2786"}
def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 repo=VersionRepository(ROOT); st=repo.load(); report=repo.validate(st); d=st.document; errors=[]
 if not report.is_valid: errors += [f"{x.code}:{x.message}" for x in report.issues]
 if d.get('app_data_revision')!=2: errors.append('app_data_revision must be 2')
 if d.get('active_system')!='V1' or d.get('active_snapshot')!='S001': errors.append('identity must remain V1/S001')
 if [x.get('id') for x in d.get('systems',[])]!=['V1'] or [x.get('id') for x in d.get('snapshots',[])]!=['S001']: errors.append('unexpected System/Snapshot IDs')
 snap=next((x for x in d.get('snapshots',[]) if x.get('id')=='S001'),None)
 if not snap or snap.get('status')!='COMPLETE' or snap.get('backup_id')!='B001': errors.append('S001 completion link invalid')
 for pid,h in EXPECTED.items():
  p=d['prompts'][pid]; r=p['revisions']['R1']
  if set(p['revisions'])!={'R1'}: errors.append(f'{pid}: unexpected revision')
  rel=r.get('file'); target=ROOT/rel if isinstance(rel,str) else None
  if r.get('file_available') is not True or target is None or not target.is_file() or sha(target)!=h or r.get('sha256')!=h: errors.append(f'{pid}: materialization/hash invalid')
 if d.get('integrity',{}).get('prompt_bytes_reconstructed') is not False: errors.append('prompt bytes reconstruction flag invalid')
 bs=[x for x in d.get('backups',[]) if x.get('id')=='B001']
 if len(bs)!=1: errors.append('B001 count invalid')
 else:
  b=bs[0]; p=ROOT/str(b.get('file')); s=ROOT/str(b.get('second_copy'))
  if not p.is_file() or sha(p)!=b.get('sha256'): errors.append('primary backup invalid')
  if not s.is_file() or sha(s)!=b.get('sha256') or b.get('second_copy_verified') is not True: errors.append('second copy invalid')
  if p.exists() and s.exists() and p.resolve()==s.resolve(): errors.append('second copy aliases primary')
  if p.is_file():
   with zipfile.ZipFile(p) as z:
    names=z.namelist()
    if z.testzip() is not None: errors.append('zip CRC failure')
    if names!=sorted(names) or len(names)!=len(set(names)): errors.append('zip order/uniqueness invalid')
    for name in names:
     q=PurePosixPath(name.replace('\\','/'))
     if q.is_absolute() or '..' in q.parts or re.match(r'^[A-Za-z]:',name) or name.startswith('//'): errors.append(f'unsafe zip entry:{name}')
    m=json.loads(z.read('bootstrap/manifest.json'))
    for e in m.get('entries',[]):
     if hashlib.sha256(z.read(e['path'])).hexdigest()!=e['sha256']: errors.append(f"manifest mismatch:{e['path']}")
 out={'gate':'STEP_09_5','status':'PASS' if not errors else 'FAIL','app_data_revision':d.get('app_data_revision'),'active_system':d.get('active_system'),'active_snapshot':d.get('active_snapshot'),'snapshot_status':snap.get('status') if snap else None,'backup_id':snap.get('backup_id') if snap else None,'prompt_count':len(EXPECTED),'issues':errors}
 print(json.dumps(out,indent=2)); return 0 if not errors else 1
if __name__=='__main__': raise SystemExit(main())
