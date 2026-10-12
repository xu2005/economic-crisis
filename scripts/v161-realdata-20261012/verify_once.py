import importlib.util, tempfile, json
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('once', Path(__file__).with_name('download_once.py'))
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
with tempfile.TemporaryDirectory() as temp:
    m.ROOT=Path(temp); (m.ROOT/'logs').mkdir()
    with patch.object(m.urllib.request,'urlopen',side_effect=TimeoutError('fixture timeout')) as request:
        first=m.attempt('same-resource','https://example.invalid/data',m.ROOT/'raw/a.bin')
        second=m.attempt('same-resource','https://example.invalid/data',m.ROOT/'raw/a.bin')
        assert first['status']=='SKIPPED'
        assert second['status']=='ALREADY_ATTEMPTED_NO_RETRY'
        assert request.call_count==1
    ledger=next((m.ROOT/'attempts').glob('*.json'))
    saved=json.loads(ledger.read_text(encoding='utf-8')); saved['status']='RESERVED'
    ledger.write_text(json.dumps(saved),encoding='utf-8')
    with patch.object(m.urllib.request,'urlopen') as request:
        assert m.attempt('same-resource','https://example.invalid/data',m.ROOT/'raw/a.bin')['status']=='ALREADY_ATTEMPTED_NO_RETRY'
        request.assert_not_called()
print('PASS: failure is requested once; later runs and interrupted RESERVED never request again')
