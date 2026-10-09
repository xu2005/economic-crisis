"""Package reports, raw evidence and exact scripts; preserve all preceding archives."""
from pathlib import Path
import json,hashlib,zipfile,shutil
R=Path(__file__).resolve().parents[1];O=R/'reports/crisis-v32-cny';P=R/'public/crisis-v32-cny'
def main():
 test=json.loads((O/'test-report.json').read_text());assert test['fail']==0 and test['pass']>=157
 files=[p for p in O.rglob('*') if p.is_file() and p.name not in ['full-review.zip','manifest.json']]
 files+=list((R/'data/v32-cny').rglob('*'))
 files+=[R/'scripts'/x for x in ['cny_implementability.py','cny_tax_model.py','cny_account.py','cny_metadata.py','register_cny_study.py','test_cny_implementability.py','cny_product_evidence.py','build_cny_evidence.py','capture_cny_evidence.py','test_cny_evidence_round2.py','run_cny_checks.py','reassemble_cny_review.py','reproduce_cny.py','write_cny_reports.py','finish_cny_study.py']]
 files+=[R/'reports/crisis-v3/input'/x for x in ['cross-asset-aligned.csv','cross-asset-alignment-audit.csv']]
 files+=[R/'reports/crisis-v31/results.json',R/'reports/crisis-v31/freeze.json']
 # Preserve the published values used by the offline webpage-consistency test.
 files+=[P/'results.json',P/'product-disclosed-periods.csv']
 for folder in ['src','server','db','drizzle']:
  files += [p for p in (R/folder).rglob('*') if p.is_file()]
 files += [R/x for x in ['package.json','package-lock.json','requirements-cny.txt','vite.config.ts','tsconfig.json','tsconfig.app.json','tsconfig.node.json','README.md','index.html','.openai/hosting.json'] if (R/x).exists()]
 files=sorted({p for p in files if p.is_file()});m={'study':'V3.2 CNY after-tax','scope':'new study scripts/data/outputs plus archived 37-event evidence; prior 135MB research project stays in site source repository; entire original backtests available via old version pages','files':{str(p.relative_to(R)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in files}}
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 with zipfile.ZipFile(O/'full-review.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in files+[O/'manifest.json']:z.write(p,str(p.relative_to(R)))
 P.mkdir(parents=True,exist_ok=True)
 for p in O.rglob('*'):
  if p.is_file():
   if p.name=='full-review.zip' and p.stat().st_size>25*1024*1024:continue
   t=P/p.relative_to(O);t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,t)
 archive=O/'full-review.zip';meta={'filename':'full-review.zip','sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'parts':[]}
 for old in P.glob('full-review.zip.*'):old.unlink()
 if archive.stat().st_size>25*1024*1024:
  (P/'full-review.zip').unlink(missing_ok=True)
  combined=hashlib.sha256()
  with archive.open('rb') as f:
   i=1
   while chunk:=f.read(20*1024*1024):
    name=f'full-review.zip.{i:03d}';(P/name).write_bytes(chunk);combined.update(chunk);meta['parts'].append({'name':name,'bytes':len(chunk),'sha256':hashlib.sha256(chunk).hexdigest()});i+=1
  if combined.hexdigest()!=meta['sha256']:raise ValueError('split archive hash mismatch')
 else:meta['parts']=[{'name':'full-review.zip','bytes':meta['bytes'],'sha256':meta['sha256']}]
 (P/'review-archive.json').write_text(json.dumps(meta,indent=2)+'\n')
 shutil.copy2(R/'scripts/reassemble_cny_review.py',P/'reassemble_cny_review.py')
 print(json.dumps({'review_zip_bytes':(O/'full-review.zip').stat().st_size,'files':len(files)}))
if __name__=='__main__':main()
