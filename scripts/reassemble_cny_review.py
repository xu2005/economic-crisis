"""Place this script, review-archive.json and all parts in one folder; run Python."""
from pathlib import Path
import hashlib,json,os
root=Path(__file__).resolve().parent;meta=json.loads((root/'review-archive.json').read_text())
if len(meta['parts'])==1:raise SystemExit('Single ZIP needs no reassembly.')
output=root/meta['filename'];temp=root/(meta['filename']+'.assembling');combined=hashlib.sha256()
try:
 with temp.open('wb') as f:
  for part in meta['parts']:
   path=root/part['name'];data=path.read_bytes()
   if len(data)!=part['bytes'] or hashlib.sha256(data).hexdigest()!=part['sha256']:raise ValueError('Missing or modified part: '+part['name'])
   f.write(data);combined.update(data)
 if temp.stat().st_size!=meta['bytes'] or combined.hexdigest()!=meta['sha256']:raise ValueError('Combined archive hash mismatch')
 os.replace(temp,output);print('Verified complete ZIP: '+str(output))
finally:temp.unlink(missing_ok=True)
